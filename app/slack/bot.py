"""Slack Bolt app + event handlers (spec §6).

The Bolt app is only constructed when Slack credentials are present; otherwise
the web UI and seed script can run standalone. The ticket-creation core is
factored into `create_ticket_from_event` so it can be unit-tested with a fake
Slack client and no live Events API.
"""
import logging

from app.models import STATUS_TODO, Ticket, db
from app.slack.formatting import creation_reply, status_label

log = logging.getLogger(__name__)

TITLE_MAX = 80


# --- Web client ------------------------------------------------------------
def get_web_client(config):
    """Return a slack_sdk WebClient, or None when Slack isn't configured."""
    if not config.SLACK_BOT_TOKEN:
        return None
    from slack_sdk import WebClient

    return WebClient(token=config.SLACK_BOT_TOKEN)


# --- Event filtering -------------------------------------------------------
def should_ignore_message(event, channel_id):
    """Decide whether a `message` event should be ignored (spec §6.2 step 2).

    Ignores: other channels, messages from bots (incl. ourselves), and any
    subtype'd message (edits -> message_changed, deletes -> message_deleted,
    channel joins, bot_message, etc.). Genuine new user messages -- root or
    plain thread reply -- have no subtype.
    """
    if channel_id and event.get("channel") != channel_id:
        return True
    if event.get("bot_id"):
        return True
    if event.get("subtype"):
        return True
    return False


def _resolve_root(event, client, channel_id):
    """Resolve the thread-root ts and the text to use as the ticket content.

    Returns (root_ts, text). For a plain root message this is just the event
    itself. For a reply to a non-ticket message (§6.5) we treat the thread
    root as the ticket content; if the root can't be fetched we fall back to
    the reply itself and log a warning -- never crash.
    """
    event_ts = event["ts"]
    thread_ts = event.get("thread_ts")

    if not thread_ts or thread_ts == event_ts:
        # Root message -- it is the ticket.
        return event_ts, event.get("text", "")

    # Reply to something that isn't (yet) a tracked ticket. Use the root.
    if client is not None:
        try:
            resp = client.conversations_replies(
                channel=channel_id, ts=thread_ts, limit=1, inclusive=True
            )
            messages = resp.get("messages") or []
            if messages:
                return thread_ts, messages[0].get("text", "")
        except Exception as exc:  # pragma: no cover - network/permission edge
            log.warning(
                "Could not resolve thread root %s in %s (%s); "
                "falling back to the reply itself.",
                thread_ts,
                channel_id,
                exc,
            )
    else:
        log.warning(
            "No Slack client to resolve thread root %s; using the reply.",
            thread_ts,
        )
    # Fallback: ticket is anchored to the reply (§6.5).
    return event_ts, event.get("text", "")


def _make_title(text):
    text = (text or "").strip()
    if not text:
        return "(no text)"
    first_line = text.splitlines()[0].strip() or text.strip()
    if len(first_line) <= TITLE_MAX:
        return first_line
    return first_line[:TITLE_MAX].rstrip() + "…"


def create_ticket_from_event(event, client, config):
    """Create a ticket from a (pre-filtered) channel message event.

    Returns the created Ticket, or None if the message maps to an existing
    ticket thread (a comment/duplicate, §6.4) and should be skipped.
    """
    channel_id = event.get("channel") or config.SLACK_TICKET_CHANNEL_ID
    root_ts, text = _resolve_root(event, client, channel_id)

    # Dedupe: a thread can only map to one ticket. This also covers replies
    # within an already-tracked ticket thread (§6.4) -- they share the root ts.
    existing = Ticket.query.filter_by(slack_message_ts=root_ts).first()
    if existing is not None:
        log.debug("Message maps to existing ticket #%s; skipping.", existing.id)
        return None

    ticket = Ticket(
        title=_make_title(text),
        description=(text or "").strip(),
        status=STATUS_TODO,
        assignee=None,
        slack_channel_id=channel_id,
        slack_message_ts=root_ts,
    )
    db.session.add(ticket)
    db.session.commit()  # assigns ticket.id, needed for the reply link

    # Best-effort permalink (§6.2 step 4).
    if client is not None:
        try:
            perma = client.chat_getPermalink(
                channel=channel_id, message_ts=root_ts
            )
            ticket.slack_permalink = perma.get("permalink")
        except Exception as exc:  # pragma: no cover - network edge
            log.warning("chat.getPermalink failed for #%s: %s", ticket.id, exc)

    # Threaded creation reply, stored for later chat.update (§6.2 step 5/6).
    if client is not None:
        try:
            resp = client.chat_postMessage(
                channel=channel_id,
                thread_ts=root_ts,
                text=creation_reply(ticket, config.BASE_URL),
                unfurl_links=False,
            )
            ticket.slack_bot_reply_ts = resp.get("ts")
        except Exception as exc:  # pragma: no cover - network edge
            log.warning("chat.postMessage failed for #%s: %s", ticket.id, exc)

    db.session.commit()
    log.info("Created ticket #%s from Slack message %s", ticket.id, root_ts)
    return ticket


def sync_status_to_slack(ticket, client, base_url):
    """Mirror a ticket's status back to its threaded Slack reply (§6.3).

    No-op (logged) when Slack isn't configured or the reply ts is missing
    (e.g. tickets created while Slack was down, or seeded tickets).
    """
    if client is None:
        log.debug("Slack not configured; skipping status sync for #%s", ticket.id)
        return False
    if not ticket.slack_bot_reply_ts or not ticket.slack_channel_id:
        log.debug("No bot reply ts for #%s; skipping status sync", ticket.id)
        return False
    try:
        client.chat_update(
            channel=ticket.slack_channel_id,
            ts=ticket.slack_bot_reply_ts,
            text=creation_reply(ticket, base_url),
            unfurl_links=False,
        )
        return True
    except Exception as exc:  # pragma: no cover - network edge
        log.warning("chat.update failed for #%s: %s", ticket.id, exc)
        return False


# --- Bolt app wiring -------------------------------------------------------
def build_bolt_app(flask_app):
    """Construct the Bolt app and register handlers, or return None.

    Returns None when Slack credentials are absent so the rest of the app can
    run standalone.
    """
    config = flask_app.config["APP_CONFIG"]
    if not config.slack_enabled:
        log.info("Slack credentials not set; Slack bot disabled.")
        return None

    from slack_bolt import App as BoltApp

    bolt = BoltApp(
        token=config.SLACK_BOT_TOKEN,
        signing_secret=config.SLACK_SIGNING_SECRET,
        # We mount Bolt behind Flask, so let Flask own the route.
        process_before_response=True,
        # Skip the auth.test network call at startup -- the token is validated
        # lazily on first use, so the app boots without outbound access.
        token_verification_enabled=False,
    )

    @bolt.event("message")
    def handle_message(event, logger):
        if should_ignore_message(event, config.SLACK_TICKET_CHANNEL_ID):
            return
        # Runs inside the Flask request (and thus app context) for db access.
        with flask_app.app_context():
            create_ticket_from_event(event, bolt.client, config)

    return bolt

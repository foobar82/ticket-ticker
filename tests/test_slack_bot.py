"""Tests for the Slack ticket-creation core (spec §6), using a fake client."""
from app.config import Config
from app.models import STATUS_TODO, Ticket
from app.slack import bot


class FakeSlackClient:
    """Records outbound calls and returns canned responses."""

    def __init__(self, root_text="root message text"):
        self.root_text = root_text
        self.posted = []
        self.updated = []

    def conversations_replies(self, channel, ts, **kwargs):
        return {"messages": [{"ts": ts, "text": self.root_text}]}

    def chat_getPermalink(self, channel, message_ts):
        return {"permalink": f"https://slack/{channel}/{message_ts}"}

    def chat_postMessage(self, channel, thread_ts, text, **kwargs):
        self.posted.append({"channel": channel, "thread_ts": thread_ts, "text": text})
        return {"ts": f"bot-{thread_ts}"}

    def chat_update(self, channel, ts, text, **kwargs):
        self.updated.append({"channel": channel, "ts": ts, "text": text})
        return {"ok": True}


class Cfg(Config):
    SLACK_TICKET_CHANNEL_ID = "C_TEST"
    BASE_URL = "http://testhost"


def _event(ts, text="hello world", thread_ts=None, **extra):
    e = {"channel": "C_TEST", "ts": ts, "text": text}
    if thread_ts:
        e["thread_ts"] = thread_ts
    e.update(extra)
    return e


# --- Filtering (§6.2 step 2) ---
def test_ignore_bot_messages():
    assert bot.should_ignore_message(_event("1", bot_id="B1"), "C_TEST")


def test_ignore_edits_and_deletes():
    assert bot.should_ignore_message(
        _event("1", subtype="message_changed"), "C_TEST")
    assert bot.should_ignore_message(
        _event("1", subtype="message_deleted"), "C_TEST")


def test_ignore_other_channels():
    assert bot.should_ignore_message(
        {"channel": "OTHER", "ts": "1"}, "C_TEST")


def test_allow_plain_message():
    assert not bot.should_ignore_message(_event("1"), "C_TEST")


# --- Creation (§6.2) ---
def test_create_root_ticket(app_ctx):
    client = FakeSlackClient()
    tk = bot.create_ticket_from_event(_event("100", "Need a filing review"),
                                      client, Cfg())
    assert tk is not None
    assert tk.status == STATUS_TODO
    assert tk.slack_message_ts == "100"
    assert tk.slack_bot_reply_ts == "bot-100"
    assert tk.slack_permalink.endswith("/100")
    assert len(client.posted) == 1
    assert client.posted[0]["thread_ts"] == "100"


def test_title_truncated(app_ctx):
    long = "x" * 200
    tk = bot.create_ticket_from_event(_event("101", long), FakeSlackClient(), Cfg())
    assert len(tk.title) <= bot.TITLE_MAX + 1  # +1 for the ellipsis
    assert tk.description == long


def test_duplicate_root_skipped(app_ctx):
    client = FakeSlackClient()
    bot.create_ticket_from_event(_event("200", "first"), client, Cfg())
    again = bot.create_ticket_from_event(_event("200", "dupe"), client, Cfg())
    assert again is None
    assert Ticket.query.filter_by(slack_message_ts="200").count() == 1


def test_reply_in_tracked_thread_skipped(app_ctx):
    """A reply within an existing ticket thread must not create a ticket (§6.4)."""
    client = FakeSlackClient()
    bot.create_ticket_from_event(_event("300", "root"), client, Cfg())
    # Reply shares the thread root ts -> maps to existing ticket -> skip.
    reply = _event("301", "a comment", thread_ts="300")
    assert bot.create_ticket_from_event(reply, client, Cfg()) is None
    assert Ticket.query.count() == 1


def test_reply_to_non_ticket_uses_thread_root(app_ctx):
    """§6.5: reply to an untracked message anchors the ticket to the root."""
    client = FakeSlackClient(root_text="ORIGINAL ROOT TEXT")
    reply = _event("401", "just replying", thread_ts="400")
    tk = bot.create_ticket_from_event(reply, client, Cfg())
    assert tk.slack_message_ts == "400"  # the root, not the reply
    assert tk.description == "ORIGINAL ROOT TEXT"
    # Bot reply threaded under the root.
    assert client.posted[0]["thread_ts"] == "400"


def test_reply_root_unresolvable_falls_back(app_ctx):
    """If the thread root can't be fetched, anchor to the reply, don't crash."""
    class Broken(FakeSlackClient):
        def conversations_replies(self, channel, ts, **kwargs):
            raise RuntimeError("not in history")

    client = Broken()
    reply = _event("501", "orphan reply", thread_ts="500")
    tk = bot.create_ticket_from_event(reply, client, Cfg())
    assert tk.slack_message_ts == "501"  # fell back to the reply
    assert tk.description == "orphan reply"


# --- Status sync (§6.3) ---
def test_status_sync_calls_chat_update(app_ctx):
    client = FakeSlackClient()
    tk = bot.create_ticket_from_event(_event("600", "x"), client, Cfg())
    tk.status = "Closed"
    ok = bot.sync_status_to_slack(tk, client, "http://testhost")
    assert ok is True
    assert client.updated[0]["ts"] == "bot-600"
    assert "Closed" in client.updated[0]["text"]


def test_status_sync_noop_without_client(app_ctx):
    tk = bot.create_ticket_from_event(_event("700", "x"), FakeSlackClient(), Cfg())
    assert bot.sync_status_to_slack(tk, None, "http://h") is False

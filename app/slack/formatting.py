"""Message templates for the bot's threaded status reply (spec §6.2/§6.3).

The format is kept stable so chat.update edits look clean -- only the status
word/emoji changes between revisions.
"""
from app.models import STATUS_CLOSED, STATUS_IN_PROGRESS, STATUS_TODO

# v2 HOOK: when new statuses are added (§11), give them an emoji here.
STATUS_EMOJI = {
    STATUS_TODO: "🆕",
    STATUS_IN_PROGRESS: "🔧",
    STATUS_CLOSED: "✅",
}


def ticket_url(base_url, ticket_id):
    return f"{base_url.rstrip('/')}/tickets/{ticket_id}"


def status_label(status):
    emoji = STATUS_EMOJI.get(status, "")
    return f"{emoji} {status}".strip()


def creation_reply(ticket, base_url):
    """The bot's threaded reply text, posted once on creation and then edited.

    Example:
        🎫 Ticket #42 created — Status: *🆕 To Do*
        <http://internal-host/tickets/42|View in tracker>
    """
    url = ticket_url(base_url, ticket.id)
    return (
        f"🎫 Ticket #{ticket.id} created — Status: *{status_label(ticket.status)}*\n"
        f"<{url}|View in tracker>"
    )

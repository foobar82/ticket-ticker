"""Ticket business logic shared between the web API and (later) the Slack bot.

Keeping this here -- rather than in the route/handler -- means status sync,
validation, and queries behave identically no matter where the request
originates, and it stays easy to unit-test without a live HTTP/Slack layer.
"""
from app.models import STATUS_CLOSED, STATUSES, Comment, Ticket, db


class ValidationError(ValueError):
    """Raised on bad caller input (invalid status, unknown assignee, etc.)."""


def list_tickets(view="all", user=None):
    """Return tickets for one of the three views (spec §7.1).

    - all:        every ticket
    - mine:       assignee == user, any status
    - mine_open:  assignee == user AND status != Closed
    Most recent first.
    """
    query = Ticket.query
    if view in ("mine", "mine_open"):
        if not user:
            # No current user picked -> nothing is "mine".
            return []
        query = query.filter(Ticket.assignee == user)
        if view == "mine_open":
            query = query.filter(Ticket.status != STATUS_CLOSED)
    elif view != "all":
        raise ValidationError(f"Unknown view: {view!r}")
    return query.order_by(Ticket.created_at.desc(), Ticket.id.desc()).all()


def get_ticket_or_none(ticket_id):
    return db.session.get(Ticket, ticket_id)


def update_ticket(ticket, *, status=None, assignee=None, team_members=None):
    """Apply a status and/or assignee change to a ticket.

    Returns (ticket, status_changed). `status_changed` lets the caller decide
    whether a Slack sync is needed (§6.3) -- only status is mirrored to Slack.
    """
    status_changed = False

    if status is not None:
        if status not in STATUSES:
            raise ValidationError(
                f"Invalid status {status!r}; must be one of {list(STATUSES)}"
            )
        if status != ticket.status:
            ticket.status = status
            status_changed = True

    if assignee is not None:
        # Empty string / explicit null means unassign.
        if assignee == "":
            ticket.assignee = None
        else:
            if team_members is not None and assignee not in team_members:
                raise ValidationError(
                    f"Unknown assignee {assignee!r}; not in the team roster"
                )
            ticket.assignee = assignee

    db.session.commit()
    return ticket, status_changed


def add_comment(ticket, author, body):
    author = (author or "").strip()
    body = (body or "").strip()
    if not author:
        raise ValidationError("A comment author is required")
    if not body:
        raise ValidationError("Comment body cannot be empty")
    comment = Comment(ticket_id=ticket.id, author=author, body=body)
    db.session.add(comment)
    db.session.commit()
    return comment

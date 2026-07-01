"""Ticket business logic shared between the web API and (later) the Slack bot.

Keeping read/query logic here -- rather than in the route -- keeps the views
thin and makes it trivial to unit-test without an HTTP layer. Mutating
operations (status/assign/comments) are added in a later slice.
"""
from app.models import STATUS_CLOSED, Ticket


class ValidationError(ValueError):
    """Raised on bad caller input (unknown view, etc.)."""


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
    from app.models import db

    return db.session.get(Ticket, ticket_id)

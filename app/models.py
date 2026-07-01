"""SQLAlchemy models for the ticketing system (spec §8).

Kept deliberately small. Hooks for deferred v2 work (extra statuses, extra
fields) are flagged inline so extension is cheap later.
"""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# --- Ticket status (spec §2) -------------------------------------------------
# v1 has exactly three states and "Closed" is terminal (§3 non-goals).
#
# v2 HOOK: additional statuses (e.g. "Won't Do", "Duplicate") and reopening
# Closed tickets are deferred (§11). To extend, add the new value here and to
# the <select> in templates/ticket_detail.html -- the column is a plain string
# so no migration is required for new enum members, only validation changes.
STATUS_TODO = "To Do"
STATUS_IN_PROGRESS = "In Progress"
STATUS_CLOSED = "Closed"
STATUSES = (STATUS_TODO, STATUS_IN_PROGRESS, STATUS_CLOSED)


def _utcnow():
    return datetime.now(timezone.utc)


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    status = db.Column(db.String(32), nullable=False, default=STATUS_TODO)

    # One of Config.TEAM_MEMBERS, or NULL when unassigned (§7.3).
    assignee = db.Column(db.String(120), nullable=True)

    # --- Slack linkage (§6) ---
    slack_channel_id = db.Column(db.String(64), nullable=True)
    # The ticket's root message ts. Unique so a thread can only ever map to a
    # single ticket -- this is what prevents double-creation (§6.2/§6.4).
    slack_message_ts = db.Column(db.String(64), nullable=True, unique=True)
    # The bot's threaded status reply ts, edited via chat.update on status
    # change (§6.3). Never re-posted.
    slack_bot_reply_ts = db.Column(db.String(64), nullable=True)
    slack_permalink = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    comments = db.relationship(
        "Comment",
        backref="ticket",
        order_by="Comment.created_at",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_dict(self, include_comments=False):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "assignee": self.assignee,
            "slack_permalink": self.slack_permalink,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }
        if include_comments:
            data["comments"] = [c.to_dict() for c in self.comments]
        return data


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(
        db.Integer, db.ForeignKey("tickets.id"), nullable=False, index=True
    )
    author = db.Column(db.String(120), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "author": self.author,
            "body": self.body,
            "created_at": _iso(self.created_at),
        }


def _iso(dt):
    if dt is None:
        return None
    # Stored naive-UTC by SQLite; mark it as UTC on the way out.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

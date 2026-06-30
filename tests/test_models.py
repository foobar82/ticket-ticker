import pytest
from sqlalchemy.exc import IntegrityError

from app.models import STATUS_TODO, STATUSES, Comment, Ticket, db


def test_status_constants():
    assert STATUSES == ("To Do", "In Progress", "Closed")


def test_create_ticket_defaults(app_ctx):
    t = Ticket(title="x", description="d", slack_message_ts="1")
    db.session.add(t)
    db.session.commit()
    assert t.id is not None
    assert t.status == STATUS_TODO  # default applied
    assert t.assignee is None
    assert t.created_at is not None
    assert t.updated_at is not None


def test_to_dict_includes_comments(app_ctx):
    t = Ticket(title="x", description="d", slack_message_ts="1")
    db.session.add(t)
    db.session.commit()
    db.session.add(Comment(ticket_id=t.id, author="Henry", body="hi"))
    db.session.commit()

    d = t.to_dict(include_comments=True)
    assert d["title"] == "x"
    assert d["status"] == STATUS_TODO
    assert len(d["comments"]) == 1
    assert d["comments"][0]["author"] == "Henry"

    # Without the flag, comments are omitted.
    assert "comments" not in t.to_dict()


def test_slack_message_ts_unique(app_ctx):
    db.session.add(Ticket(title="a", description="d", slack_message_ts="dup"))
    db.session.commit()
    db.session.add(Ticket(title="b", description="d", slack_message_ts="dup"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()

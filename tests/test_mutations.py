"""Tests for the mutating API + service layer (status, assign, comments)."""
import pytest

from app import services
from app.models import (
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_TODO,
    Ticket,
    db,
)


def _seed(app):
    with app.app_context():
        db.session.add_all([
            Ticket(title="a", description="d", status=STATUS_TODO,
                   assignee="Henry", slack_message_ts="1"),
            Ticket(title="c", description="d", status=STATUS_TODO,
                   assignee=None, slack_message_ts="3"),
        ])
        db.session.commit()


# --- Service layer ---
def test_update_status_flags_change(app_ctx):
    t = Ticket(title="x", description="d", slack_message_ts="1")
    db.session.add(t)
    db.session.commit()
    t, changed = services.update_ticket(t, status=STATUS_IN_PROGRESS)
    assert changed is True and t.status == STATUS_IN_PROGRESS
    # Same status again -> not a change (so no needless Slack sync later).
    t, changed = services.update_ticket(t, status=STATUS_IN_PROGRESS)
    assert changed is False


def test_update_invalid_status(app_ctx):
    t = Ticket(title="x", description="d", slack_message_ts="1")
    db.session.add(t)
    db.session.commit()
    with pytest.raises(services.ValidationError):
        services.update_ticket(t, status="Bogus")


def test_assign_unknown_member_rejected(app_ctx):
    t = Ticket(title="x", description="d", slack_message_ts="1")
    db.session.add(t)
    db.session.commit()
    with pytest.raises(services.ValidationError):
        services.update_ticket(t, assignee="Mallory", team_members=["Henry"])


def test_add_comment_validation(app_ctx):
    t = Ticket(title="x", description="d", slack_message_ts="1")
    db.session.add(t)
    db.session.commit()
    with pytest.raises(services.ValidationError):
        services.add_comment(t, author="Henry", body="   ")
    c = services.add_comment(t, author="Henry", body="hello")
    assert c.id is not None and len(t.comments) == 1


# --- API ---
def test_patch_status_and_assignee(app, client):
    _seed(app)
    r = client.patch("/api/tickets/2",
                     json={"status": STATUS_CLOSED, "assignee": "Raj"})
    assert r.status_code == 200
    t = r.get_json()["ticket"]
    assert t["status"] == STATUS_CLOSED and t["assignee"] == "Raj"


def test_patch_unassign(app, client):
    _seed(app)
    r = client.patch("/api/tickets/1", json={"assignee": ""})
    assert r.status_code == 200
    assert r.get_json()["ticket"]["assignee"] is None


def test_patch_invalid_status(app, client):
    _seed(app)
    assert client.patch("/api/tickets/1",
                        json={"status": "Nope"}).status_code == 400


def test_patch_unknown_assignee(app, client):
    _seed(app)
    assert client.patch("/api/tickets/1",
                        json={"assignee": "Mallory"}).status_code == 400


def test_add_and_read_comment(app, client):
    _seed(app)
    r = client.post("/api/tickets/1/comments",
                    json={"author": "Henry", "body": "hi"})
    assert r.status_code == 201
    detail = client.get("/api/tickets/1").get_json()["ticket"]
    assert detail["comments"][0]["body"] == "hi"


def test_add_comment_empty_body_400(app, client):
    _seed(app)
    assert client.post("/api/tickets/1/comments",
                       json={"author": "Henry", "body": "  "}).status_code == 400

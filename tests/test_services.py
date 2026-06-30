import pytest

from app import services
from app.models import (
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_TODO,
    Ticket,
    db,
)


def _mk(title="t", status=STATUS_TODO, assignee=None, ts=None):
    tk = Ticket(
        title=title,
        description="d",
        status=status,
        assignee=assignee,
        slack_message_ts=ts,
    )
    db.session.add(tk)
    db.session.commit()
    return tk


def test_list_views(app_ctx):
    _mk("a", assignee="Henry", status=STATUS_TODO, ts="1")
    _mk("b", assignee="Henry", status=STATUS_CLOSED, ts="2")
    _mk("c", assignee="Raj", status=STATUS_IN_PROGRESS, ts="3")

    assert len(services.list_tickets("all")) == 3
    assert len(services.list_tickets("mine", "Henry")) == 2
    assert len(services.list_tickets("mine_open", "Henry")) == 1
    # mine with no user -> empty
    assert services.list_tickets("mine", None) == []


def test_list_unknown_view(app_ctx):
    with pytest.raises(services.ValidationError):
        services.list_tickets("bogus")


def test_update_status_flags_change(app_ctx):
    tk = _mk(ts="1")
    tk, changed = services.update_ticket(tk, status=STATUS_IN_PROGRESS)
    assert changed is True
    assert tk.status == STATUS_IN_PROGRESS
    # Same status again -> not a change
    tk, changed = services.update_ticket(tk, status=STATUS_IN_PROGRESS)
    assert changed is False


def test_update_invalid_status(app_ctx):
    tk = _mk(ts="1")
    with pytest.raises(services.ValidationError):
        services.update_ticket(tk, status="Bogus")


def test_assign_and_unassign(app_ctx):
    tk = _mk(ts="1")
    services.update_ticket(tk, assignee="Henry", team_members=["Henry"])
    assert tk.assignee == "Henry"
    services.update_ticket(tk, assignee="", team_members=["Henry"])
    assert tk.assignee is None


def test_assign_unknown_member_rejected(app_ctx):
    tk = _mk(ts="1")
    with pytest.raises(services.ValidationError):
        services.update_ticket(tk, assignee="Mallory", team_members=["Henry"])


def test_add_comment_validation(app_ctx):
    tk = _mk(ts="1")
    with pytest.raises(services.ValidationError):
        services.add_comment(tk, author="", body="hi")
    with pytest.raises(services.ValidationError):
        services.add_comment(tk, author="Henry", body="   ")
    c = services.add_comment(tk, author="Henry", body="hello")
    assert c.id is not None
    assert len(tk.comments) == 1

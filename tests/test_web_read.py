from app.models import STATUS_CLOSED, STATUS_TODO, Ticket, db


def _seed(app):
    with app.app_context():
        db.session.add_all([
            Ticket(title="a", description="d", status=STATUS_TODO,
                   assignee="Henry", slack_message_ts="1"),
            Ticket(title="b", description="d", status=STATUS_CLOSED,
                   assignee="Henry", slack_message_ts="2"),
            Ticket(title="c", description="d", status=STATUS_TODO,
                   assignee=None, slack_message_ts="3"),
        ])
        db.session.commit()


def test_list_all(app, client):
    _seed(app)
    r = client.get("/api/tickets?view=all")
    assert r.status_code == 200
    assert len(r.get_json()["tickets"]) == 3


def test_list_mine(app, client):
    _seed(app)
    r = client.get("/api/tickets?view=mine&user=Henry")
    assert len(r.get_json()["tickets"]) == 2


def test_list_mine_open(app, client):
    _seed(app)
    r = client.get("/api/tickets?view=mine_open&user=Henry")
    data = r.get_json()["tickets"]
    assert len(data) == 1
    assert data[0]["title"] == "a"


def test_list_mine_without_user_is_empty(app, client):
    _seed(app)
    r = client.get("/api/tickets?view=mine")
    assert r.get_json()["tickets"] == []


def test_get_ticket_detail(app, client):
    _seed(app)
    r = client.get("/api/tickets/1")
    assert r.status_code == 200
    assert r.get_json()["ticket"]["title"] == "a"


def test_get_missing_ticket_404(app, client):
    r = client.get("/api/tickets/999")
    assert r.status_code == 404
    assert r.get_json()["error"]


def test_pages_render(app, client):
    _seed(app)
    assert client.get("/").status_code == 200
    assert client.get("/mine").status_code == 200
    assert client.get("/mine/open").status_code == 200
    assert client.get("/tickets/1").status_code == 200
    assert client.get("/tickets/999").status_code == 404

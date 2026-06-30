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


def test_list_mine_open(app, client):
    _seed(app)
    r = client.get("/api/tickets?view=mine_open&user=Henry")
    data = r.get_json()["tickets"]
    assert len(data) == 1
    assert data[0]["title"] == "a"


def test_get_ticket_with_comments(app, client):
    _seed(app)
    client.post("/api/tickets/1/comments",
                json={"author": "Henry", "body": "hi"})
    r = client.get("/api/tickets/1")
    assert r.status_code == 200
    t = r.get_json()["ticket"]
    assert len(t["comments"]) == 1
    assert t["comments"][0]["body"] == "hi"


def test_get_missing_ticket(app, client):
    r = client.get("/api/tickets/999")
    assert r.status_code == 404


def test_patch_status_and_assignee(app, client):
    _seed(app)
    r = client.patch("/api/tickets/3",
                     json={"status": STATUS_CLOSED, "assignee": "Raj"})
    assert r.status_code == 200
    t = r.get_json()["ticket"]
    assert t["status"] == STATUS_CLOSED
    assert t["assignee"] == "Raj"


def test_patch_unassign(app, client):
    _seed(app)
    r = client.patch("/api/tickets/1", json={"assignee": ""})
    assert r.status_code == 200
    assert r.get_json()["ticket"]["assignee"] is None


def test_patch_invalid_status(app, client):
    _seed(app)
    r = client.patch("/api/tickets/1", json={"status": "Nope"})
    assert r.status_code == 400


def test_patch_unknown_assignee(app, client):
    _seed(app)
    r = client.patch("/api/tickets/1", json={"assignee": "Mallory"})
    assert r.status_code == 400


def test_add_comment_empty_body(app, client):
    _seed(app)
    r = client.post("/api/tickets/1/comments",
                    json={"author": "Henry", "body": "  "})
    assert r.status_code == 400


def test_web_pages_render(app, client):
    _seed(app)
    assert client.get("/").status_code == 200
    assert client.get("/mine").status_code == 200
    assert client.get("/mine/open").status_code == 200
    assert client.get("/tickets/1").status_code == 200
    assert client.get("/tickets/999").status_code == 404

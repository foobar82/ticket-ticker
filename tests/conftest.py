import pytest

from app import create_app
from app.config import Config
from app.models import db


class TestConfig(Config):
    # In-memory DB so tests never touch a real file.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    TEAM_MEMBERS = ["Henry", "Raj", "Priya"]
    # No Slack creds -> Slack features stay disabled (no /slack/events route,
    # no outbound calls). The Slack logic is exercised with a fake client.
    SLACK_BOT_TOKEN = None
    SLACK_SIGNING_SECRET = None
    SLACK_TICKET_CHANNEL_ID = "C_TEST"
    BASE_URL = "http://testhost"


@pytest.fixture
def app():
    app = create_app(TestConfig())
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def app_ctx(app):
    with app.app_context():
        yield

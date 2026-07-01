import pytest

from app import create_app
from app.config import Config
from app.models import db


class TestConfig(Config):
    # In-memory DB so tests never touch a real file.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    TEAM_MEMBERS = ["Henry", "Raj", "Priya"]


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

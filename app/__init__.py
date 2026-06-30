"""Flask application factory (spec §10).

This first slice wires up the database only. Web pages, the JSON API, and the
Slack bot are layered on in subsequent changes.
"""
import logging

from flask import Flask

from app.config import Config
from app.models import db


def create_app(config=None):
    app = Flask(__name__)
    config = config or Config()
    app.config.from_object(config)
    # Stash the live Config instance so future blueprints can read TEAM_MEMBERS
    # etc. without re-reading the environment.
    app.config["APP_CONFIG"] = config

    logging.basicConfig(level=logging.INFO)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    return app

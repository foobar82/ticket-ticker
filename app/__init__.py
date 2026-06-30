"""Flask application factory (spec §10).

Wires up the database, web pages, JSON API, and -- when Slack credentials are
present -- the Slack Bolt event endpoint at /slack/events.
"""
import logging

from flask import Flask, jsonify, request

from app.config import Config
from app.models import db


def create_app(config=None):
    app = Flask(__name__)
    config = config or Config()
    app.config.from_object(config)
    # Stash the live Config instance so blueprints can read TEAM_MEMBERS,
    # BASE_URL, Slack creds, etc. without re-reading the environment.
    app.config["APP_CONFIG"] = config

    logging.basicConfig(level=logging.INFO)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    # --- Blueprints ---
    from app.routes.api import api_bp
    from app.routes.web import web_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    _register_slack(app, config)
    _register_errorhandlers(app)

    return app


def _register_slack(app, config):
    """Mount the Bolt events endpoint behind Flask, if Slack is configured."""
    from app.slack.bot import build_bolt_app

    bolt = build_bolt_app(app)
    if bolt is None:
        return

    from slack_bolt.adapter.flask import SlackRequestHandler

    handler = SlackRequestHandler(bolt)

    @app.post("/slack/events")
    def slack_events():
        return handler.handle(request)

    app.logger.info("Slack events endpoint mounted at /slack/events")


def _register_errorhandlers(app):
    @app.errorhandler(404)
    def not_found(err):
        if request.path.startswith("/api/"):
            return jsonify(error="Not found"), 404
        return ("Not found", 404)

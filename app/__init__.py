"""Flask application factory (spec §10).

Wires up the database, the server-rendered web pages, and the read side of the
JSON API. Mutating endpoints and the Slack bot are layered on later.
"""
import logging

from flask import Flask, jsonify, request

from app.config import Config
from app.models import db


def create_app(config=None):
    app = Flask(__name__)
    config = config or Config()
    app.config.from_object(config)
    # Stash the live Config instance so blueprints can read TEAM_MEMBERS etc.
    # without re-reading the environment.
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

    _register_errorhandlers(app)

    return app


def _register_errorhandlers(app):
    @app.errorhandler(404)
    def not_found(err):
        if request.path.startswith("/api/"):
            return jsonify(error="Not found"), 404
        return ("Not found", 404)

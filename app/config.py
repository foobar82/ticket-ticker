"""Application configuration.

All settings are read from environment variables (loaded from a local
`.env` file in development via python-dotenv). There is intentionally no
auth-related config in v1 -- see spec §3 (Non-goals).
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _team_members():
    raw = os.environ.get("TEAM_MEMBERS", "").strip()
    if raw:
        return [name.strip() for name in raw.split(",") if name.strip()]
    # Fallback default roster so the app is usable out of the box.
    return ["Henry", "Raj", "Priya", "Sam"]


class Config:
    # --- Slack ---
    SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
    SLACK_TICKET_CHANNEL_ID = os.environ.get("SLACK_TICKET_CHANNEL_ID")

    # --- App ---
    BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000").rstrip("/")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///ticketing.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Fixed roster for the name picker (§7.3). Not a security boundary (§4).
    TEAM_MEMBERS = _team_members()

    @property
    def slack_enabled(self):
        """Slack features are only wired up when we have the credentials.

        This lets the web UI / seed script run standalone in development
        without a Slack app configured.
        """
        return bool(self.SLACK_BOT_TOKEN and self.SLACK_SIGNING_SECRET)

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
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///ticketing.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Fixed roster for the name picker (§7.3). Not a security boundary (§4).
    TEAM_MEMBERS = _team_members()

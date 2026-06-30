# Financing & Compliance Ticketing (v1)

A rudimentary ticketing/workflow tool for a small financing & compliance team.
Tickets are created from a dedicated Slack channel and managed via a simple
internal web UI. **Prototype** — no auth, single team, internally hosted.

> This is the first slice of the build: project scaffold + data model. The
> web UI, JSON API, and Slack bot are added in follow-up changes (see the
> build order in spec §12).

## This slice

- Flask application factory (`app/__init__.py`) wiring up the database.
- SQLAlchemy models (`app/models.py`): `Ticket` and `Comment` (spec §8).
- A seed script for sample data so later UI work has something to render.

The three v1 statuses (**To Do → In Progress → Closed**, Closed terminal) and
the `slack_message_ts` uniqueness constraint that will prevent double-creation
are already modelled. Deferred v2 work is flagged with `v2 HOOK` comments.

## Quick start

```bash
pip install -r requirements.txt
python seed.py        # create tables + sample tickets
python -m pytest      # run the tests
```

The DB tables are created automatically on first `create_app()`.

## Configuration

Copy `.env.example` to `.env`:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL (defaults to a local SQLite file) |
| `TEAM_MEMBERS` | Comma-separated roster for the (upcoming) name picker |

## Identity model (no auth)

There is no login (spec §3/§4). A later slice adds a name picker whose value is
a convenience for "assigned to me" filtering, **not** a security boundary.

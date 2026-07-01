# Financing & Compliance Ticketing (v1)

A rudimentary ticketing/workflow tool for a small financing & compliance team.
Tickets are created from a dedicated Slack channel and managed via a simple
internal web UI. **Prototype** — no auth, single team, internally hosted.

> Build progress: scaffold + data model, the read-only web UI, and now the
> **interactive web UI** (status / self-assign / comments). The Slack bot
> follows in the final slice (spec build order §12).

## What works so far

- SQLAlchemy `Ticket` + `Comment` models (spec §8).
- Three web views (spec §7.1): **All** (`/`), **Assigned to me** (`/mine`),
  **Open & assigned to me** (`/mine/open`).
- Ticket detail page (`/tickets/<id>`): change status, self-assign / unassign,
  and add comments — all via `fetch()` against the API, no full reload.
- JSON API: list, detail, `PATCH` status/assignee, and add comment.
- localStorage name picker in the header (spec §4/§7.3): a convenience for
  "assigned to me" filtering and as the comment/assign actor, **not** a
  security boundary.

## Architecture

- **Backend:** Python + Flask (app factory in `app/__init__.py`).
- **DB:** SQLite via Flask-SQLAlchemy (`app/models.py`).
- **Frontend:** server-rendered Jinja2 + a little vanilla JS (`app/static/`).
  List rows are loaded client-side from the API so the "mine" views can use the
  localStorage name picker without the server knowing the current user.

## Quick start

```bash
pip install -r requirements.txt
python seed.py        # optional: sample tickets
python run.py         # http://localhost:5000  (added with the run entrypoint)
python -m pytest      # run the tests
```

The DB tables are created automatically on first boot.

## Configuration

Copy `.env.example` to `.env`:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL (defaults to a local SQLite file) |
| `TEAM_MEMBERS` | Comma-separated roster for the name picker |

## API (so far)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/tickets?view=all\|mine\|mine_open&user=<name>` | List tickets |
| GET | `/api/tickets/<id>` | Ticket detail incl. comments |
| PATCH | `/api/tickets/<id>` | Update status and/or assignee |
| POST | `/api/tickets/<id>/comments` | Add a comment |

The Slack `POST /slack/events` endpoint is added in the final slice.

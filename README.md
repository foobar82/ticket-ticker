# Financing & Compliance Ticketing (v1)

A rudimentary ticketing/workflow tool for a small financing & compliance team.
Tickets are created from a dedicated Slack channel and managed via a simple
internal web UI. **Prototype** — no auth, single team, internally hosted. See
[`SPEC` in the project history] for the full v1 specification.

## What it does (v1)

- Watches one Slack channel and turns each new top-level message into a ticket.
- The bot posts a threaded reply with the ticket link + status, and **edits**
  that same reply (`chat.update`) whenever the status changes.
- Web UI with three views: **All**, **Assigned to me**, **Open & assigned to
  me**.
- Three statuses: **To Do → In Progress → Closed** (Closed is terminal in v1).
- Self-assignment and lightweight per-ticket comments.

Explicitly **out of scope** for v1: auth/permissions, SLAs/priorities/due
dates, reporting, slash commands/modals, multi-channel, notifications beyond
the Slack thread, and deletion/archiving. Extension points for these are
flagged with `v2 HOOK` comments in the code (see `app/models.py`,
`app/slack/formatting.py`).

## Architecture

```
Slack channel ──(Events API)──▶ Flask app (Bolt) ──▶ SQLite
                                       ▲
Browser ──(HTTP/JSON)──────────────────┘
```

- **Backend:** Python + Flask (app factory in `app/__init__.py`).
- **Slack:** `slack-bolt`, mounted behind Flask at `POST /slack/events`.
- **DB:** SQLite via Flask-SQLAlchemy (`app/models.py`).
- **Frontend:** server-rendered Jinja2 + a little vanilla JS (`app/static/`).

See `app/` for the layout described in the spec (§10).

## Identity model (no auth)

There is no login. The header has a name picker populated from a fixed roster
(`TEAM_MEMBERS`). The choice is stored in `localStorage` and sent with requests
that need an actor (self-assign, comments). It is a **convenience for filtering,
not a security boundary** (spec §4).

## Quick start (web UI only, no Slack)

```bash
pip install -r requirements.txt
python seed.py        # optional: sample tickets
python run.py         # http://localhost:5000
```

The DB tables are created automatically on first boot. Without Slack
credentials the bot is simply disabled and the web UI runs standalone.

## Enabling Slack

1. Create a Slack app, enable the **Events API**, and subscribe to
   `message.channels` (or `message.groups` for a private channel).
2. Bot token scopes: `channels:history`, `chat:write`, `channels:read`
   (`groups:*` equivalents for a private channel).
3. Invite the bot to the dedicated channel.
4. Copy `.env.example` to `.env` and fill in:

   | Variable | Purpose |
   |---|---|
   | `SLACK_BOT_TOKEN` | Bot User OAuth token (`xoxb-…`) |
   | `SLACK_SIGNING_SECRET` | Verifies inbound Events API requests |
   | `SLACK_TICKET_CHANNEL_ID` | The single channel to watch |
   | `BASE_URL` | Public base URL, used for ticket links in Slack |
   | `TEAM_MEMBERS` | Comma-separated roster for the name picker |

5. Point the Slack app's Request URL at `https://<host>/slack/events`.

### How tickets are created (spec §6)

- New top-level message → new ticket (`To Do`, unassigned). The bot replies in
  thread with the ticket link.
- Bot/edited/deleted messages are ignored.
- A reply **inside an existing ticket thread** is treated as discussion, not a
  new ticket (v1 keeps Slack-side discussion in Slack; web comments are a
  separate log).
- A reply to a message that *isn't* a tracked ticket anchors the ticket to the
  **thread root**; if the root can't be resolved it falls back to the reply and
  logs a warning (spec §6.5).

## API (used by the web UI)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/tickets?view=all\|mine\|mine_open&user=<name>` | List tickets |
| GET | `/api/tickets/<id>` | Ticket detail incl. comments |
| PATCH | `/api/tickets/<id>` | Update status and/or assignee |
| POST | `/api/tickets/<id>/comments` | Add a comment |
| POST | `/slack/events` | Slack Events API (Bolt) |

## Tests

```bash
python -m pytest
```

Covers the service layer, the JSON API, page rendering, and the Slack
ticket-creation/sync logic (with a fake Slack client — no network needed).

## Docker (optional)

```bash
docker build -t ticketing .
docker run --env-file .env -p 5000:5000 ticketing
```

## Deferred to v2 (spec §11)

Extra statuses / reopening, message-edit backfill, editing title/description,
multi-channel/multi-team, and real auth. Hooks are flagged in code.

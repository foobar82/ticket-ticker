"""Seed the local DB with sample tickets so the web UI is usable standalone
(spec §12 build step 1) -- no Slack required.

Usage: python seed.py
"""
from app import create_app
from app.models import (
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_TODO,
    Comment,
    Ticket,
    db,
)

SAMPLE = [
    {
        "title": "Q2 regulatory filing checklist needs review",
        "description": "Can someone sanity-check the Q2 filing checklist before "
        "we submit on Friday? A few line items look stale.",
        "status": STATUS_TODO,
        "assignee": None,
    },
    {
        "title": "Vendor KYC docs missing for Acme Capital",
        "description": "Acme Capital onboarding is blocked — we don't have their "
        "updated beneficial-ownership docs. Chasing the relationship manager.",
        "status": STATUS_IN_PROGRESS,
        "assignee": "Raj",
        "comments": [
            ("Raj", "Emailed the RM, waiting on a reply."),
            ("Henry", "Flag it on the compliance standup if no reply by Weds."),
        ],
    },
    {
        "title": "Annual AML training reminder",
        "description": "Send the annual AML training reminder to the whole desk.",
        "status": STATUS_CLOSED,
        "assignee": "Priya",
        "comments": [("Priya", "Sent — 100% completion logged.")],
    },
]


def main():
    app = create_app()
    with app.app_context():
        if Ticket.query.count():
            print("DB already has tickets; skipping seed.")
            return
        for i, row in enumerate(SAMPLE, start=1):
            comments = row.pop("comments", [])
            # Fake Slack ts values so the column stays unique without a real
            # Slack message behind it.
            ticket = Ticket(slack_message_ts=f"seed-{i}", **row)
            db.session.add(ticket)
            db.session.flush()
            for author, body in comments:
                db.session.add(
                    Comment(ticket_id=ticket.id, author=author, body=body)
                )
        db.session.commit()
        print(f"Seeded {len(SAMPLE)} tickets.")


if __name__ == "__main__":
    main()

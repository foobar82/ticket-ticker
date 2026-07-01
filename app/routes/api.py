"""JSON API used by the web UI's vanilla-JS bits (spec §9).

Read + mutating endpoints. No auth (§3/§4): the `user`/`author` value is
supplied by the client's name picker and is a convenience, not a boundary.

NOTE: status changes will additionally be mirrored back to Slack (§6.3) once
the Slack bot slice lands; that hook is wired into `patch_ticket` then.
"""
from flask import Blueprint, current_app, jsonify, request

from app import services

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Map the public view name to the internal one.
_VIEW_ALIASES = {
    "all": "all",
    "mine": "mine",
    "mine_open": "mine_open",
}


@api_bp.get("/tickets")
def list_tickets():
    view = _VIEW_ALIASES.get(request.args.get("view", "all"), "all")
    user = request.args.get("user") or None
    try:
        tickets = services.list_tickets(view=view, user=user)
    except services.ValidationError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(tickets=[t.to_dict() for t in tickets])


@api_bp.get("/tickets/<int:ticket_id>")
def get_ticket(ticket_id):
    ticket = services.get_ticket_or_none(ticket_id)
    if ticket is None:
        return jsonify(error="Ticket not found"), 404
    return jsonify(ticket=ticket.to_dict(include_comments=True))


@api_bp.patch("/tickets/<int:ticket_id>")
def patch_ticket(ticket_id):
    ticket = services.get_ticket_or_none(ticket_id)
    if ticket is None:
        return jsonify(error="Ticket not found"), 404

    payload = request.get_json(silent=True) or {}
    config = current_app.config["APP_CONFIG"]

    # `assignee` may be explicitly null/"" to unassign, so check presence.
    status = payload.get("status")
    assignee = payload["assignee"] if "assignee" in payload else None

    try:
        ticket, _status_changed = services.update_ticket(
            ticket,
            status=status,
            assignee=assignee,
            team_members=config.TEAM_MEMBERS,
        )
    except services.ValidationError as exc:
        return jsonify(error=str(exc)), 400

    return jsonify(ticket=ticket.to_dict(include_comments=True))


@api_bp.post("/tickets/<int:ticket_id>/comments")
def add_comment(ticket_id):
    ticket = services.get_ticket_or_none(ticket_id)
    if ticket is None:
        return jsonify(error="Ticket not found"), 404

    payload = request.get_json(silent=True) or {}
    try:
        comment = services.add_comment(
            ticket, author=payload.get("author"), body=payload.get("body")
        )
    except services.ValidationError as exc:
        return jsonify(error=str(exc)), 400

    return jsonify(comment=comment.to_dict()), 201

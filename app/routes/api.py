"""JSON API used by the web UI's vanilla-JS bits (spec §9).

This slice covers the read endpoints (list + detail). Mutating endpoints
(status/assign/comments) are added in a later slice. No auth (§3/§4).
"""
from flask import Blueprint, jsonify, request

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

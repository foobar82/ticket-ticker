"""Server-rendered page routes (spec §7).

The three list views share one template; the actual rows are loaded client-side
from the JSON API so that "assigned to me" can use the localStorage name picker
(§4/§7.3) without the server needing to know the current user.
"""
from flask import Blueprint, abort, current_app, render_template

from app import services

web_bp = Blueprint("web", __name__)


def _team_members():
    return current_app.config["APP_CONFIG"].TEAM_MEMBERS


@web_bp.get("/")
def all_tickets():
    return render_template(
        "ticket_list.html",
        view="all",
        view_title="All tickets",
        team_members=_team_members(),
    )


@web_bp.get("/mine")
def my_tickets():
    return render_template(
        "ticket_list.html",
        view="mine",
        view_title="Assigned to me",
        team_members=_team_members(),
    )


@web_bp.get("/mine/open")
def my_open_tickets():
    return render_template(
        "ticket_list.html",
        view="mine_open",
        view_title="Open, assigned to me",
        team_members=_team_members(),
    )


@web_bp.get("/tickets/<int:ticket_id>")
def ticket_detail(ticket_id):
    ticket = services.get_ticket_or_none(ticket_id)
    if ticket is None:
        abort(404)
    return render_template(
        "ticket_detail.html",
        ticket=ticket,
        team_members=_team_members(),
    )

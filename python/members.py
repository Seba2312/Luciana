# members.py  (put next to auth.py / profile.py)
from flask import Blueprint, render_template, session, jsonify, request, abort, current_app, redirect, url_for
from python.auth import login_required
from python.db import list_members, set_chair, kick_user, gift_sqm, reset_gifts_for_user

members_bp = Blueprint("members_bp", __name__, template_folder="templates")


@members_bp.route("/members")
@login_required
def members_page():
    """Render the page listing all apartment members."""
    code = session.get("apartment_code")
    if not code:
        abort(404)

    members = list_members(code)
    me = next((m for m in members if m["uid"] == session["uid"]), {})
    return render_template(
        "members.html",
        members=members,
        current_uid=session["uid"],
        current_is_chair=me.get("is_chair", False),
    )


@members_bp.route("/members/api/set_chair", methods=["POST"])
@login_required
def api_set_chair():
    """Make another member the chair if the current user is chair."""
    if not request.is_json:
        abort(400)
    code = session.get("apartment_code")
    members_lst = list_members(code)
    me = next((m for m in members_lst if m["uid"] == session["uid"]), {})
    if not me.get("is_chair"):
        abort(403)

    target_uid = request.json.get("uid")
    set_chair(code, target_uid)
    return jsonify(success=True)


@members_bp.route("/members/api/kick", methods=["POST"])
@login_required
def api_kick():
    """Kick a user from the apartment if the current user is chair."""
    if not request.is_json:
        abort(400)
    code = session.get("apartment_code")
    members_lst = list_members(code)
    me = next((m for m in members_lst if m["uid"] == session["uid"]), {})

    if not me.get("is_chair"):
        abort(403)

    target_uid = request.json.get("uid")
    kick_user(code, target_uid)
    return jsonify(success=True)



@members_bp.route("/members/api/gift", methods=["POST"])
@login_required
def api_gift():
    """Transfer square meters from the current user to another."""
    data = request.get_json(force=True)
    try:
        gift_sqm(
          session["apartment_code"],
          session["uid"],
          data["to_uid"],
          int(data["sqm"])
        )
    except ValueError as e:
        return jsonify(success=False, error=str(e)), 400
    return jsonify(success=True)

@members_bp.route("/members/api/reset_gifts", methods=["POST"])
@login_required
def api_reset_gifts():
    """Reset the current user's gifted square meter tally."""
    reset_gifts_for_user(session["apartment_code"], session["uid"])
    return jsonify(success=True)

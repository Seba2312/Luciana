from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for
from firebase_admin import auth as admin_auth
from python.auth import login_required
from python.db import (
    get_user,
    update_user_settings,
    delete_user_document,
    DEFAULT_CUSTOMIZATION,
)

profile_bp = Blueprint("profile_bp", __name__, template_folder="templates")

AVATAR_COLOURS = [
    "red-500","orange-500","amber-500","yellow-500",
    "lime-500","green-500","emerald-500","teal-500",
    "cyan-500","sky-500","blue-500","indigo-500",
    "violet-500","fuchsia-500","rose-500"
]

@profile_bp.route("/settings")
@login_required
def settings_page():
    """Display the profile settings form."""
    uid  = session["uid"]
    user = get_user(uid) or {}
    user["customization"] = user.get("customization", DEFAULT_CUSTOMIZATION)
    user["variant"] = user.get("variant", "A")
    return render_template(
        "settings.html",
        user=user,
        avatar_colours=AVATAR_COLOURS,
    )

@profile_bp.route("/settings/update", methods=["POST"])
@login_required
def update_profile():
    """Update the stored profile details for the user."""
    uid   = session["uid"]
    data  = request.get_json(force=True)
    first = data.get("first_name", "").strip()
    last  = data.get("last_name", "").strip()
    sqm   = int(data.get("sqm", 0))
    avatar= data.get("avatar", "")
    customization = data.get("customization")

    if not (first and last and sqm >= 0):
        return jsonify(success=False, error="Invalid data"), 400

    update_user_settings(uid, first, last, sqm, avatar, customization)
    session["first_name"] = first
    session["avatar"]     = avatar
    if customization is not None:
        session["customization"] = customization
    return jsonify(success=True)

@profile_bp.route("/settings/delete", methods=["POST"])
@login_required
def delete_account():
    """Delete the current user's account and data."""
    uid = session["uid"]
    data = request.get_json(force=True)
    if data.get("confirmation","") != "DELETE":
        return jsonify(success=False, error="Type DELETE to confirm"), 400

    try:
        admin_auth.delete_user(uid)
    except Exception as e:
        pass

    delete_user_document(uid)

    session.clear()
    return jsonify(success=True, redirect=url_for("auth_bp.login_page"))

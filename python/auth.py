import os

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from firebase_admin import auth as admin_auth, credentials, initialize_app
import requests, time

from config import FIREBASE_WEB_CONFIG, cred, GOOGLE_MEET_CLIENT_ID, GOOGLE_MEET_CLIENT_SECRET
from python.db import (
    get_user,
    create_user_if_absent,
    update_profile,
    save_calendar_token,
    start_session,
    end_session,
    DEFAULT_CUSTOMIZATION,
)

auth_bp = Blueprint("auth_bp", __name__)




from flask import send_from_directory

@auth_bp.route("/login/googlecd7fa5c64986813d.html")
def google_verification():
    """Serve the Google site verification file."""

    print("Exists:", os.path.exists("static/verify/googlecd7fa5c64986813d.html"))

    path = os.path.abspath("static/verify/googlecd7fa5c64986813d.html")
    print("Expected path:", path)
    print("Exists:", os.path.exists(path))

    return send_from_directory("static/verify", "googlecd7fa5c64986813d.html")


@auth_bp.route("/firebase-config")
def firebase_config():
    """Hand the dict to the browser so Firebase JS can initialise."""
    return jsonify(FIREBASE_WEB_CONFIG)


@auth_bp.route("/login")
def login_page():
    """Render the login page."""
    return render_template("auth/login.html")


@auth_bp.route("/complete_profile")
def complete_profile_page():
    """Page for users to finish setting up their profile."""

    uid = request.args.get("uid")
    if not uid:
        return "uid missing", 400
    variant = session.get("variant", "A")
    video_id = "VPPKt7m0lRU" if variant == "A" else "XvnovRTBrMk"
    return render_template("auth/complete_profile.html", uid=uid, video_id=video_id)


@auth_bp.route("/api/add_user", methods=["POST"])
def api_add_user():
    """Create a user entry and store calendar credentials."""

    data = request.get_json(force=True)
    uid = data["uid"]
    email = data["email"]

    create_user_if_absent(uid, email)

    save_calendar_token(
        uid,
        access=data.get("access_token"),
        refresh=None,
        expires=time.time() + int(data.get("expires_in", 3600))
    )
    return jsonify(success=True)


@auth_bp.route("/api/user_status", methods=["POST"])
def api_user_status():
    """Return whether the user profile is complete and calendar is linked."""

    uid = request.get_json(force=True)["uid"]
    user = get_user(uid)
    if user is None:
        create_user_if_absent(uid, "<unknown>")
        user = get_user(uid)

    missing_info = not all([user.get("first_name"), user.get("last_name"), user.get("sqm")])
    exp_ts = user.get("gcal_exp") or 0
    needs_calendar = (not user.get("gcal_access")) or (time.time() >= exp_ts)

    return jsonify(success=True,
                   missing_info=missing_info,
                   needs_calendar=needs_calendar)


@auth_bp.route("/api/complete_profile", methods=["POST"])
def api_complete_profile():
    """Fill in the remaining profile fields for a user."""

    data = request.get_json(force=True)
    uid = data["uid"]
    update_profile(uid, data["first_name"], data["last_name"], int(data["sqm"]))
    return jsonify(success=True)


@auth_bp.route("/api/set_session", methods=["POST"])
def api_set_session():
    """Start a new session for the specified UID."""
    uid = request.get_json(force=True)["uid"]
    user = get_user(uid)
    if not user:
        return jsonify(success=False), 404

    if session.get("uid") and session.get("session_id"):
        end_session(session["uid"], session["session_id"])

    session.clear()
    session["uid"] = uid
    session["role"] = user["role"]
    session["first_name"] = user["first_name"]
    session["apartment_code"] = (user.get("apartment_code"))
    session["avatar"] = user["avatar"]
    session["variant"] = user.get("variant", "A")

    cust = user.get("customization", DEFAULT_CUSTOMIZATION)
    if session["variant"] == "B":
        cust = {k: False for k in DEFAULT_CUSTOMIZATION}

    session["customization"] = cust

    session["session_id"] = start_session(uid)

    return jsonify(success=True)



def login_required(view):
    """Decorator redirecting anonymous users to the login page."""
    from functools import wraps
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "uid" not in session:
            return redirect(url_for("auth_bp.login_page"))
        return view(*args, **kwargs)

    return wrapped



@auth_bp.route("/api/store_google_code", methods=["POST"])
@login_required
def api_store_google_code():
    """Exchange an OAuth code for tokens and store them."""

    code = request.json["code"]
    token = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_MEET_CLIENT_ID,
            "client_secret": GOOGLE_MEET_CLIENT_SECRET,
            "redirect_uri": "postmessage",
            "grant_type": "authorization_code",
        }
    ).json()

    save_calendar_token(session["uid"],
                        access=token.get("access_token"),
                        refresh=None,
                        expires=time.time() + token.get("expires_in", 3600))

    return jsonify(success=True, exp=time.time() + token["expires_in"])

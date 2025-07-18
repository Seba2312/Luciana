
from flask import Flask, render_template, request, redirect, session, url_for, abort, current_app
from datetime import datetime, timedelta

from config import MAPS_API_KEY
from placeholder_loader import members_housing
from python.auth import auth_bp, login_required
from python.db import (
    add_apartment_to_user,
    generate_code,
    create_apartment,
    join_apartment,
    list_meetings,
    bulk_create_demo_users,
    gift_sqm,
    _seed_demo_meetings,
    get_user,
    record_click,
    start_session,
    end_session,
)
from python.meetings import meet_bp
from python.members import members_bp
from python.past_meetings import past_meet_bp
from python.profile import profile_bp
from python.questionnaire import questionnaire_bp

app = Flask(__name__)
app.secret_key = "replace-with-your-own-secret"


@app.context_processor
def inject_maps_key():
    """Expose the Google Maps API key to templates."""
    return dict(MAPS_API_KEY=MAPS_API_KEY)

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(profile_bp)
app.register_blueprint(members_bp)
app.register_blueprint(meet_bp)
app.register_blueprint(past_meet_bp)
app.register_blueprint(questionnaire_bp)



def joined() -> bool:
    """Return True if the current user is linked to an apartment."""
    return bool(session.get("apartment_code"))


@app.route("/logout")
def logout():
    """Clear the session and record the end of the current login."""
    uid = session.get("uid")
    sid = session.get("session_id")
    if uid and sid:
        end_session(uid, sid)
    session.clear()
    return redirect(url_for("auth_bp.login_page"))


def _partition_meetings(items):
    """Split meeting list into current, upcoming and past buckets."""

    now   = datetime.now()
    near  = timedelta(hours=5)

    current  = None
    upcoming = []
    past     = []

    for m in items:
        iso = m.get("date_iso") or m.get("start_iso")
        if not iso:
            continue
        dt  = datetime.fromisoformat(iso)
        m["date_human"] = dt.strftime("%d %b %Y %H:%M")

        if -near <= dt - now <= near and current is None:
            current = m
        elif dt >= now:
            upcoming.append(m)
        else:
            past.append(m)

    upcoming.sort(key=lambda x: x["start_iso"])
    past.sort(key=lambda x: x["start_iso"])
    return current, upcoming, past



@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET","POST"])
@login_required
def home():
    """Homepage: join/create apartment and list meetings."""
    if request.method == "POST":
        uid = session["uid"]
        code = request.form.get("code", "").strip()

        if "create_entity" in request.form:
            code = generate_code()
            create_apartment(code, uid)
            add_apartment_to_user(uid,code)
        elif code:
            join_apartment(code, uid)
            add_apartment_to_user(uid,code)


        session["apartment_code"] = code or None

    joined = bool(session.get("apartment_code"))
    print(session.get("apartment_code"))
    print(joined)

    meetings = list_meetings(session["apartment_code"]) if joined else []
    current, upcoming, past = _partition_meetings(meetings)
    user = get_user(session["uid"])

    return render_template(
        "home.html",
        joined=joined,
        current=current,
        upcoming=upcoming,
        past=past,
        user=user,
    )





@app.route("/dev/seed_demo")
def dev_seed_demo():
    """Populate the DB with demo users and meetings."""

    uid  = session["uid"]

    code = session.get("apartment_code")
    if not code:
        code = generate_code()
        create_apartment(code, chair_uid=uid)
        add_apartment_to_user(uid, code)
        session["apartment_code"] = code

    bulk_create_demo_users(code, members_housing)

    _seed_demo_meetings(code, creator_uid=uid)
    return redirect(url_for("members_bp.members_page"))


@app.route("/metrics/click", methods=["POST"])
@login_required
def metrics_click():
    """Record a simple click event for analytics."""
    data = request.get_json(force=True)
    event = data.get("event")
    dur = data.get("duration")
    page = data.get("page")
    label = data.get("label")
    if event:
        record_click(session["uid"], event, duration=dur, page=page, label=label)
    return {"success": True}


@app.route("/privacy")
def privacy_page():
    """Show the privacy policy page."""
    return render_template("privacy.html")


@app.route("/terms")
def terms_page():
    """Render the terms-of-service page."""
    return render_template("terms.html")


@app.route("/help")
def help_page():
    """Contextual help page for different app sections."""
    page = request.args.get("page", "home")
    descriptions = {
        "home": (
            "The home page acts as your dashboard and landing area. "
            "It lists upcoming meetings and those that already took place so you can quickly see what is next. "
            "Use the join or create form at the top to manage your apartment group."
        ),
        "members_bp.members_page": (
            "The members page shows everyone currently in your apartment. "
            "Here you can promote a new chair, gift square metres and even remove a member when necessary. "
            "All membership management happens right here."
        ),
        "profile_bp.settings_page": (
            "On the settings page you can update your personal information and avatar. "
            "Changing colours or names here immediately updates your profile across the app. "
            "Use the save button at the bottom to confirm any adjustments."
        ),
        "meet_bp.meeting_page": (
            "The meeting detail view gives you full control over a single meeting. "
            "Attendance buttons let you specify whether you'll be there live, join online or skip the meeting. "
            "Other controls update the location, open or copy the online link, add and vote on topics, generate a schedule or delete the meeting if you are the organiser."
        ),
    }
    desc = descriptions.get(page, "This page provides information about the application.")
    variant = session.get("variant", "A")
    video_id = "VPPKt7m0lRU" if variant == "A" else "XvnovRTBrMk"
    return render_template("help.html", description=desc, video_id=video_id)



@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 error handler."""
    print("error")
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True, port=5002)

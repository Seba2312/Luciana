from flask import Blueprint, render_template, session, request, abort, jsonify, redirect, url_for
from python.auth import login_required
from python.db import *
import datetime, dateutil.parser as du
from config import firestoreDatabase
from python.google_meets import create_google_meet

meet_bp = Blueprint("meet_bp", __name__, template_folder="templates")


@meet_bp.route("/meeting/new")
@login_required
def meeting_new_page():
    """Render the page used to create a new meeting."""
    return render_template("meeting_new.html")


@meet_bp.route("/meeting/<mid>", methods=["GET", "POST"])
@login_required
def meeting_page(mid):
    """Display the meeting details page and handle location updates."""
    code = session["apartment_code"]
    m = get_meeting(code, mid)
    if not m:
        abort(404)

    doc_ref = MEET_ROOT(code).document(mid)
    if request.method == "POST" and request.form.get("form_name") == "update_location":
        formatted = request.form["formatted_address"].strip()
        lat = float(request.form["latitude"])
        lng = float(request.form["longitude"])
        doc_ref.update({
            "formatted_address": formatted,
            "latitude": lat,
            "longitude": lng
        })
        return redirect(url_for("meet_bp.meeting_page", mid=mid))

    snap = doc_ref.get()
    if not snap.exists:
        abort(404)
    m = snap.to_dict()
    m["id"] = mid
    m["start_human"] = du.isoparse(m["start_iso"]).strftime("%d %b %Y %H:%M")

    m["id"] = mid
    m["start_human"] = du.isoparse(m["start_iso"]).strftime("%d %b %Y %H:%M")
    attends = {
        "live": m.get("attending_live", []),
        "online": m.get("attending_online", []),
    }

    everyone = list_members(code)
    by_uid = {u["uid"]: u for u in everyone}

    attends["live_names"] = [by_uid[uid]["name"] for uid in attends["live"] if uid in by_uid]
    attends["online_names"] = [by_uid[uid]["name"] for uid in attends["online"] if uid in by_uid]

    chosen = set(attends["live"] + attends["online"])
    attends["undecided"] = [u["first_name"] for u in everyone if u["uid"] not in chosen]
    me_uid = session["uid"]

    topics = list_topics(code, mid)
    return render_template("meeting_detail/master.html",
                           m=m, topics=topics,
                           attends=attends,
                           me=get_user(session["uid"]),
                           me_uid=me_uid
                           )


@meet_bp.route("/meeting/<mid>/api/attend", methods=["POST"])
@login_required
def api_attend(mid):
    """Update current user's attendance preference for the meeting."""
    where = request.json.get("where")
    set_attendance(session["apartment_code"], mid, session["uid"], where)
    return jsonify(success=True)


@meet_bp.route("/meeting/<mid>/api/topic", methods=["POST", "PATCH"])
@login_required
def api_topic(mid):
    """Add or update a topic for a meeting, or record a vote."""
    code = session["apartment_code"]
    if request.method == "POST":
        t = add_topic(code, mid, session["uid"],
                      request.json["title"], request.json["body"])
        return jsonify(id=t, success=True)

    tid = request.json["tid"]
    if "delta" in request.json:
        vote_topic(code, mid, tid, session["uid"], int(request.json["delta"]))
    else:
        update_topic(code, mid, tid, request.json["update"])
    return jsonify(success=True)


@meet_bp.route("/meeting/<mid>/api/delete", methods=["POST"])
@login_required
def api_delete_mid(mid):
    """Remove a meeting and its topics if the user has permission."""
    code = session["apartment_code"]
    m = get_meeting(code, mid)

    if not m:
        abort(404)
    chair_uid = firestoreDatabase.collection("apartments").document(code).get().to_dict().get("chair_uid")

    if (session["uid"] not in (m["created_by"], chair_uid) or m["start_iso"] < datetime.datetime.utcnow().isoformat()):
        abort(403)

    print("entered 3")
    meet_ref = MEET_ROOT(code).document(mid)
    topics_ref = meet_ref.collection("topics")
    batch = firestoreDatabase.batch()
    for t in topics_ref.stream():
        batch.delete(t.reference)

    batch.delete(meet_ref)
    batch.commit()

    return jsonify(success=True)


def vote_topic(code, mid, tid, uid, delta: int):
    """Update a user's vote for a topic using delta (-1, 0 or 1)."""
    if delta not in (-1, 0, 1):
        raise ValueError("delta must be -1, 0 or 1")

    doc = MEET_ROOT(code).document(mid).collection("topics").document(tid)
    doc.update({f"votes.{uid}": delta})


@meet_bp.route("/meeting/api/new", methods=["POST"])
@login_required
def api_new_meeting():
    """Create a new meeting record and possibly a Google Meet link."""
    code = session.get("apartment_code")
    uid = session["uid"]
    data = request.json
    try:
        du.isoparse(data["start_iso"])
        if data["mode"] in ("online", "hybrid"):
            meet_link = create_google_meet(uid, data["title"], data["start_iso"], code)
            if not meet_link:
                return jsonify(error="NO_CREDS"), 401

            data["online_link"] = meet_link

        mid = create_meeting(code, session["uid"], data)
    except Exception as e:
        import traceback, sys
        traceback.print_exception(e, file=sys.stderr)
        return jsonify(error=str(e)), 400
    return jsonify(id=mid, success=True)


def save_ai_schedule(code: str, mid: str, schedule: str):
    """Persist an AI-generated schedule string for a meeting."""
    MEET_ROOT(code).document(mid).update({"ai_schedule": schedule})


@meet_bp.route("/meeting/<mid>/api/generate_schedule", methods=["POST"])
@login_required
def api_generate_schedule(mid):
    """Generate and store a suggested meeting schedule using AI."""
    code = session["apartment_code"]
    m = get_meeting(code, mid)
    if not m:
        return jsonify(error="Meeting not found"), 404

    topics = list_topics(code, mid)

    from python.ai_stuff import generate_schedule_with_gemini
    schedule = generate_schedule_with_gemini(topics, m["start_iso"])

    save_ai_schedule(code, mid, schedule)
    return jsonify(schedule=schedule)

from flask import Blueprint, render_template, session, abort, request, jsonify
from python.auth import login_required
from python.db import (
    get_meeting,
    list_members,
    MEET_ROOT,
    list_topics,
    update_topic,
    get_user,
)
import dateutil.parser as du, datetime

past_meet_bp = Blueprint("past_meet_bp", __name__, template_folder="templates")


# ───────────────────────── helpers ──────────────────────────
def _build_detail_context(code: str, m: dict) -> dict:
    """(verbatim copy from meetings.py – duplication is fine)"""
    mid = m["id"]
    dt = du.isoparse(m["start_iso"])
    m["start_human"] = dt.strftime("%d %b %Y %H:%M")

    attends = {
        "live": m.get("attending_live", []),
        "online": m.get("attending_online", [])
    }

    everyone = list_members(code)
    by_uid = {u["uid"]: u for u in everyone}

    attends["live_names"] = [by_uid[u]["name"] for u in attends["live"] if u in by_uid]
    attends["online_names"] = [by_uid[u]["name"] for u in attends["online"] if u in by_uid]
    attends["undecided"] = [u["first_name"] for u in everyone
                            if u["uid"] not in attends["live"] + attends["online"]]

    me = get_user(session["uid"])

    return dict(m=m, attends=attends, me=me, me_uid=session["uid"])


# ───────────────────────── routes ───────────────────────────
@past_meet_bp.route("/meeting/<mid>/past")
@login_required
def meeting_past_page(mid: str):
    """Render the detail page for a past meeting."""

    code = session["apartment_code"]
    m = get_meeting(code, mid)
    if not m:
        abort(404)

    ctx = _build_detail_context(code, m)
    ctx["topics"] = list_topics(code, mid)

    return render_template(
        "past_meeting_detail/master.html",
        **ctx
    )

@past_meet_bp.route("/meeting/<mid>/api/topic_update", methods=["PATCH"])
@login_required
def api_topic_update(mid):
    """Update summary or status for a meeting topic."""

    code  = session["apartment_code"]
    tid   = request.json["tid"]
    patch = {
        "summary": request.json.get("summary", ""),
        "status" : request.json.get("status", "open")
    }
    update_topic(code, mid, tid, patch)
    return jsonify(success=True)


from python.ai_stuff import generate_summary_with_gemini

def save_ai_summary(code: str, mid: str, text: str):
    """Store the AI generated summary for a meeting."""
    MEET_ROOT(code).document(mid).update({"ai_summary": text})


@past_meet_bp.route("/meeting/<mid>/api/generate_summary", methods=["POST"])
@login_required
def api_generate_summary(mid):
    """Generate and save a summary for the given meeting."""

    code = session["apartment_code"]
    m    = get_meeting(code, mid)
    if not m:
        return jsonify(error="Meeting not found"), 404

    topics = list_topics(code, mid)
    summary = generate_summary_with_gemini(topics, m["start_iso"])
    save_ai_summary(code, mid, summary)

    return jsonify(summary=summary)


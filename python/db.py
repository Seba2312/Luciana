# db.py
from datetime import datetime, timezone, timedelta
import time


from flask import session
from google.cloud import firestore

from config import firestoreDatabase, Client_secret, Client_id

DEFAULT_CUSTOMIZATION = {
    "showWhere": True,
    "showWhen": True,
    "showParticipation": True,
    "showTopics": True,
    "showVotingRight": True,
}

import random, string
from google.cloud import firestore
from config import firestoreDatabase

USERS = firestoreDatabase.collection("users")


def get_user(uid: str) -> dict | None:
    """Return the Firestore user document for *uid* or None if missing."""
    snap = USERS.document(uid).get()
    return snap.to_dict() if snap.exists else None


def create_user_if_absent(uid: str, email: str) -> None:
    """Create a new user entry if it doesn't already exist."""
    if not get_user(uid):
        variant = random.choice(["A", "B"])
        customization = DEFAULT_CUSTOMIZATION.copy()
        if variant == "B":
            customization = {k: False for k in customization}

        USERS.document(uid).set(
            {
                "uid": uid,
                "email": email,
                "first_name": None,
                "last_name": None,
                "sqm": 0,
                "role": None,
                "avatar": "emerald-500",
                "gifted_sqm": 0,
                "received_gifts": [],
                "apartment_code": None,
                "customization": customization,
                "variant": variant,
            }
        )


def update_profile(uid: str, first_name: str, last_name: str, sqm: int) -> None:
    """Fill in missing profile fields and compute the user's role."""
    role = "tenant" if sqm == 0 else "landlord"
    USERS.document(uid).set(
        {
            "first_name": first_name,
            "last_name": last_name,
            "sqm": sqm,
            "role": role,
            "total_votes": sqm
        },
        merge=True
    )


def add_apartment_to_user(uid: str, code: str) -> None:
    """Link an existing user to an apartment via its code."""
    ref = USERS.document(uid)
    ref.update({"apartment_code": code})


def update_user_settings(uid: str,
                         first_name: str,
                         last_name: str,
                         sqm: int,
                         avatar: str,
                         customization: dict | None = None) -> None:
    """Update general profile settings including optional customization."""
    update = {
        "first_name": first_name,
        "last_name": last_name,
        "sqm": sqm,
        "role": ("tenant" if sqm == 0 else "landlord"),
        "avatar": avatar,
    }
    if customization is not None:
        update["customization"] = customization
    USERS.document(uid).update(update)


def delete_user_document(uid: str) -> None:
    """Remove the Firestore user doc."""
    USERS.document(uid).delete()



SERS = firestoreDatabase.collection("users")
APTS = firestoreDatabase.collection("apartments")
METRICS = firestoreDatabase.collection("metrics")


def generate_code(k: int = 6) -> str:
    """Generate a unique random apartment code."""
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(alphabet, k=k))
        if not APTS.document(code).get().exists:
            return code


def create_apartment(code: str, chair_uid: str) -> None:
    """Fresh apartment; creator is chair + only member."""
    APTS.document(code).set({
        "chair_uid": chair_uid,
        "members": [chair_uid],
    })


def join_apartment(code: str, uid: str) -> None:
    """Add user to existing apartment (idempotent)."""
    APTS.document(code).update({
        "members": firestore.ArrayUnion([uid])
    })


def record_click(uid: str, event: str, *, duration: int | None = None, page: str | None = None, label: str | None = None) -> None:
    """Store a simple click event for analytics.

    Parameters
    ----------
    uid: str
        The user identifier.
    event: str
        Name of the event being recorded.
    duration: int | None
        Optional duration in milliseconds. Used for page visit times.
    page: str | None
        Optional page path associated with the event.
    label: str | None
        Additional label for the event (e.g. clicked element).
    """

    data = {
        "event": event,
        "ts": firestore.SERVER_TIMESTAMP,
    }
    if duration is not None:
        data["duration"] = duration
    if page is not None:
        data["page"] = page
    if label is not None:
        data["label"] = label

    METRICS.document(uid).collection("clicks").document().set(data)


def start_session(uid: str) -> str:
    """Record the start of a user session and return the session id."""
    ref = METRICS.document(uid).collection("sessions").document()
    ref.set({"start": firestore.SERVER_TIMESTAMP})
    return ref.id


def end_session(uid: str, sid: str | None) -> None:
    """Mark the end of a user session."""
    if not sid:
        return
    METRICS.document(uid).collection("sessions").document(sid).update({
        "end": firestore.SERVER_TIMESTAMP
    })


def store_questionnaire(uid: str, answers: dict) -> None:
    """Persist questionnaire answers for a user."""
    METRICS.document(uid).collection("questionnaires").document().set({
        "answers": answers,
        "ts": firestore.SERVER_TIMESTAMP,
    })


def _click_summary(uid: str) -> dict:
    """Return basic metrics aggregated from stored click events."""
    snaps = METRICS.document(uid).collection("clicks").stream()
    total = 0
    for s in snaps:
        total += 1
    return {"total_clicks": total}


def store_user_evaluation(uid: str, answers: dict) -> None:
    """Store derived evaluation comparing answers with click behaviour."""
    summary = _click_summary(uid)
    nums = [int(v) for v in answers.values() if isinstance(v, (int, str)) and str(v).isdigit()]
    avg = sum(nums) / len(nums) if nums else None
    METRICS.document(uid).collection("evaluation").document().set({
        "average_score": avg,
        "total_clicks": summary["total_clicks"],
        "ts": firestore.SERVER_TIMESTAMP,
    })


#############################################

#       Members

######################################
def list_members(code: str):
    """Return enriched user dicts for apartment *code*."""
    apt = firestoreDatabase.collection("apartments").document(code).get().to_dict()
    member_uids = apt.get("members", [])
    chair_uid = apt.get("chair_uid")

    snaps = USERS.where("uid", "in", member_uids).stream()
    out = []
    for s in snaps:
        u = s.to_dict()
        u["uid"] = s.id
        u["name"] = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip()
        u["is_chair"] = (u["uid"] == chair_uid)

        sqm = u.get("sqm") or 0
        gifted = u.get("gifted_sqm") or 0
        received_sum = sum(g.get("sqm", 0) for g in u.get("received_gifts", []))

        u["received_sum"] = received_sum
        u["total_votes"] = sqm - gifted + received_sum
        u["total_gifted"] = gifted
        u["attending"] = u.get("role") in ("tenant", "landlord")

        out.append(u)

    out.sort(key=lambda r: (not r["is_chair"], r["name"]))
    return out


def set_chair(code: str, new_uid: str) -> None:
    """Assign a new chairperson for the given apartment."""
    APTS.document(code).update({"chair_uid": new_uid})


def kick_user(code: str, uid: str) -> None:
    """Remove uid from members; if he was chair → chair field emptied."""
    ref = APTS.document(code)
    ref.update({"members": firestore.ArrayRemove([uid])})
    if ref.get().to_dict().get("chair_uid") == uid:
        ref.update({"chair_uid": None})


def recalc_votes(uid: str) -> None:
    """Recalculate and update the total voting power for a user."""
    ref = USERS.document(uid)
    data = ref.get().to_dict() or {}
    sqm = data.get("sqm", 0)
    gifted = data.get("gifted_sqm", 0)
    received = sum(g.get("sqm", 0) for g in data.get("received_gifts", []))
    total = sqm - gifted + received
    ref.update({"total_votes": total})


def gift_sqm(code: str, giver_uid: str, receiver_uid: str, sqm: int) -> None:
    """Gift voting power from one user to another within an apartment."""
    if giver_uid == receiver_uid or sqm <= 0:
        raise ValueError("invalid gift parameters")

    print("gifting check should appear twice")
    giver_ref = USERS.document(giver_uid)
    recv_ref = USERS.document(receiver_uid)

    giver = giver_ref.get().to_dict()
    remaining = giver.get("sqm", 0) - giver.get("gifted_sqm", 0)
    if remaining < sqm:
        raise ValueError("not enough m² left to gift")

    batch = firestoreDatabase.batch()
    batch.update(giver_ref, {"gifted_sqm": firestore.Increment(sqm)})

    recv = recv_ref.get().to_dict()
    gifts = recv.get("received_gifts", [])
    gifts.append({
        "from": f"{giver.get('first_name', '')} {giver.get('last_name', '')}".strip(),
        "sqm": sqm
    })
    batch.update(recv_ref, {"received_gifts": gifts})

    batch.commit()
    recalc_votes(giver_uid)
    recalc_votes(receiver_uid)


def reset_gifts_for_user(code: str, giver_uid: str) -> None:
    """Withdraw *all* gifts you have previously given."""
    giver_ref = USERS.document(giver_uid)
    giver = giver_ref.get().to_dict() or {}
    total_given = giver.get("gifted_sqm", 0)
    if total_given <= 0:
        return

    batch = firestoreDatabase.batch()
    batch.update(giver_ref, {"gifted_sqm": 0})

    from_name = f"{giver.get('first_name', '')} {giver.get('last_name', '')}".strip()
    for member in list_members(code):
        if member["uid"] == giver_uid:
            continue
        ref = USERS.document(member["uid"])
        data = ref.get().to_dict() or {}
        new_gifts = [g for g in data.get("received_gifts", [])
                     if g.get("from") != from_name]
        if len(new_gifts) != len(data.get("received_gifts", [])):
            batch.update(ref, {"received_gifts": new_gifts})

    batch.commit()
    recalc_votes(giver_uid)
    for member in list_members(code):
        recalc_votes(member["uid"])


#############################################

#       Meeting

######################################

# ───────────────────────── MEETINGS ──────────────────────────
MEET_ROOT = lambda code: APTS.document(code).collection("meetings")


def create_meeting(code: str, creator_uid: str, data: dict) -> str:
    """
    data = {"title":..., "start_iso":..., "mode":..., "location":..., "online_link":...}
    returns new meeting-id
    """
    doc = MEET_ROOT(code).document()
    doc.set({
        **data,
        "created_by": creator_uid,
        "attending_live": [creator_uid] if data["mode"] != "online" and data["mode"] != "hybrid" else [],
        "attending_online": [creator_uid] if data["mode"] != "praesenz" and data["mode"] != "hybrid" else [],
        "ai_schedule": "",
    })
    return doc.id


def list_meetings(code: str) -> list[dict]:
    """Return all meetings for an apartment sorted by start time."""
    snaps = MEET_ROOT(code).stream()
    out = []
    for s in snaps:
        x = s.to_dict()
        x["id"] = s.id
        try:
            x["topic_count"] = len(list(MEET_ROOT(code).document(s.id).collection("topics").stream()))
        except Exception:
            x["topic_count"] = 0
        out.append(x)
    out.sort(key=lambda m: m["start_iso"])
    return out


def get_meeting(code: str, mid: str) -> dict | None:
    """Fetch a single meeting document or None if it doesn't exist."""
    snap = MEET_ROOT(code).document(mid).get()
    if not snap.exists: return None
    d = snap.to_dict()
    d["id"] = mid
    d["ai_schedule"] = d.get("ai_schedule", "")
    d["ai_summary"] = d.get("ai_summary", "")

    return d


def set_attendance(code: str, mid: str, uid: str, where: str):
    """Mark whether a user attends a meeting live or online."""
    ref = MEET_ROOT(code).document(mid)

    ref.update({
        "attending_live": firestore.ArrayRemove([uid]),
        "attending_online": firestore.ArrayRemove([uid]),
    })

    if where == "live":
        ref.update({"attending_live": firestore.ArrayUnion([uid])})
    elif where == "online":
        ref.update({"attending_online": firestore.ArrayUnion([uid])})


def add_topic(code: str, mid: str, uid: str, title: str, body: str) -> str:
    """Create a new discussion topic for a meeting and return its id."""
    doc = MEET_ROOT(code).document(mid).collection("topics").document()
    doc.set({
        "title": title, "body_md": body, "votes": {uid: 1},
        "created_by": uid, "ts": firestore.SERVER_TIMESTAMP,
    })
    return doc.id


def update_topic(code, mid, tid, new_t):
    """Apply partial updates to an existing topic."""
    MEET_ROOT(code).document(mid).collection("topics").document(tid).update(new_t)


def vote_topic(code, mid, tid, uid, delta: int):
    """Record a user's vote on a topic: +1, -1 or 0 to clear."""
    if delta not in (-1, 0, 1):
        raise ValueError("delta must be -1, 0 or 1")

    doc = MEET_ROOT(code).document(mid) \
        .collection("topics").document(tid)

    doc.update({f"votes.{uid}": delta})


def list_topics(code: str, mid: str) -> list[dict]:
    """Return all topics for a meeting ordered by vote score."""
    snaps = MEET_ROOT(code).document(mid) \
        .collection("topics").stream()

    power = {u["uid"]: u["total_votes"] for u in list_members(code)}

    out = []
    for s in snaps:
        d = s.to_dict()
        d["id"] = s.id
        votes = d.get("votes", {})
        d["score"] = sum(power.get(u, 1) * v for u, v in votes.items())
        d["user_vote"] = votes.get(session.get("uid"), 0)

        out.append(d)

    out.sort(key=lambda t: -t["score"])
    return out


##########################
## meets
#######################

def save_calendar_token(uid, *, access=None, refresh=None, expires=None):
    """Persist Google Calendar API tokens for later reuse."""
    update = {}
    if access:  update["gcal_access"] = access
    if refresh: update["gcal_refresh"] = refresh
    if expires is not None:
        update["gcal_exp"] = int(expires)
    if update:
        USERS.document(uid).set(update, merge=True)


from google.oauth2.credentials import Credentials




def load_calendar_creds(uid: str):
    """Load stored Calendar credentials if they are still valid."""
    doc = USERS.document(uid).get().to_dict() or {}
    token  = doc.get("gcal_access")
    exp_ts = doc.get("gcal_exp") or 0
    if not token or time.time() >= exp_ts:
        return None

    expiry = datetime.utcfromtimestamp(exp_ts)
    return Credentials(token=token, expiry=expiry, scopes=[
        "https://www.googleapis.com/auth/calendar.events"
    ])









#############################

#Placeholder values##

################################


def bulk_create_demo_users(code: str, demo: list[dict]) -> None:
    """Insert demo users & attach them to *code* **and** add them to the
    apartment’s members array."""
    batch = firestoreDatabase.batch()
    uids = []

    for d in demo:
        uid = d["uid"]
        uids.append(uid)
        batch.set(
            USERS.document(uid),
            {
                "uid": uid,
                "email": f"{uid}@demo.local",
                "first_name": d["name"].split()[0],
                "last_name": d["name"].split()[-1],
                "sqm": d["sqm"],
                "role": ("tenant" if d["sqm"] == 0 else "landlord"),
                "avatar": "sky-500",
                "gifted_sqm": 0,
                "received_gifts": d.get("received_gifts", []),
                "is_chair": d.get("is_chair", False),
                "apartment_code": code,
                "customization": DEFAULT_CUSTOMIZATION,
            },
        )
    batch.commit()

    if uids:
        APTS.document(code).update({
            "members": firestore.ArrayUnion(uids)
        })
    for uid in uids:
        recalc_votes(uid)

def _seed_demo_meetings(code: str, creator_uid: str) -> None:
    """Create the 4 demo meetings *plus* a handful of topics for each."""
    from python.google_meets import create_google_meet

    def iso(y, m, d, h, mi):
        """Return ISO string for a UTC datetime without timezone info."""
        return datetime(y, m, d, h, mi, tzinfo=timezone.utc)\
               .replace(tzinfo=None).isoformat()

    MEET_DEFS = [
        dict(
            meta = dict(
                title="Budget",
                start_iso=iso(2025, 5, 19, 18, 45),
                mode="praesenz",
                formatted_address="Marrakesh, Morocco",
                latitude=31.6225224,
                longitude=-7.9898258,
                online_link=""
            ),
            topics = [
                ("2025 maintenance fund overview",
                 "Quick glance at incoming rent, reserve and outstanding bills."),
                ("Painting the staircase – cost split?",
                 "Get quotes from at least **three** local companies."),
            ]
        ),

        dict(
            meta = dict(
                title="Meeting near the Church",
                start_iso=iso(2025, 10, 11, 18, 46),
                mode="hybrid",
                formatted_address="Domkloster 4, 50667 Köln, Deutschland",
                latitude=50.9412784,
                longitude=6.9582814,
                online_link=create_google_meet(
                    creator_uid, "Meeting near the Church",
                    iso(2025, 5, 11, 18, 46), code) or ""
            ),
            topics = [
                ("Facade renovation timeline",
                 "Architect’s proposal & expected scaffolding period."),
                ("Roof-insulation grant",
                 "Deadline for the federal subsidy is **31 May**."),
            ]
        ),

        dict(
            meta = dict(
                title="Emergency meeting",
                start_iso=iso(2025, 5, 25, 18, 45),
                mode="online",
                formatted_address="",
                latitude="",
                longitude="",
                online_link=create_google_meet(
                    creator_uid, "Emergency meeting",
                    iso(2025, 5, 25, 18, 45), code) or ""
            ),
            topics = [
                ("Water leak in basement",
                 "Plumber’s short report & next steps."),
                ("Insurance claim procedure",
                 "Which documents do we still need?"),
                ("Temporary storage for residents",
                 "Find space for bikes & strollers while repairs happen."),
            ]
        ),

        dict(
            meta = dict(
                title="Summer BBQ planning",
                start_iso=iso(2025, 7, 29, 18, 30),
                mode="praesenz",
                formatted_address="Englischer Garten, Munich, Germany",
                latitude=48.16423229999999,
                longitude=11.6055522,
                online_link=""
            ),
            topics = [
                ("Budget & shopping list",
                 "Meat, veggie options, drinks – assign shoppers."),
                ("Clean-up rota",
                 "Volunteers for before/after the event."),
                ("homes42", "Here is the flag to open the questionnaire."),
            ]
        ),
    ]

    for m in MEET_DEFS:
        mid = create_meeting(code, creator_uid, m["meta"])
        for title, body in m["topics"]:
            add_topic(code, mid, creator_uid, title, body)
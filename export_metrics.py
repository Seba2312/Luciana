"""Export user questionnaire answers and metrics to CSV.
Requires configured Firestore via config.firestoreDatabase.
"""
import csv
import json
from pathlib import Path

from config import firestoreDatabase

USERS = firestoreDatabase.collection("users")
METRICS = firestoreDatabase.collection("metrics")


def _questionnaire_answers(uid: str) -> list[dict]:
    """Return a list of questionnaire answer dicts for the user."""
    snaps = METRICS.document(uid).collection("questionnaires").stream()
    return [s.to_dict().get("answers", {}) for s in snaps]

def _user_email(uid: str) -> str:
    """Fetch the email address of a user based on their UID."""
    doc = USERS.document(uid).get()
    return doc.to_dict().get("email", "") if doc.exists else ""

def _click_count(uid: str) -> int:
    """Return the number of recorded click events for *uid*."""
    return len(list(METRICS.document(uid).collection("clicks").stream()))

def _session_count(uid: str) -> int:
    """Return how many sessions the user has started."""
    return len(list(METRICS.document(uid).collection("sessions").stream()))


EXCLUDED_UIDS: set[str] = {f"u{i}" for i in range(1, 10)}  # u1 bis u9

def gather_data() -> list[dict]:
    """Collect metrics and questionnaire answers for all users, excluding test UIDs."""
    rows = []
    for snap in USERS.stream():
        user = snap.to_dict() or {}
        uid = user.get("uid") or snap.id

        if uid in EXCLUDED_UIDS:
            continue

        variant = user.get("variant", "A")

        answers = _questionnaire_answers(uid)
        clicks = _click_count(uid)
        sessions = _session_count(uid)

        nums = [
            int(v)
            for a in answers
            for v in a.values()
            if isinstance(v, (int, str)) and str(v).isdigit()
        ]
        avg_score = sum(nums) / len(nums) if nums else None

        rows.append(
            {
                "uid": uid,
                "email": _user_email(uid),
                "variant": variant,
                "questionnaires": json.dumps(answers, ensure_ascii=False),
                "average_score": avg_score,
                "total_clicks": clicks,
                "session_count": sessions,
            }
        )
    return rows

def export_csv(path: str = "exports/data_export.csv") -> None:
    """Export collected data to *path* as CSV."""
    data = gather_data()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "uid",
        "email",
        "variant",
        "questionnaires",
        "average_score",
        "total_clicks",
        "session_count",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Exported {len(data)} rows to {path}")

if __name__ == "__main__":
    export_csv()

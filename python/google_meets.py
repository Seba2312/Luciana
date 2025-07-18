from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import timedelta, timezone
from dateutil import parser as du

from python.db import load_calendar_creds, save_calendar_token

from python.db import list_members


def create_google_meet(uid: str, title: str, start_iso: str, apt_code: str) -> str | None:
    """Create a Google Meet link for the given meeting."""
    try:

        creds = load_calendar_creds(uid)
        if not creds:
            return None

        if creds.expired:
            return None

        if getattr(creds, "refresh_token", None) and creds.expired:
            creds.refresh(Request())
            save_calendar_token(uid, creds.token, creds.refresh_token)

        service = build("calendar", "v3", credentials=creds)

        start = du.isoparse(start_iso).astimezone(timezone.utc)
        end = start + timedelta(hours=1)

        members = list_members(apt_code)

        attendees = [{"email": m["email"]} for m in members if m.get("email")]

        body = {
            "summary": title,
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
            "attendees": "" ,
            # in a real code it would have attendees listed, but as we have placeholder data this spams the user full of email not found emails, hence removed
            "conferenceData": {
                "createRequest": {"requestId": f"meet-{int(start.timestamp())}"}
            }
        }

        event = service.events() \
            .insert(calendarId="primary",
                    conferenceDataVersion=1,
                    body=body) \
            .execute()

        for ep in event["conferenceData"]["entryPoints"]:
            if ep["entryPointType"] == "video":
                return ep["uri"]

    except Exception:
        return None

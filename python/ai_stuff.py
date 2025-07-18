import json, requests, textwrap, dateutil.parser as du

from config import gemini_api_key


def generate_schedule_with_gemini(topics: list[dict], start_time_iso: str) -> str:
    """Create a meeting agenda using the Gemini API."""

    prompt = _build_prompt(topics, start_time_iso)

    res = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-1.5-flash:generateContent",
        params={"key": gemini_api_key},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=20
    )

    data = res.json()

    if "candidates" in data:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    
    print("Gemini API error:", json.dumps(data, indent=2))
    return "⚠️ Gemini error: " + data.get("error", {}).get("message", "unknown")


def _build_prompt(topics: list[dict], start_iso: str) -> str:
    """Build the Gemini prompt for scheduling."""
    
    start = du.isoparse(start_iso)
    hour = start.hour
    start_time = start.strftime("%H:%M")

    if hour < 7 or hour >= 23:
        return f"Meeting start time {start_time} is outside normal hours (07:00–23:00). Do not generate an agenda. Explain that the time chosen is unreasonable."

    day_part = (
        "late evening" if 20 <= start.hour
        else "evening" if 18 <= start.hour
        else "afternoon" if 12 <= start.hour < 18
        else "morning"
    )

    ts = sorted(topics, key=lambda t: -t["score"])
    bullets = "\n".join(
        f"- **{t['title']}** (votes: {t['score']}): {t['body_md'][:180]}…"
        for t in ts
    )

    return textwrap.dedent(f"""
        You are a professional meeting facilitator for an owners’ meeting
        in an apartment (or housing) complex.

        • The meeting begins **{start_time}** ({day_part}).  
        • Draft a realistic agenda that fits into **4 hours or less**.  
        • Prioritize topics by vote-count: higher votes → earlier slot & more time.  
        • Read each topic’s title **and** description to gauge appropriate duration.
        • Only discuss topics that are in the topics list, never mention other topics.


        Additional rules
        ----------------
        1. Always start with **5 min Welcome & introductions**.
        2. If total runtime exceeds **1 hour**, insert **one** break:
           • If your break **overlaps any time** between **11:30–14:00**, label it 
             **“Lunch break”** (≥ 30 min).  
           • Else if runtime exceeds **2 hours**, insert **30 min** **“Coffee break”**  
             (or **“Dinner break”** if start_time is after 18:00).  
        3. End with **5 min Wrap-up & next steps**.
        4. Never schedule past **22:00** (hard cap at **23:00**). If it would,
           reply that such a schedule is implausible.
        5. Include topics with negative scores—but only a brief slot
           so they don’t overly lengthen the meeting.
        6. **Output nothing but** lines in this exact format:

               HH:MM – HH:MM  Title

        Topic list
        ----------
        {bullets}
    """).strip()



def generate_summary_with_gemini(topics: list[dict], start_iso: str) -> str:
    """Generate a concise meeting recap using Gemini."""

    t_block = "\n".join(
        f"- {t['title']}\n"
        f"  original: {t['body_md'][:200]}\n"
        f"  update  : {t.get('summary','(none)')[:200]}\n"
        f"  status  : {t.get('status','open')}"
        for t in topics
    )

    prompt = f"""
You are an assistant that writes concise meeting summaries for apartment
owner assemblies.  Create 5-8 bullet points that capture the key decisions or
open questions.  Use the word **RESOLVED** or **OPEN** in brackets after every
bullet so readers can scan quickly.

Topics with their updates
-------------------------
{t_block}

Only output the bullet list – nothing else.
""".strip()

    res = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-1.5-flash:generateContent",
        params={"key": gemini_api_key},
        json={"contents":[{"parts":[{"text":prompt}]}]},
        timeout=20
    )
    data = res.json()
    if "candidates" in data:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    print("Gemini API error:", json.dumps(data, indent=2))
    return "⚠️ Gemini error: " + data.get("error", {}).get("message", "unknown")

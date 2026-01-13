import json
from datetime import datetime
import ollama

from .schema import MeetingOutput
from .date_resolver import resolve_due_date


SYSTEM_PROMPT = """
You are an information extraction engine.
Your job: convert meeting transcript into structured JSON.

Rules:
- Output ONLY valid JSON. No markdown. No explanation.
- NEVER guess absolute dates.
- If deadlines are relative (e.g., Wednesday, tomorrow, by Friday), put it in due_date_text and keep due_date as null.
- If no deadline mentioned, both due_date_text and due_date should be null.
- priority must be one of: Low, Medium, High (never null). If unknown set Medium.
- confidence must be a number between 0 and 1 (never null). If unknown set 0.5.
- status must be one of: Backlog, To Do, In Progress, Done
- If status is not mentioned, set status = "To Do"
"""


def normalize_action_item(a: dict) -> dict:
    """Fix null / invalid values from LLM output so Pydantic won't crash."""
    if not isinstance(a, dict):
        return {}

    # Required
    if not a.get("task"):
        a["task"] = "Unknown task"

    # Owner
    if "owner" not in a:
        a["owner"] = None

    # Due fields
    if "due_date_text" not in a:
        a["due_date_text"] = None
    if "due_date" not in a:
        a["due_date"] = None

    # Priority default
    if a.get("priority") not in ["Low", "Medium", "High"]:
        a["priority"] = "Medium"

    # Confidence default + safe float
    conf = a.get("confidence", 0.5)
    try:
        conf = float(conf)
    except Exception:
        conf = 0.5

    # clamp 0..1
    conf = max(0.0, min(1.0, conf))
    a["confidence"] = conf

    # Status default
    if a.get("status") not in ["Backlog", "To Do", "In Progress", "Done"]:
        a["status"] = "To Do"

    return a


def extract_meeting_data(transcript: str) -> dict:
    user_prompt = f"""
Transcript:
{transcript}

Return JSON in this schema:
{{
  "meeting_title": string|null,
  "date": string|null,
  "summary": string,
  "decisions": [string],
  "action_items": [
    {{
      "task": string,
      "owner": string|null,
      "due_date_text": string|null,
      "due_date": null,
      "priority": "Low"|"Medium"|"High",
      "confidence": number,
      "status": "Backlog"|"To Do"|"In Progress"|"Done"
    }}
  ],
  "risks_or_blockers": [string]
}}
"""

    resp = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        options={"temperature": 0.2},
    )

    raw = resp["message"]["content"].strip()

    # Extract JSON block only
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("LLM did not return JSON output.")

    raw_json = raw[start:end + 1]
    data = json.loads(raw_json)

    # ✅ Normalize action items BEFORE Pydantic validation
    if "action_items" in data and isinstance(data["action_items"], list):
        data["action_items"] = [normalize_action_item(a) for a in data["action_items"]]

    # Validate schema using pydantic
    validated = MeetingOutput(**data)
    out = validated.model_dump()

    # Convert relative due dates
    for item in out.get("action_items", []):
        item["due_date"] = resolve_due_date(item.get("due_date_text"), datetime.now())
        if not item.get("status"):
            item["status"] = "To Do"

    return out

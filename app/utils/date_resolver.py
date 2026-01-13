from datetime import datetime, timedelta
import re

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

def next_weekday_date(target_weekday: int, base_date: datetime) -> datetime:
    days_ahead = target_weekday - base_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return base_date + timedelta(days=days_ahead)

def resolve_due_date(due_text: str, base_date: datetime | None = None) -> str | None:
    """
    Converts 'Wednesday', 'tomorrow', 'in 2 days' into ISO date.
    """
    if not due_text:
        return None

    base_date = base_date or datetime.now()
    t = due_text.strip().lower()

    if t in ["today"]:
        return base_date.strftime("%Y-%m-%d")

    if t in ["tomorrow"]:
        return (base_date + timedelta(days=1)).strftime("%Y-%m-%d")

    # "in 2 days"
    m = re.search(r"in\s+(\d+)\s+day", t)
    if m:
        n = int(m.group(1))
        return (base_date + timedelta(days=n)).strftime("%Y-%m-%d")

    # weekday name
    for day, idx in WEEKDAYS.items():
        if day in t:
            dt = next_weekday_date(idx, base_date)
            return dt.strftime("%Y-%m-%d")

    # if unknown format, keep None
    return None

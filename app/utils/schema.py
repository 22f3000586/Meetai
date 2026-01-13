from typing import List, Optional, Literal
from pydantic import BaseModel, Field

Priority = Literal["Low", "Medium", "High"]

class ActionItem(BaseModel):
    task: str
    owner: Optional[str] = None

    due_date_text: Optional[str] = None   # "Wednesday", "tomorrow", "15 Jan"
    due_date: Optional[str] = None        # converted ISO date YYYY-MM-DD

    priority: Priority = "Medium"
    confidence: float = Field(ge=0.0, le=1.0)


class MeetingOutput(BaseModel):
    meeting_title: Optional[str] = None
    date: Optional[str] = None
    summary: str
    decisions: List[str] = []
    action_items: List[ActionItem] = []
    risks_or_blockers: List[str] = []

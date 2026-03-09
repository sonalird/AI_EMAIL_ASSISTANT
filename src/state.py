from pydantic import BaseModel
from typing import Optional, Dict, List
from .agents.input_parser import ParsedInput

class EmailState(BaseModel):
    raw: str
    parsed: Optional[ParsedInput] = None
    intent: Optional[str] = None
    tone: Optional[str] = None
    tone_tokens: Optional[List[str]] = None
    draft_subject: Optional[str] = None
    draft_body: Optional[str] = None
    personalized_body: Optional[str] = None
    route: Optional[str] = None
    user_profile: Optional[Dict] = None
    history: List[str] = []
    user_name: Optional[str] = None
    company:  Optional[str] = None
    preferred_style: Optional[str] = None
    prior_messages: Optional[List[Dict]] = None
    conversation_summary: Optional[str] = None
    is_valid: Optional[bool] = None
    validation_report: Optional[Dict] = None
    retry_count: int = 0
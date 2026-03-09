from pydantic import BaseModel, Field
from typing import Optional, List
import json
import openai , os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class ParsedInput(BaseModel):
    raw: str
    normalized: str
    subject: Optional[str] = None
    recipient: Optional[str] = None
    requirements: Optional[str] = None  # kept for backward compatibility
    tone: Optional[str] = None
    intent: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)
    valid: bool = True
    issues: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

INPUT_PARSER_PROMPT = """
You are an Input Parsing Agent for an email assistant.

Your job:
1. Validate the user prompt, Flag unclear or missing information
2. Extract intent, recipient, tone, subject, and constraints
3. Normalize vague language into clear fields
4. for a proper email subject, if user input contains a subject line starting with "Subject:", extract the subject after "Subject:" and before any other lines like "Tone:". If no subject line is present, set subject to None.

Return ONLY valid JSON in this format:

 {{ "valid": boolean,
  "intent": string | null,
  "recipient": string | null,
  "tone": string | null,
  "subject": string | null,
  "constraints": [string],
  "raw": string,
  "errors": [string]
}}

Intent examples:
- outreach
- follow_up
- apology
- information
- reminder
- rejection

Tone examples:
- formal
- friendly
- assertive
- apologetic
- polite
- casual

If prompt is unclear or empty:
- is_valid = false
- if valid is false only then explain error briefly in "errors" field, e.g. ["missing_intent", "missing_subject"]

User prompt:
"{user_prompt}"
"""

class InputParsingAgent:

    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        # Temperature can be configured via env; default to 0.2 for controlled variability
        self.temperature = float(os.getenv("INPUT_PARSER_TEMPERATURE", "0.2"))

    def run(self, text:str) -> ParsedInput:
        logger.info("InputParsingAgent.run start")
        formatted_prompt = INPUT_PARSER_PROMPT.format(user_prompt=text)
        try:
            resp = openai.chat.completions.create(
                model="gpt-5.2",
                messages=[{"role": "user", "content": formatted_prompt}],
                temperature=getattr(self, "temperature", 0.0),
            )
            content = resp.choices[0].message.content if resp and resp.choices else ""
            data = json.loads(content) if content else {}
            logger.debug(f"Parser LLM content: {content[:200]}")
        except Exception as e:
            logger.exception("InputParsingAgent LLM or JSON error")
            return ParsedInput(
                raw=text,
                normalized=text,
                subject=None,
                recipient=None,
                requirements=None,
                tone=None,
                intent=None,
                constraints=[],
                valid=False,
                issues=["parse_error"],
                errors=[str(e)]
            )
        parsed = ParsedInput(
            raw=text,
            normalized=text,
            subject=data.get("subject"),
            recipient=data.get("recipient"),
            requirements=None,
            tone=data.get("tone"),
            intent=data.get("intent"),
            constraints=data.get("constraints", []) or [],
            valid=bool(data.get("valid", True)),
            issues=[],
            errors=[]
        )
        logger.info("InputParsingAgent.run success")
        return parsed
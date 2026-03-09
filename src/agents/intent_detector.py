from unittest import result
from pydantic import BaseModel
from typing import Optional
import json
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import PromptTemplate
import openai , os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class Intent(BaseModel):
    intent: str
    confidence: float
    reason: Optional[str] = None


INTENT_DETECTION_PROMPT = """
You are an Intent Detection Agent for an email assistant.

Classify the user's primary email intent using ONLY the allowed list below:

Allowed intents:
- outreach
- follow_up
- apology
- information
- reminder
- thank_you
- rejection
- confirmation
- reschedule
- general

Rules:
- Choose ONE primary intent only
- If multiple intents exist, pick the dominant one
- If unclear, use "general"
- Do NOT invent new intent labels

Return ONLY valid JSON:

{{  "intent": "<one allowed intent>",
  "confidence": <number between 0 and 1>,
  "reason": "<short explanation>"
}}

User prompt:
"{raw_prompt}"

Respond with ONLY the intent label.
"""


class IntentDetectionAgent:

    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        # Temperature can be configured via env; default to 0.2 for controlled variability
        self.temperature = float(os.getenv("INPUT_PARSER_TEMPERATURE", "0.2"))

    def run(self, state: str) -> Intent:
        logger.info("IntentDetectionAgent.run start")
        prompt = INTENT_DETECTION_PROMPT.format(raw_prompt=state)
        try:
            response = openai.chat.completions.create(
                model="gpt-5.2",
                messages=[{"role": "user", "content": prompt}],
                temperature=getattr(self, "temperature", 0.0),
            )
            content = response.choices[0].message.content if response and response.choices else ""
            data = json.loads(content) if content else {}
            intent = str(data.get("intent", "general")).strip()
            confidence = float(data.get("confidence", 0.5))
            reason = data.get("reason")
            logger.debug(f"Intent LLM content: {content[:200]}")
        except Exception:
            logger.exception("IntentDetectionAgent error")
            intent = "general"
            confidence = 0.5
            reason = None
        logger.info("IntentDetectionAgent.run success")
        return Intent(intent=intent, confidence=confidence, reason=reason)
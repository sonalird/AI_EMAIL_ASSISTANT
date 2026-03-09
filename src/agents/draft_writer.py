from pydantic import BaseModel
from typing import Optional
import json
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import PromptTemplate
import openai , os
from src.state import EmailState
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class Draft(BaseModel):
    subject: Optional[str]
    body: str

TONE_TEMPLATES = {
    "formal": {
        "opening": "I hope this message finds you well.",
        "closing": "Thank you for your time and consideration."
    },
    "casual": {
        "opening": "Hope you're doing well!",
        "closing": "Thanks so much!"
    },
    "assertive": {
        "opening": "I am writing to follow up on this matter.",
        "closing": "I look forward to your response."
    }
}

DRAFT_WRITER_PROMPT = """
You are a Draft Writer Agent for an email assistant.

Write a clear, well-structured email body.

Context:
- Intent: {intent}
- Tone: {tone}
- Recipient: {recipient}

Constraints:
{constraints}

User request:
"{raw_prompt}"

Rules:
- An appropriate subject line
- A proper greeting
- Well-structured body paragraphs
- Maintain the requested tone throughout
-A professional closing

Respond in JSON:
{{
    "subject": "...",
    "body": "..."
}}
"""

class DraftWriterAgent:

    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        # Temperature can be configured via env; default to 0.2 for controlled variability
        self.temperature = float(os.getenv("INPUT_PARSER_TEMPERATURE", "0.2"))

    def draft_writer_agent(self,state:EmailState) -> EmailState:
        logger.info("DraftWriterAgent.start")
        tone = state.tone or "formal"
        # template = TONE_TEMPLATES.get(tone, TONE_TEMPLATES["formal"])
        try:
            prompt = DRAFT_WRITER_PROMPT.format(
                intent=state.intent,
                tone=tone,
                recipient=state.parsed.recipient if state.parsed else None,
                tone_tokens="\n".join(f"- {t}" for t in (state.tone_tokens or [])),
                # opening=template["opening"],
                # closing=template["closing"],
                constraints=", ".join(state.parsed.constraints) if state.parsed else "None",
                raw_prompt=state.parsed.normalized if state.parsed else state.raw,
            )
            logger.debug(f"Draft prompt: {prompt[:200]}")
            response = openai.chat.completions.create(
                model="gpt-5.2",
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )
            content = response.choices[0].message.content if response and response.choices else ""
            data = json.loads(content) if content else {}
        except Exception:
            logger.exception("DraftWriterAgent LLM error; using fallback body")
        logger.info("DraftWriterAgent.success")
        return Draft(
            subject=data.get("subject") if isinstance(data, dict) else None,
            body=data.get("body") if isinstance(data, dict) else "",
        )
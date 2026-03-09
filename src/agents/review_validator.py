from pydantic import BaseModel
import json
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import PromptTemplate
import openai , os
from src.state import EmailState
from dotenv import load_dotenv
load_dotenv()
import logging

logger = logging.getLogger(__name__)

class Review(BaseModel):
    approved: bool
    issues: list[str]

REVIEW_VALIDATOR_PROMPT = """
You are a Review & Validator Agent for an email assistant.

Your job:
1. Review the email for grammar, clarity, and tone alignment
2. Ensure it is coherent with the intent and conversation context
3. Make minimal edits only when necessary

Context:
- Intent: {intent}
- Required tone: {tone}
- Tone rules:
{tone_tokens}

Conversation context:
{conversation_summary}

Original user request:
"{raw_prompt}"

Draft email:
\"\"\"
{draft_email}
\"\"\"

Rules:
- Preserve the original meaning
- Do NOT add new information
- Do NOT change intent
- If content conflicts with context, fix it
- Return VALID JSON only

Output format:
{{
  "is_valid": true | false,
  "final_email": "<revised email body>",
  "issues": ["<issue1>", "<issue2>"]
}}
"""


class ReviewValidatorAgent:

    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
         # Temperature can be configured via env; default to 0.2 for controlled variability
        self.temperature = float(os.getenv("INPUT_PARSER_TEMPERATURE", "0.2"))

    def review_validator_agent(self, state: EmailState) -> EmailState:
        logger.info("ReviewValidatorAgent.start")
        try:
            prompt = REVIEW_VALIDATOR_PROMPT.format(
                intent=state.intent or "general",
                tone=state.tone or "formal",
                tone_tokens="\n".join(f"- {t}" for t in (state.tone_tokens or [])),
                conversation_summary=state.conversation_summary or "None",
                raw_prompt=state.raw or "",
                draft_email=state.draft_body or "",
            )
            response = openai.chat.completions.create(
                model="gpt-5.2",
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )
            content = response.choices[0].message.content
            result = json.loads(content)
            state.is_valid = result.get("is_valid")
            state.draft_body = result.get("final_email", "")
            state.validation_report = {"issues": result.get("issues", [])}
            logger.info("ReviewValidatorAgent.success")
        except json.JSONDecodeError:
            logger.exception("Validator returned invalid JSON")
            state.is_valid = False
            state.validation_report = {"issues": ["Validator returned invalid JSON"]}
        except Exception:
            logger.exception("ReviewValidatorAgent LLM error")
            state.is_valid = False
            state.validation_report = {"issues": ["LLM error in review"]}
        return state
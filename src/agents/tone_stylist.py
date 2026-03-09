from pydantic import BaseModel
import logging

from src.state import EmailState
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import PromptTemplate
import openai , os
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class Tone(BaseModel):
    tone: str
    tone_tokens: list[str]

SUPPORTED_TONES = ["formal", "casual", "assertive"]

TONE_TOKENS = {
    "formal": [
        "use professional and respectful language",
        "avoid contractions",
        "maintain structured sentences",
        "neutral and objective phrasing"
    ],
    "casual": [
        "friendly and conversational tone",
        "use contractions naturally",
        "simple and relaxed phrasing",
        "warm closing"
    ],
    "assertive": [
        "confident and direct language",
        "clear requests or statements",
        "avoid hedging or vague phrases",
        "decisive closing"
    ]
}


INTENT_TO_TONE = {
    "outreach": "formal",
    "follow_up": "formal",
    "apology": "formal",
    "information": "formal",
    "reminder": "assertive",
    "thank_you": "casual",
    "rejection": "formal",
    "confirmation": "formal",
    "reschedule": "formal",
    "general": "formal"
}


TONE_CLASSIFICATION_PROMPT = """
You are a Tone Stylist Agent.

Classify the requested writing tone into EXACTLY ONE
of the following options:

- formal
- casual
- assertive

Rules:
- Return ONE word only
- No explanations
- If unclear or mixed, choose "formal"

User tone request:
- formal
- casual
- assertive

Rules:
- Return ONE word only
- No explanations
- If unclear or mixed, choose "formal"

User tone request:
"{tone_request}"
"""

class ToneStylistAgent:

    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
         # Temperature can be configured via env; default to 0.2 for controlled variability
        self.temperature = float(os.getenv("INPUT_PARSER_TEMPERATURE", "0.2"))

    def tone_stylist_agent(self,state: EmailState):
        logger.info("ToneStylistAgent.start")
        try:
            prompt = TONE_CLASSIFICATION_PROMPT.format(tone_request=state.tone)
            response = openai.chat.completions.create(
                model="gpt-5.2",
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )
            tone_label = response.choices[0].message.content.strip().lower()
        except Exception:
            logger.exception("ToneStylistAgent LLM error; using heuristic")
            tone_label = INTENT_TO_TONE.get(state.intent or "general", "formal")
        if tone_label not in SUPPORTED_TONES:
            tone_label = "formal"
        logger.info("ToneStylistAgent.success")
        return Tone(tone=tone_label, tone_tokens=TONE_TOKENS.get(tone_label, []))

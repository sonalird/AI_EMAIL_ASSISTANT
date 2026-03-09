from src.state import EmailState
import openai , os
import json
from dotenv import load_dotenv
load_dotenv()
from src.storage.personalization_store import (
    load_user_profile,
    load_recent_messages
)
PERSONALIZATION_PROMPT = """Personalize this email draft with relevant details.

{personalization_context}

Current draft:
Subject: {subject_line}
Body: {draft_body}

Add personalization where appropriate:
- Use recipient's name if known
- Reference user's role/company if relevant
- Add specific details from user profile
- Reference prior conversations if applicable

Keep the same structure and tone. Only enhance with personal touches.

Respond in JSON:
{{
   "subject": "...",
    "body": "..."
}}"""

class PersonalizationAgent:
    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        # Temperature can be configured via env; default to 0.2 for controlled variability
        self.temperature = float(os.getenv("INPUT_PARSER_TEMPERATURE", "0.2"))

    def personalization_agent(self,state: EmailState) -> EmailState:
        profile = load_user_profile()
        prior_messages = load_recent_messages(limit=4)

        state.user_profile = profile
        state.user_name = profile.get("name")
        state.company = profile.get("company")
        state.preferred_style = profile.get("preferred_style")

        state.prior_messages = prior_messages
        state.conversation_summary = self.summarize_messages(prior_messages)

        personalization_context = f"""
        User profile: {json.dumps(profile, indent=2) if profile else 'None'}
        Recipient: {state.parsed.recipient if state.parsed else 'Unknown'}
        Previous conversation: {self.summarize_messages(prior_messages)}

        """

        prompt = PERSONALIZATION_PROMPT.format(
                personalization_context=personalization_context,
                subject_line=state.draft_subject,
                draft_body=state.draft_body,
        )
        response = openai.chat.completions.create(
                model="gpt-5.2",
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )
        content = response.choices[0].message.content.strip()
        if content:
            data = json.loads(content) if content else {}
            state.draft_subject = data.get("subject", state.draft_subject)
            state.draft_body = data.get("body", state.draft_body)
        return state

    def summarize_messages(self, messages: list) -> str:
        if not messages:
            return ""
        return " | ".join(
            f"{m['role']}: {m['content']}" for m in messages
        )


    


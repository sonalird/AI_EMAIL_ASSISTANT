from pydantic import BaseModel
from src.storage.memory_store import log_draft
from src.storage.personalization_store import add_message, save_user_profile
from src.state import EmailState
import logging

logger = logging.getLogger(__name__)

class RouteDecision(BaseModel):
    next_step: str

class RoutingMemoryAgent:

    def routing_memory_agent(self,state: EmailState) -> EmailState:
        logger.info("RoutingMemoryAgent.start")
        try:
            # Initialize retry counter
            state.retry_count += 1

            # Log drafts
            if state.draft_body:
                log_draft(state.draft_body, stage="draft")

            # Store conversation memory
            if state.raw:
                add_message("user", state.raw)

            if state.draft_body:
                add_message("assistant", state.draft_body)

            # Persist profile memory if updated
            if state.user_profile:
                save_user_profile(state.user_profile)

            # Routing decision
            route = self.routing_rules(state)
            state.route = route

            if route == "fallback":
                state = self.fallback_agent(state)

            # Increment retry count if retrying
            if route == "retry_draft":
                state.retry_count += 1

            logger.info(f"RoutingMemoryAgent.route={route}")
            return state
        except Exception:
            logger.exception("RoutingMemoryAgent error")
            state.route = "error"
            return state

    def fallback_agent(self,state: EmailState) -> EmailState:
        state.draft_body = (
            "I was unable to generate a confident draft based on the "
            "current information. Please provide more details or clarify "
            "your request." + (f" Constraints noted: {state.parsed.constraints}" if state.parsed.constraints else "")
        )
        state.is_valid = False
        return state

    def routing_rules(self,state: EmailState) -> str:
            # 1️⃣ Invalid intent → fallback
            if not state.intent:
                return "fallback"

            # if state.parsed.valid is False:
            #     return "fallback"

            # 2️⃣ Validator failed → retry draft once
            if state.is_valid is False:
                if state.retry_count < 1:
                    return "retry_draft"
                return "fallback"

            # 3️⃣ Happy path
            return "complete"



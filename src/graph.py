from langgraph.graph import StateGraph,START, END
from .agents.input_parser import InputParsingAgent, ParsedInput
from .agents.intent_detector import IntentDetectionAgent
from .agents.tone_stylist import ToneStylistAgent
from .agents.draft_writer import DraftWriterAgent
from .agents.personalization import PersonalizationAgent
from .agents.review_validator import ReviewValidatorAgent
from .agents.routing_memory import RoutingMemoryAgent
from src.state import EmailState
import logging


parser = InputParsingAgent()
intentor = IntentDetectionAgent()
stylist = ToneStylistAgent()
writer = DraftWriterAgent()
personalizer = PersonalizationAgent()
reviewer = ReviewValidatorAgent()
router = RoutingMemoryAgent()

graph = StateGraph(EmailState)

logger = logging.getLogger(__name__)

# Nodes
def parse_node(state: EmailState) -> EmailState:
    logger.info("Node: parse_input start")
    parsed = parser.run(state.raw)
    new_state = state.model_copy(update={
        "parsed": parsed,
        # remove intent update to avoid multiple writers of same key
        # "intent": parsed.intent or state.intent,
        "tone": parsed.tone or state.tone,
        "history": [*state.history, "parse_input"],
    })
    logger.info("Node: parse_input end")
    return new_state


def intent_node(state: EmailState) -> EmailState:
    logger.info("Node: detect_intent start")
    intent = intentor.run(state.raw)
    new_state = state.model_copy(update={
        "intent": intent.intent,
        "history": [*state.history, "detect_intent"],
    })
    logger.info(f"Node: detect_intent end intent={new_state.intent}")
    return new_state


def tone_node(state: EmailState) -> EmailState:
    logger.info("Node: style_tone start")
    if state.tone:
        return state.model_copy(update={"history": [*state.history, "style_tone(skip)"]})
    tone = stylist.tone_stylist_agent(state)
    new_state = state.model_copy(update={
        "tone": tone.tone,
        "tone_tokens": tone.tone_tokens,
        "history": [*state.history, "style_tone"],
    })
    logger.info(f"Node: style_tone end tone={new_state.tone}")
    return new_state


def draft_node(state: EmailState) -> EmailState:
    logger.info("Node: write_draft start")
    d = writer.draft_writer_agent(state)
    new_state = state.model_copy(update={
        "draft_subject": d.subject,
        "draft_body": d.body,
        "history": [*state.history, "write_draft"],
    })
    logger.info("Node: write_draft end")
    return new_state


def personalize_node(state: EmailState) -> EmailState:
    logger.info("Node: personalize_draft start")
    new_state = personalizer.personalization_agent(state)
    new_state = new_state.model_copy(update={
        "history": [*state.history, "personalize_draft"],
    })
    logger.info("Node: personalize_draft end")
    return new_state


def review_node(state: EmailState) -> EmailState:
    logger.info("Node: validate_review start")
    new_state = reviewer.review_validator_agent(state)
    new_state = new_state.model_copy(update={"history": [*state.history, "validate_review"]})
    logger.info(f"Node: validate_review end valid={new_state.is_valid}")
    return new_state


def route_node(state: EmailState) -> EmailState:
    logger.info("Node: route_decision start")
    new_state = router.routing_memory_agent(state)
    new_state = new_state.model_copy(update={"history": [*state.history, "route_decision"]})
    logger.info(f"Node: route_decision end route={new_state.route}")
    return new_state

# Build graph
for name, fn in [
    ("parse", parse_node),
    ("detect_intent", intent_node),
    ("style_tone", tone_node),
    ("draft", draft_node),
    ("personalize", personalize_node),
    ("review", review_node),
    ("route_decision", route_node),
]:
    graph.add_node(name, fn)

graph.add_edge(START, "parse")
graph.add_edge("parse", "detect_intent")
graph.add_edge("detect_intent", "style_tone")
graph.add_edge("style_tone", "draft")
graph.add_edge("draft", "personalize")
graph.add_edge("personalize", "review")
graph.add_edge("review", "route_decision")
graph.add_edge("route_decision", END)

app = graph.compile()

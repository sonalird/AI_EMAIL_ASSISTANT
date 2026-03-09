from src.agents.input_parser import InputParsingAgent


def test_normalization_and_extraction():
    text = (
        "Subject: follow-up meeting\r\n"
        "To: alex@example.com\n\n"
        "Tone: friendly\n"
        "Constraints: concise, polite ; friendly\n"
        "Notes: include agenda items\n\n"
        "Following up on last week."
    )
    agent = InputParsingAgent()
    out = agent.run(text)
    assert out.valid
    assert out.normalized.count("\n\n") == 0  # no duplicate blank lines
    assert out.subject == "Follow-up meeting"
    assert out.recipient == "alex@example.com"
    assert out.tone in {"friendly", "professional"}
    assert "concise" in out.constraints and "polite" in out.constraints and "friendly" in out.constraints
    assert out.intent in {"follow_up", "request", "thank_you", "update", "introduction", None}


def test_fallback_subject_and_validation():
    text = "Quick update\nPlease review the report."
    out = InputParsingAgent().run(text)
    assert out.subject == "Quick update"
    assert out.valid


def test_empty_prompt_invalid():
    out = InputParsingAgent().run("   ")
    assert not out.valid
    assert "Empty prompt" in out.issues

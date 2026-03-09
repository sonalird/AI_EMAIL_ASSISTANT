from src.graph import app, EmailState


def test_graph_uses_parsed_intent_tone():
    text = (
        "Subject: Status update\n"
        "To: Sam\n"
        "Tone: formal\n"
        "Intent: update\n"
        "Constraints: concise\n"
        "We completed phase 1."
    )
    init = EmailState(raw=text)
    out = app.invoke(init)
    assert out.draft_subject is not None
    # Route should be set
    assert out.route in {"deliver", "revise"}

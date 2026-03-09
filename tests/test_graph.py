from src.graph import app, EmailState

def test_flow_runs():
    init = EmailState(raw="Subject: Test\nTo: Sam\nRequirements: friendly\nPlease help with report.")
    out = app.invoke(init)
    assert out.draft_subject is not None
    assert out.route in {"deliver", "revise"}

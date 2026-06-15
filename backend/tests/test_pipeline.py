from app.cortex_client import cortex
from app import prompts
from app.pipeline import run_pipeline

DOC = """\
# thing

install: `pip install thing==1.0`

## usage
```bash
thing run --port 9000
```
docs at https://example.com/thing
"""


def test_happy_path_no_loss():
    res = run_pipeline(DOC)
    assert res["status"] == "ok"
    assert res["verified"] is True
    assert res["loss"] is None
    assert res["retries"] == 0
    assert "thing run --port 9000" in res["markdown"]
    assert "before" in res["score"] and "after" in res["score"]


def test_blocked_on_high_severity_secret():
    res = run_pipeline(DOC + "\nAKIAIOSFODNN7EXAMPLE\n")
    assert res["status"] == "blocked"
    assert res["secrets"]["blocking"] is True


def test_allow_secrets_proceeds():
    res = run_pipeline(DOC + "\nAKIAIOSFODNN7EXAMPLE\n", opts={"allow_secrets": True})
    assert res["status"] == "ok"


def test_redact_opt_sanitises_before_llm():
    res = run_pipeline(DOC + '\nAPI_KEY = "supersecretvalue1"\n', opts={"redact": True})
    assert res["status"] == "ok"
    assert res["redacted"] is True
    assert "supersecretvalue1" not in res["markdown"]


def test_retry_then_recover():
    # stub drops the code block on the first pass, restores it on repair
    def responder(system, user):
        if "MISSING ITEMS" in user:
            return DOC  # repair: full document restored
        doc = prompts.extract_document(user)
        return doc.replace("```bash\nthing run --port 9000\n```", "")

    cortex.set_stub_responder(responder)
    res = run_pipeline(DOC)
    assert res["retries"] == 1
    assert res["verified"] is True
    assert "thing run --port 9000" in res["markdown"]


def test_residual_loss_reported_when_llm_keeps_dropping():
    def responder(system, user):
        doc = prompts.extract_document(user)
        return doc.replace("https://example.com/thing", "the docs")

    cortex.set_stub_responder(responder)
    res = run_pipeline(DOC)
    assert res["status"] == "ok"
    assert res["verified"] is False
    assert "https://example.com/thing" in res["loss"]["urls"]
    assert res["retries"] >= 1

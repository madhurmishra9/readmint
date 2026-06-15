from app.core import scoring, templates
from app import prompts


def test_list_templates_finds_yaml():
    names = templates.list_templates()
    assert "service" in names
    assert "library" in names


def test_load_service_template():
    t = templates.load("service")
    assert t["name"] == "Internal Service"
    headings = [s["heading"] for s in t["sections"]]
    assert "Runbook" in headings
    assert all("required" in s for s in t["sections"])


def test_load_missing_raises():
    import pytest
    with pytest.raises(FileNotFoundError):
        templates.load("does-not-exist")


def test_template_governance_scoring():
    t = templates.load("service")
    md = "# Svc\n\n## Overview\nx\n## Runbook\ny\n"
    s = scoring.score(md, t)
    assert s["mode"] == "template"
    assert s["breakdown"]["Overview"]["passed"]
    assert not s["breakdown"]["Deployment"]["passed"]


def test_system_prompt_includes_template_sections():
    t = templates.load("service")
    sysprompt = prompts.system_for(t)
    assert "Internal Service" in sysprompt
    assert "Runbook (required)" in sysprompt
    # base rules still present
    assert "NEVER remove or alter factual content" in sysprompt

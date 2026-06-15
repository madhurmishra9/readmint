from app.core import scoring

GOOD = """\
# Project

A short description paragraph.

## Installation
```bash
pip install x
```

## Usage
Run it.

## Configuration
Set things.

## License
MIT
"""


def test_rubric_score_range():
    s = scoring.score(GOOD)
    assert s["mode"] == "rubric"
    assert 0 <= s["score"] <= 100
    assert s["score"] > 50


def test_empty_doc_low_score():
    assert scoring.score("")["score"] < scoring.score(GOOD)["score"]


def test_install_and_usage_detected():
    b = scoring.score(GOOD)["breakdown"]
    assert b["installation"]["passed"]
    assert b["usage"]["passed"]
    assert b["license"]["passed"]


def test_template_mode():
    template = {"name": "svc", "sections": [
        {"heading": "Installation", "required": True},
        {"heading": "Runbook", "required": True},
    ]}
    s = scoring.score(GOOD, template)
    assert s["mode"] == "template"
    assert s["breakdown"]["Installation"]["passed"]
    assert not s["breakdown"]["Runbook"]["passed"]

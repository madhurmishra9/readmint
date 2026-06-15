from app.core import inventory


SAMPLE = """\
# My Project

Install with `pip install foo==1.2.3` then run it on port 8080.

```bash
foo --serve --port 8080
```

See https://example.com/docs and ![logo](https://img.example.com/l.png).
Contact ops@example.com for help.
"""


def test_extract_captures_data_atoms():
    inv = inventory.extract(SAMPLE)
    assert "foo --serve --port 8080" in inv.code_blocks
    assert "pip install foo==1.2.3" in inv.inline_code
    assert "https://example.com/docs" in inv.urls
    assert "https://img.example.com/l.png" in inv.images
    assert "ops@example.com" in inv.emails
    assert "8080" in inv.numbers


def test_identical_document_has_no_loss():
    a = inventory.extract(SAMPLE)
    b = inventory.extract(SAMPLE)
    assert not inventory.has_loss(inventory.diff(a, b))


def test_reorder_and_reword_prose_is_not_loss():
    reorganised = """\
# My Project — Overview

A friendly intro paragraph that did not exist before.

## Usage
```bash
foo --serve --port 8080
```
Run `pip install foo==1.2.3`. Docs: https://example.com/docs

## Assets
![logo](https://img.example.com/l.png)

## Contact
ops@example.com — port 8080.
"""
    before = inventory.extract(SAMPLE)
    after = inventory.extract(reorganised)
    report = inventory.diff(before, after)
    assert not inventory.has_loss(report), report


def test_dropped_code_block_is_loss():
    after = SAMPLE.replace("```bash\nfoo --serve --port 8080\n```", "")
    report = inventory.diff(inventory.extract(SAMPLE), inventory.extract(after))
    assert inventory.has_loss(report)
    assert any("foo --serve" in c for c in report["code_blocks"])


def test_dropped_url_is_loss():
    after = SAMPLE.replace("https://example.com/docs", "the docs")
    report = inventory.diff(inventory.extract(SAMPLE), inventory.extract(after))
    assert "https://example.com/docs" in report["urls"]


def test_dropped_version_number_is_loss():
    after = SAMPLE.replace("foo==1.2.3", "foo")
    report = inventory.diff(inventory.extract(SAMPLE), inventory.extract(after))
    assert inventory.has_loss(report)


def test_duplicate_count_tracked():
    before = inventory.extract("`a`\n`a`\n`a`")
    after = inventory.extract("`a`")
    report = inventory.diff(before, after)
    assert report["inline_code"].count("a") == 2


def test_code_block_trailing_whitespace_not_loss():
    # Trailing whitespace + a trailing blank line are noise; leading indentation
    # is preserved (it is semantically significant in Python et al.).
    a = "```\nx = 1   \ny = 2\n\n```"
    b = "```python\nx = 1\ny = 2\n```"
    report = inventory.diff(inventory.extract(a), inventory.extract(b))
    assert not report["code_blocks"]


def test_summarize_loss_readable():
    report = {"urls": ["https://x.com"], "code_blocks": [], "inline_code": [],
              "images": [], "numbers": [], "emails": []}
    text = inventory.summarize_loss(report)
    assert "urls" in text and "https://x.com" in text

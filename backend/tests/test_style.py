from app.core import style


def test_clean_doc_has_no_findings():
    md = "# Project\n\nA short description.\n\n## Usage\nRun it.\n"
    r = style.lint(md)
    assert r["count"] == 0
    assert r["findings"] == []


def test_wordy_phrase_detected():
    md = "# Project\n\nWe built this in order to solve a real problem.\n"
    r = style.lint(md)
    rules = {f["rule"] for f in r["findings"]}
    assert "wordy_phrase" in rules


def test_passive_voice_detected():
    md = "# Project\n\nThe request is handled by the server before it is forwarded.\n"
    r = style.lint(md)
    rules = {f["rule"] for f in r["findings"]}
    assert "passive_voice" in rules


def test_long_sentence_detected():
    words = " ".join(["word"] * 45)
    md = f"# Project\n\n{words}.\n"
    r = style.lint(md)
    rules = {f["rule"] for f in r["findings"]}
    assert "long_sentence" in rules


def test_missing_alt_text_detected():
    md = "# Project\n\n![](https://example.com/screenshot.png)\n"
    r = style.lint(md)
    rules = {f["rule"] for f in r["findings"]}
    assert "missing_alt_text" in rules


def test_trailing_whitespace_detected():
    md = "# Project\n\nSome text.   \n"
    r = style.lint(md)
    rules = {f["rule"] for f in r["findings"]}
    assert "trailing_whitespace" in rules


def test_multiple_blank_lines_detected():
    md = "# Project\n\nIntro.\n\n\n\nMore.\n"
    r = style.lint(md)
    rules = {f["rule"] for f in r["findings"]}
    assert "multiple_blank_lines" in rules


def test_code_blocks_are_excluded():
    md = "# Project\n\n```bash\n" + ("cmd " * 45).strip() + "\n```\n"
    r = style.lint(md)
    assert r["count"] == 0


def test_headings_and_lists_not_flagged_as_sentences():
    md = "# This is a fairly normal heading without punctuation\n\n- a list item.\n"
    r = style.lint(md)
    assert r["count"] == 0

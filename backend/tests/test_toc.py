from app.core import toc

DOC = """\
# Title

## Getting Started
text
## Getting Started
dup heading
### Deep Dive: Details!
more
"""


def test_few_headings_unchanged():
    md = "# T\n\n## Only One\n\ntext"
    assert toc.ensure(md) == md


def test_toc_inserted_after_title():
    out = toc.ensure(DOC)
    lines = out.splitlines()
    assert lines[0] == "# Title"
    assert "## Table of Contents" in out


def test_anchor_slugs_and_dedup():
    out = toc.ensure(DOC)
    assert "- [Getting Started](#getting-started)" in out
    assert "- [Getting Started](#getting-started-1)" in out  # duplicate


def test_punctuation_stripped_in_anchor():
    out = toc.ensure(DOC)
    assert "[Deep Dive: Details!](#deep-dive-details)" in out


def test_nested_indentation_for_h3():
    out = toc.ensure(DOC)
    assert "  - [Deep Dive: Details!]" in out  # h3 indented


def test_headings_inside_code_fence_are_ignored():
    md = (
        "# Title\n\nIntro.\n\n"
        "## Real One\ntext\n\n"
        "```markdown\n## Example Heading\n### Also Example\n```\n\n"
        "## Real Two\nmore\n\n"
        "## Real Three\nmore\n"
    )
    out = toc.ensure(md)
    # the example headings stay in the body (preserved) but are NOT listed in the ToC
    assert "- [Example Heading]" not in out
    assert "- [Also Example]" not in out
    assert "- [Real One](#real-one)" in out
    assert "- [Real Two](#real-two)" in out
    assert "- [Real Three](#real-three)" in out


def test_idempotent():
    once = toc.ensure(DOC)
    twice = toc.ensure(once)
    assert once.count("## Table of Contents") == 1
    assert twice.count("## Table of Contents") == 1

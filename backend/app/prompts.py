"""Prompts for the refine + repair + summary LLM calls.

The system prompt is deliberately **structure-only**: the model may reorganise,
retitle and tighten prose, but must never invent facts or drop content. The
deterministic verifier (``core.inventory``) is what actually enforces that — the
prompt just makes compliance likely.

The document is wrapped in explicit markers so a) the model knows exactly what to
transform and b) the stub LLM can recover it verbatim.
"""
from __future__ import annotations

from typing import Optional

DOC_OPEN = "<<<README"
DOC_CLOSE = "README>>>"

SYSTEM_BASE = """\
You are a senior technical writer refining a project README.

RULES (in priority order):
1. NEVER remove or alter factual content: code, commands, URLs, version
   numbers, file paths, configuration values, or names. Reproduce every code
   block and inline-code span byte-for-byte.
2. NEVER invent facts, features, badges, or links that are not in the source.
3. You MAY reorganise sections into a logical order, add a clear title,
   improve headings, fix grammar, and tighten wording.
4. Output GitHub-Flavored Markdown only. No preamble, no explanation, no code
   fence around the whole document — just the refined README.
"""

_TEMPLATE_CLAUSE = """\

REQUIRED STRUCTURE (org template "{name}"): shape the content to fit these
sections in this order, creating a section only if the source has content for
it; never fabricate content to fill a section:
{sections}
"""

USER = (
    "Refine the README between the markers. Return only the refined Markdown.\n\n"
    f"{DOC_OPEN}\n{{document}}\n{DOC_CLOSE}"
)


def system_for(template: Optional[dict] = None) -> str:
    """Build the system prompt, optionally appending template requirements.

    ``template`` is the parsed YAML dict from ``core.templates`` (has a ``name``
    and a ``sections`` list of ``{heading, required}``).
    """
    if not template:
        return SYSTEM_BASE
    lines = []
    for s in template.get("sections", []):
        flag = "required" if s.get("required") else "optional"
        lines.append(f"  - {s['heading']} ({flag})")
    return SYSTEM_BASE + _TEMPLATE_CLAUSE.format(
        name=template.get("name", "custom"), sections="\n".join(lines)
    )


def repair(loss_report, previous_output: str) -> str:
    """Prompt that re-feeds the model its output and the exact missing atoms."""
    from .core.inventory import summarize_loss

    missing = summarize_loss(loss_report)
    return (
        "Your previous refinement DROPPED content that must be preserved. "
        "Re-emit the FULL refined README with every missing item below restored "
        "verbatim, in a sensible place. Do not drop anything else.\n\n"
        f"MISSING ITEMS:\n{missing}\n\n"
        f"YOUR PREVIOUS OUTPUT:\n{DOC_OPEN}\n{previous_output}\n{DOC_CLOSE}"
    )


SUMMARY_SYSTEM = (
    "You summarise the difference between two versions of a README. "
    "Return 3-5 terse bullet points describing what structurally changed "
    "(reordered, retitled, added section headings, fixed formatting). "
    "Do not mention content you cannot see changed. Markdown bullets only."
)


def summary_user(before: str, after: str) -> str:
    return (
        f"BEFORE:\n{DOC_OPEN}\n{before}\n{DOC_CLOSE}\n\n"
        f"AFTER:\n{DOC_OPEN}\n{after}\n{DOC_CLOSE}"
    )


def extract_document(user_msg: str) -> str:
    """Recover the wrapped document from a user message (used by the stub LLM)."""
    start = user_msg.find(DOC_OPEN)
    end = user_msg.rfind(DOC_CLOSE)
    if start == -1 or end == -1 or end <= start:
        return user_msg
    return user_msg[start + len(DOC_OPEN):end].strip("\n")

# Prompt: core/inventory.py (the no-loss guard)

Goal: let the LLM reorganise/reword prose freely while guaranteeing no *data* is
lost.

Grounding:
- `extract(md) -> Inventory`: multiset (`Counter`) of data atoms — fenced &
  inline code, URLs, image refs, numbers/versions, emails. Code blocks are
  normalised by trailing whitespace only (leading indentation is significant).
  Prose is deliberately NOT inventoried.
- `diff(before, after) -> {category: [lost...]}` via multiset subtraction
  (dropped duplicates count).
- `has_loss(report) -> bool`; `summarize_loss(report) -> str` for repair prompts.

Test that reordering sections, retitling headings and rewriting sentences is
NOT loss, while dropping a code block / URL / version number IS.

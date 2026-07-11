// Splits a markdown document into heading-delimited sections, so the review
// UI can offer accept/reject per section instead of only a whole-doc diff.
const HEADING_RE = /^(#{1,6})\s+(.*)$/;

export function splitSections(md) {
  const lines = (md || "").split("\n");
  const sections = [];
  let current = { heading: null, level: 0, lines: [] };
  for (const line of lines) {
    const m = HEADING_RE.exec(line);
    if (m) {
      if (current.lines.length) sections.push(current);
      current = { heading: m[2].trim(), level: m[1].length, lines: [line] };
    } else {
      current.lines.push(line);
    }
  }
  if (current.lines.length) sections.push(current);
  return sections.map((s) => ({ ...s, body: s.lines.join("\n") }));
}

export function normalizeHeading(h) {
  return (h || "").trim().toLowerCase();
}

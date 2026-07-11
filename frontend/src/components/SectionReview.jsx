import React, { useEffect, useMemo, useState } from "react";
import { splitSections, normalizeHeading } from "../lib/sections.js";
import { lineDiff } from "../lib/diff.js";

// Lets a reviewer accept or reject the refined wording section-by-section
// instead of only all-or-nothing. Sections are matched before/after by
// heading text; a heading only in the refined doc is a "new section" (can be
// excluded); a heading only in the original is "removed" (can be restored).
// The merged result is reported to the parent via onChange, for Export.
export default function SectionReview({ before, after, onChange }) {
  const beforeSections = useMemo(() => splitSections(before), [before]);
  const afterSections = useMemo(() => splitSections(after), [after]);

  const beforeByHeading = useMemo(() => {
    const map = new Map();
    for (const s of beforeSections) if (s.heading) map.set(normalizeHeading(s.heading), s);
    return map;
  }, [beforeSections]);

  const afterHeadings = useMemo(
    () => new Set(afterSections.filter((s) => s.heading).map((s) => normalizeHeading(s.heading))),
    [afterSections]
  );

  const removed = useMemo(
    () => beforeSections.filter((s) => s.heading && !afterHeadings.has(normalizeHeading(s.heading))),
    [beforeSections, afterHeadings]
  );

  const [useRefined, setUseRefined] = useState(() => afterSections.map(() => true));
  const [restore, setRestore] = useState(() => removed.map(() => false));

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { setUseRefined(afterSections.map(() => true)); }, [after]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { setRestore(removed.map(() => false)); }, [before, after]);

  useEffect(() => {
    const parts = afterSections
      .map((s, i) => {
        if (useRefined[i] !== false) return s.body;
        const b = s.heading ? beforeByHeading.get(normalizeHeading(s.heading)) : null;
        return b ? b.body : null; // no original counterpart + rejected ⇒ drop the new section
      })
      .filter((body) => body !== null);
    const restoredParts = removed.filter((_, i) => restore[i]).map((s) => s.body);
    onChange([...parts, ...restoredParts].join("\n"));
    // onChange identity is expected to be stable (useCallback) in the parent.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [useRefined, restore, afterSections, removed, beforeByHeading]);

  const headedSections = afterSections.filter((s) => s.heading);
  if (headedSections.length === 0 && removed.length === 0) return null;

  return (
    <div className="card">
      <h3>Section review</h3>
      <p className="hint">
        Toggle any section back to its original wording, or exclude a newly added section. This only
        changes what you export/download here — it does not amend a PR already opened above.
      </p>
      {afterSections.map((s, i) => {
        if (!s.heading) return null;
        const b = beforeByHeading.get(normalizeHeading(s.heading));
        const checked = useRefined[i] !== false;
        const rows = !checked && b ? lineDiff(b.body, s.body).filter(([kind]) => kind !== "same") : null;
        return (
          <div key={i} className="section-row">
            <label>
              <input
                type="checkbox"
                checked={checked}
                onChange={(e) => setUseRefined((u) => u.map((v, idx) => (idx === i ? e.target.checked : v)))}
              />{" "}
              <span className="section-heading">{"#".repeat(s.level)} {s.heading}</span>{" "}
              <span className="muted">
                {checked ? "using refined wording" : b ? "kept original wording" : "excluded (new section)"}
              </span>
            </label>
            {rows && rows.length > 0 && (
              <pre className="diff section-diff">
                {rows.slice(0, 20).map(([kind, line], j) => (
                  <div key={j} className={"dl " + kind}>
                    <span className="sign">{kind === "add" ? "+" : "-"}</span>{line || " "}
                  </div>
                ))}
              </pre>
            )}
          </div>
        );
      })}
      {removed.length > 0 && (
        <div className="removed-sections">
          <h4>Removed by refinement</h4>
          {removed.map((s, i) => (
            <label key={i} className="section-row">
              <input
                type="checkbox"
                checked={!!restore[i]}
                onChange={(e) => setRestore((r) => r.map((v, idx) => (idx === i ? e.target.checked : v)))}
              />{" "}
              Restore "{s.heading}"
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

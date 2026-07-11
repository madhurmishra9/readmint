import React, { useMemo } from "react";
import { lineDiff } from "../lib/diff.js";

export default function DiffPanel({ before, after }) {
  const rows = useMemo(() => lineDiff(before || "", after || ""), [before, after]);
  return (
    <div className="card">
      <h3>Diff (original → refined)</h3>
      <pre className="diff">
        {rows.map(([kind, line], i) => (
          <div key={i} className={"dl " + kind}>
            <span className="sign">{kind === "add" ? "+" : kind === "del" ? "-" : " "}</span>
            {line || " "}
          </div>
        ))}
      </pre>
    </div>
  );
}

import React, { useMemo } from "react";

// Minimal LCS line-diff so reviewers see what moved/changed, without a heavy dep.
function lineDiff(a, b) {
  const A = a.split("\n"), B = b.split("\n");
  const n = A.length, m = B.length;
  const dp = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--)
    for (let j = m - 1; j >= 0; j--)
      dp[i][j] = A[i] === B[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  const out = [];
  let i = 0, j = 0;
  while (i < n && j < m) {
    if (A[i] === B[j]) { out.push(["same", A[i]]); i++; j++; }
    else if (dp[i + 1][j] >= dp[i][j + 1]) { out.push(["del", A[i]]); i++; }
    else { out.push(["add", B[j]]); j++; }
  }
  while (i < n) out.push(["del", A[i++]]);
  while (j < m) out.push(["add", B[j++]]);
  return out;
}

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

import React from "react";

export default function BatchPanel({ batch }) {
  if (!batch) return null;
  const { summary, results } = batch;
  return (
    <div className="card">
      <h3>Batch results</h3>
      <p className="muted">
        {summary.count} file(s) · {summary.blocked} blocked · {summary.unverified} unverified
      </p>
      <table className="batch">
        <thead>
          <tr><th>File</th><th>Status</th><th>Score Δ</th><th>Loss</th><th>Secrets</th><th>Links</th></tr>
        </thead>
        <tbody>
          {Object.entries(results).map(([name, r]) => {
            const delta = r.score ? r.score.after.score - r.score.before.score : null;
            const broken = r.links ? r.links.broken.length : 0;
            return (
              <tr key={name}>
                <td>{name}</td>
                <td className={r.status === "blocked" ? "bad" : r.verified ? "good" : "warn"}>{r.status}</td>
                <td>{delta === null ? "—" : (delta >= 0 ? "+" : "") + delta}</td>
                <td>{r.loss ? "⚠" : "✓"}</td>
                <td>{r.secrets && r.secrets.count ? `⚠ ${r.secrets.count}` : "—"}</td>
                <td>{r.links ? (broken ? `⚠ ${broken}` : "✓") : "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

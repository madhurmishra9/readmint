import React, { useEffect, useState } from "react";
import { getDashboard } from "../api.js";

function Sparkline({ trend }) {
  if (!trend || trend.length < 2) return <span className="muted">—</span>;
  const w = 80, h = 20, max = 100, step = w / (trend.length - 1);
  const points = trend.map((v, i) => `${i * step},${h - (v / max) * h}`).join(" ");
  return (
    <svg width={w} height={h} className="sparkline">
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

export default function Dashboard() {
  const [repos, setRepos] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDashboard().then(setRepos).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="banner danger">Error loading dashboard: {error}</div>;
  if (!repos) return <div className="card">Loading…</div>;
  if (repos.length === 0) {
    return <div className="card"><h3>Documentation health</h3><p className="muted">No runs recorded yet.</p></div>;
  }

  return (
    <div className="card">
      <h3>Documentation health — {repos.length} {repos.length === 1 ? "target" : "targets"}, worst first</h3>
      <table className="batch">
        <thead>
          <tr><th>Target</th><th>Latest score</th><th>Trend</th><th>Runs</th><th>Verified</th></tr>
        </thead>
        <tbody>
          {repos.map((r) => (
            <tr key={r.target}>
              <td><code>{r.target}</code></td>
              <td className={r.latest_score === null ? "warn" : r.latest_score < 60 ? "bad" : r.latest_score < 85 ? "warn" : "good"}>
                {r.latest_score === null ? "—" : r.latest_score}
              </td>
              <td><Sparkline trend={r.trend} /></td>
              <td>{r.runs}</td>
              <td>{r.verified === null ? "—" : r.verified ? "✓" : "⚠"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

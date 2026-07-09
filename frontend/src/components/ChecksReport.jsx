import React from "react";

// Renders the three optional repo-aware / advisory checks: badge staleness,
// doc-drift (README references vs. real repo tree), and version sync
// (README version claims vs. manifest files). Any of the three props may be
// null when its check wasn't requested.
export default function ChecksReport({ badges, drift, versionSync }) {
  if (!badges && !drift && !versionSync) return null;
  return (
    <>
      {badges && (
        <div className="card">
          <h3>Badges — {badges.checked} checked, {badges.stale.length} stale</h3>
          {badges.stale.length > 0 && (
            <ul className="style-findings">
              {badges.stale.map((b, i) => <li key={i}><code>{b.label}</code>: {b.reason}</li>)}
            </ul>
          )}
        </div>
      )}
      {drift && (
        <div className="card">
          <h3>Doc-drift — {drift.checked} reference(s) checked, {drift.missing.length} missing</h3>
          {drift.missing.length > 0 && (
            <ul className="style-findings">
              {drift.missing.map((p) => <li key={p}><code>{p}</code> no longer exists in the repo</li>)}
            </ul>
          )}
        </div>
      )}
      {versionSync && (
        <div className="card">
          <h3>Version sync — {versionSync.checked} claim(s) checked, {versionSync.mismatches.length} mismatched</h3>
          {versionSync.mismatches.length > 0 && (
            <ul className="style-findings">
              {versionSync.mismatches.map((m, i) => <li key={i}>{m.reason}</li>)}
            </ul>
          )}
        </div>
      )}
    </>
  );
}

import React from "react";

export default function StyleReport({ style }) {
  if (!style) return null;
  if (!style.count) {
    return <div className="card"><h3>Style lint</h3><p>No findings.</p></div>;
  }
  return (
    <div className="card">
      <h3>Style lint — {style.count} finding(s)</h3>
      <ul className="style-findings">
        {style.findings.slice(0, 30).map((f, i) => (
          <li key={i}>
            <code>{f.rule}</code>{f.line ? <span className="loc"> line {f.line}</span> : null}: {f.message}
          </li>
        ))}
      </ul>
      {style.findings.length > 30 && <p className="hint">+{style.findings.length - 30} more</p>}
    </div>
  );
}

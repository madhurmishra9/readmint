import React from "react";

export default function LossReport({ verified, loss }) {
  if (verified && !loss) {
    return <div className="banner ok">✓ Content-preservation verified — no data lost.</div>;
  }
  return (
    <div className="banner danger">
      <strong>⚠ Content loss detected</strong> — refinement not safe to ship.
      <ul>
        {Object.entries(loss || {}).map(([cat, items]) => (
          <li key={cat}><b>{cat}</b>: {items.slice(0, 5).map((i) => <code key={i}>{i}</code>)}
            {items.length > 5 ? ` +${items.length - 5} more` : ""}</li>
        ))}
      </ul>
    </div>
  );
}

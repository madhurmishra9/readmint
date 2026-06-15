import React from "react";

export default function SecretReport({ secrets }) {
  if (!secrets || secrets.count === 0) return null;
  return (
    <div className={"banner " + (secrets.blocking ? "danger" : "warn")}>
      <strong>{secrets.blocking ? "⛔ Secrets blocked egress" : "⚠ Possible secrets / PII"}</strong>
      {" "}({secrets.count} finding{secrets.count === 1 ? "" : "s"})
      <table className="secrets">
        <tbody>
          {secrets.items.map((it, i) => (
            <tr key={i} className={it.severity}>
              <td>{it.severity}</td>
              <td>{it.type}</td>
              <td><code>{it.match}</code></td>
              <td>L{it.line}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import React from "react";

export default function ScoreCard({ score }) {
  if (!score) return null;
  const { before, after } = score;
  const delta = after.score - before.score;
  return (
    <div className="card">
      <h3>Completeness score</h3>
      <div className="scores">
        <div className="bigscore">{before.score}<span>before</span></div>
        <div className="arrow">→</div>
        <div className="bigscore">{after.score}<span>after</span></div>
        <div className={"delta " + (delta >= 0 ? "up" : "down")}>{delta >= 0 ? "+" : ""}{delta}</div>
      </div>
      <table className="rubric">
        <tbody>
          {Object.entries(after.breakdown).map(([name, row]) => (
            <tr key={name}>
              <td>{row.passed ? "✓" : "✗"}</td>
              <td>{name}</td>
              <td className="weight">{row.weight}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import React, { useState } from "react";
import { exportDoc } from "../api.js";

export default function ExportBar({ markdown, disabled }) {
  const [busy, setBusy] = useState(false);

  function downloadMd() {
    const blob = new Blob([markdown], { type: "text/markdown" });
    triggerDownload(blob, "README.md");
  }

  async function exportAs(format) {
    setBusy(true);
    try {
      const data = await exportDoc(markdown, format);
      const blob = format === "html" ? new Blob([data], { type: "text/html" }) : data;
      triggerDownload(blob, `README.${format}`);
    } catch (e) {
      alert(`Export failed: ${e.message}`);
    } finally {
      setBusy(false);
    }
  }

  function triggerDownload(blob, name) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = name; a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="exportbar">
      <button disabled={disabled} onClick={downloadMd}>⬇ .md</button>
      <button disabled={disabled || busy} onClick={() => exportAs("html")}>⬇ HTML</button>
      <button disabled={disabled || busy} onClick={() => exportAs("pdf")}>⬇ PDF</button>
      {disabled && <span className="hint">acknowledge findings to enable</span>}
    </div>
  );
}

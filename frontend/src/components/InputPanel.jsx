import React, { useEffect, useState } from "react";
import { listTemplates } from "../api.js";

export default function InputPanel({ onRefine, onBatchZip, busy }) {
  const [mode, setMode] = useState("paste"); // paste | attach | zip
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [opts, setOpts] = useState({ template: "", check_links: false, summary: false, redact: false, allow_secrets: false });

  useEffect(() => { listTemplates().then(setTemplates).catch(() => {}); }, []);

  const setOpt = (k, v) => setOpts((o) => ({ ...o, [k]: v }));

  function submit() {
    const flags = {
      template: opts.template || "",
      check_links: opts.check_links,
      summary: opts.summary,
      redact: opts.redact,
      allow_secrets: opts.allow_secrets,
    };
    if (mode === "zip" && file) onBatchZip(file, flags);
    else if (mode === "attach" && file) onRefine({ file }, flags);
    else if (text.trim()) onRefine({ text }, flags);
  }

  return (
    <div className="panel">
      <div className="tabs">
        {["paste", "attach", "zip"].map((m) => (
          <button key={m} className={mode === m ? "tab active" : "tab"} onClick={() => setMode(m)}>
            {m === "paste" ? "Paste" : m === "attach" ? "Attach file" : "Zip / batch"}
          </button>
        ))}
      </div>

      {mode === "paste" && (
        <textarea value={text} onChange={(e) => setText(e.target.value)}
          placeholder="# Paste your README here…" rows={16} />
      )}
      {mode !== "paste" && (
        <input type="file" accept={mode === "zip" ? ".zip" : ".md,.markdown"}
          onChange={(e) => setFile(e.target.files[0])} />
      )}

      <div className="options">
        <label>Template
          <select value={opts.template} onChange={(e) => setOpt("template", e.target.value)}>
            <option value="">— default rubric —</option>
            {templates.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </label>
        {mode !== "zip" && (
          <label><input type="checkbox" checked={opts.summary}
            onChange={(e) => setOpt("summary", e.target.checked)} /> Change summary</label>
        )}
        <label><input type="checkbox" checked={opts.check_links}
          onChange={(e) => setOpt("check_links", e.target.checked)} /> Check links</label>
        <label><input type="checkbox" checked={opts.redact}
          onChange={(e) => setOpt("redact", e.target.checked)} /> Redact secrets</label>
        <label><input type="checkbox" checked={opts.allow_secrets}
          onChange={(e) => setOpt("allow_secrets", e.target.checked)} /> Allow secrets</label>
      </div>

      <button className="primary" disabled={busy} onClick={submit}>
        {busy ? "Refining…" : mode === "zip" ? "Refine batch" : "Refine"}
      </button>
    </div>
  );
}

import React, { useEffect, useState } from "react";
import { listTemplates } from "../api.js";

export default function InputPanel({ onRefine, onBatchZip, onGithub, busy }) {
  const [mode, setMode] = useState("paste"); // paste | attach | zip | github
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [opts, setOpts] = useState({ template: "", check_links: false, summary: false, redact: false, allow_secrets: false });
  const [gh, setGh] = useState({ pat: "", owner: "", repo: "", ref: "HEAD", base: "", open_pr: true });

  useEffect(() => { listTemplates().then(setTemplates).catch(() => {}); }, []);

  const setOpt = (k, v) => setOpts((o) => ({ ...o, [k]: v }));
  const setGhField = (k, v) => setGh((g) => ({ ...g, [k]: v }));

  function submit() {
    const flags = {
      template: opts.template || "",
      check_links: opts.check_links,
      summary: opts.summary,
      redact: opts.redact,
      allow_secrets: opts.allow_secrets,
    };
    if (mode === "github") onGithub(gh, flags);
    else if (mode === "zip" && file) onBatchZip(file, flags);
    else if (mode === "attach" && file) onRefine({ file }, flags);
    else if (text.trim()) onRefine({ text }, flags);
  }

  const ghReady = gh.owner.trim() && gh.repo.trim();

  return (
    <div className="panel">
      <div className="tabs">
        {["paste", "attach", "zip", "github"].map((m) => (
          <button key={m} className={mode === m ? "tab active" : "tab"} onClick={() => setMode(m)}>
            {m === "paste" ? "Paste" : m === "attach" ? "Attach file" : m === "zip" ? "Zip / batch" : "GitHub"}
          </button>
        ))}
      </div>

      {mode === "paste" && (
        <textarea value={text} onChange={(e) => setText(e.target.value)}
          placeholder="# Paste your README here…" rows={16} />
      )}
      {(mode === "attach" || mode === "zip") && (
        <input type="file" accept={mode === "zip" ? ".zip" : ".md,.markdown"}
          onChange={(e) => setFile(e.target.files[0])} />
      )}
      {mode === "github" && (
        <div className="github-form">
          <input type="password" autoComplete="off" placeholder="GitHub Personal Access Token (repo scope)"
            value={gh.pat} onChange={(e) => setGhField("pat", e.target.value)} />
          <div className="gh-row">
            <input placeholder="owner" value={gh.owner} onChange={(e) => setGhField("owner", e.target.value)} />
            <span className="gh-sep">/</span>
            <input placeholder="repo" value={gh.repo} onChange={(e) => setGhField("repo", e.target.value)} />
          </div>
          <div className="gh-row">
            <input placeholder="ref to read (default HEAD)" value={gh.ref}
              onChange={(e) => setGhField("ref", e.target.value)} />
            <input placeholder="PR base branch (default: repo default)" value={gh.base}
              onChange={(e) => setGhField("base", e.target.value)} />
          </div>
          <label><input type="checkbox" checked={gh.open_pr}
            onChange={(e) => setGhField("open_pr", e.target.checked)} /> Commit on a new branch & open a PR</label>
          <p className="hint">Your token is sent to the Readmint backend only for this request and is never stored.</p>
        </div>
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

      <button className="primary" disabled={busy || (mode === "github" && !ghReady)} onClick={submit}>
        {busy
          ? "Refining…"
          : mode === "zip"
          ? "Refine batch"
          : mode === "github"
          ? (gh.open_pr ? "Refine & open PR" : "Fetch & refine")
          : "Refine"}
      </button>
    </div>
  );
}

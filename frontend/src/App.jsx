import React, { useCallback, useEffect, useState } from "react";
import InputPanel from "./components/InputPanel.jsx";
import ScoreCard from "./components/ScoreCard.jsx";
import LossReport from "./components/LossReport.jsx";
import SecretReport from "./components/SecretReport.jsx";
import DiffPanel from "./components/DiffPanel.jsx";
import SectionReview from "./components/SectionReview.jsx";
import StyleReport from "./components/StyleReport.jsx";
import ChecksReport from "./components/ChecksReport.jsx";
import ExportBar from "./components/ExportBar.jsx";
import BatchPanel from "./components/BatchPanel.jsx";
import Dashboard from "./components/Dashboard.jsx";
import { refineText, refineFile, batchZip, githubRefine } from "./api.js";

export default function App() {
  const [view, setView] = useState("refine"); // refine | dashboard
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [original, setOriginal] = useState("");
  const [result, setResult] = useState(null);
  const [finalMarkdown, setFinalMarkdown] = useState("");
  const [batch, setBatch] = useState(null);
  const [ack, setAck] = useState(false);

  // Section review reports the merged (possibly partially-reverted) markdown
  // here; it starts out equal to the fully-refined markdown before any edits.
  useEffect(() => { setFinalMarkdown(result ? result.markdown : ""); }, [result]);
  const handleSectionChange = useCallback((md) => setFinalMarkdown(md), []);

  async function handleRefine(source, opts) {
    setBusy(true); setError(null); setBatch(null); setResult(null); setAck(false);
    try {
      let res;
      if (source.file) {
        setOriginal(await source.file.text());
        res = await refineFile(source.file, opts);
      } else {
        setOriginal(source.text);
        res = await refineText(source.text, opts);
      }
      setResult(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleGithub(gh, opts) {
    setBusy(true); setError(null); setBatch(null); setResult(null); setAck(false); setOriginal("");
    try {
      const res = await githubRefine(gh, opts);
      setOriginal(res.original || "");
      setResult(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleBatchZip(file, opts) {
    setBusy(true); setError(null); setResult(null); setBatch(null);
    try {
      setBatch(await batchZip(file, opts));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const blocked = result && result.status === "blocked";
  const hasFindings = result && result.secrets && result.secrets.count > 0;
  const exportDisabled = blocked || (result && result.verified === false) || (hasFindings && !ack);

  return (
    <div className="app">
      <header>
        <h1>🌿 Readmint</h1>
        <span className="tagline">Refine READMEs without losing a byte.</span>
        <nav className="view-tabs">
          <button className={view === "refine" ? "tab active" : "tab"} onClick={() => setView("refine")}>Refine</button>
          <button className={view === "dashboard" ? "tab active" : "tab"} onClick={() => setView("dashboard")}>Dashboard</button>
        </nav>
      </header>

      {view === "dashboard" ? (
        <main className="layout single">
          <Dashboard />
        </main>
      ) : (
      <main className="layout">
        <section className="left">
          <InputPanel onRefine={handleRefine} onBatchZip={handleBatchZip} onGithub={handleGithub} busy={busy} />
          {error && <div className="banner danger">Error: {error}</div>}
        </section>

        <section className="right">
          {batch && <BatchPanel batch={batch} />}

          {result && (
            <>
              <SecretReport secrets={result.secrets} />
              {blocked && (
                <div className="banner danger">
                  Egress blocked on high-severity secrets. Remove them, redact, or re-run with “Allow secrets”.
                </div>
              )}
              {!blocked && (
                <>
                  <LossReport verified={result.verified} loss={result.loss} />
                  {result.summary && (
                    <div className="card"><h3>What changed</h3>
                      <pre className="summary">{result.summary}</pre></div>
                  )}
                  <ScoreCard score={result.score} />
                  {result.links && (
                    <div className="card"><h3>Links</h3>
                      <p>{result.links.checked} checked · {result.links.broken.length} broken</p>
                      <ul>{result.links.broken.map((b) => <li key={b.url}><code>{b.url}</code> → {b.status || b.error}</li>)}</ul>
                    </div>
                  )}
                  {result.pr_url && (
                    <div className="banner ok">
                      Pull request opened: <a href={result.pr_url} target="_blank" rel="noreferrer">{result.pr_url}</a>
                    </div>
                  )}
                  {result.pr_skipped_reason && (
                    <div className="banner warn">PR skipped — {result.pr_skipped_reason}.</div>
                  )}
                  <DiffPanel before={original} after={result.markdown} />
                  <SectionReview before={original} after={result.markdown} onChange={handleSectionChange} />
                  <StyleReport style={result.style} />
                  <ChecksReport badges={result.badges} drift={result.drift} versionSync={result.version_sync} />
                  {hasFindings && (
                    <label className="ack"><input type="checkbox" checked={ack}
                      onChange={(e) => setAck(e.target.checked)} /> I acknowledge the findings above</label>
                  )}
                  <ExportBar markdown={finalMarkdown} disabled={exportDisabled} />
                </>
              )}
            </>
          )}
        </section>
      </main>
      )}
    </div>
  );
}

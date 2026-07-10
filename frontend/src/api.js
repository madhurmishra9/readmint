// Thin API client for the Readmint backend.

export async function refineText(text, opts = {}) {
  const form = new FormData();
  form.append("text", text);
  for (const k of ["template", "check_links", "check_style", "check_badges", "summary", "allow_secrets", "redact", "model"]) {
    if (opts[k] !== undefined && opts[k] !== null && opts[k] !== "") form.append(k, opts[k]);
  }
  const r = await fetch("/api/refine", { method: "POST", body: form });
  if (!r.ok) throw new Error(`refine failed: ${r.status}`);
  return r.json();
}

export async function refineFile(file, opts = {}) {
  const form = new FormData();
  form.append("file", file);
  for (const k of ["template", "check_links", "check_style", "check_badges", "summary", "allow_secrets", "redact", "model"]) {
    if (opts[k] !== undefined && opts[k] !== null && opts[k] !== "") form.append(k, opts[k]);
  }
  const r = await fetch("/api/refine", { method: "POST", body: form });
  if (!r.ok) throw new Error(`refine failed: ${r.status}`);
  return r.json();
}

export async function batchZip(file, opts = {}) {
  const form = new FormData();
  form.append("file", file);
  for (const k of ["template", "check_links", "allow_secrets", "redact"]) {
    if (opts[k] !== undefined && opts[k] !== "") form.append(k, opts[k]);
  }
  const r = await fetch("/api/batch/zip", { method: "POST", body: form });
  if (!r.ok) throw new Error(`batch failed: ${r.status}`);
  return r.json();
}

export async function githubRefine({ owner, repo, ref, base, pat, open_pr }, opts = {}) {
  const body = {
    owner,
    repo,
    ref: ref || "HEAD",
    open_pr: !!open_pr,
    options: {
      template: opts.template || null,
      check_links: !!opts.check_links,
      check_style: !!opts.check_style,
      check_badges: !!opts.check_badges,
      check_drift: !!opts.check_drift,
      check_version_sync: !!opts.check_version_sync,
      summary: !!opts.summary,
      allow_secrets: !!opts.allow_secrets,
      redact: !!opts.redact,
      model: opts.model || null,
    },
  };
  if (base) body.base = base;
  if (pat) body.pat = pat;
  const r = await fetch("/api/github/refine", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    let detail = `${r.status}`;
    try { detail = (await r.json()).detail || detail; } catch { /* ignore */ }
    throw new Error(`GitHub refine failed: ${detail}`);
  }
  return r.json();
}

export async function listTemplates(docType = "") {
  const qs = docType ? `?doc_type=${encodeURIComponent(docType)}` : "";
  const r = await fetch(`/api/templates${qs}`);
  return r.ok ? r.json() : { templates: [], doc_types: [] };
}

export async function getDashboard(limit = 500) {
  const r = await fetch(`/api/dashboard?limit=${limit}`);
  return r.ok ? (await r.json()).repos : [];
}

export async function getLlmInfo() {
  const r = await fetch("/api/llm");
  return r.ok ? r.json() : { provider: "stub", models: [], selected: "" };
}

export async function exportDoc(markdown, format, title = "README") {
  const r = await fetch("/api/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ markdown, format, title }),
  });
  if (!r.ok) throw new Error(`export failed: ${r.status}`);
  return format === "html" ? r.text() : r.blob();
}

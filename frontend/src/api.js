// Thin API client for the Readmint backend.

export async function refineText(text, opts = {}) {
  const form = new FormData();
  form.append("text", text);
  for (const k of ["template", "check_links", "summary", "allow_secrets", "redact"]) {
    if (opts[k] !== undefined && opts[k] !== null && opts[k] !== "") form.append(k, opts[k]);
  }
  const r = await fetch("/api/refine", { method: "POST", body: form });
  if (!r.ok) throw new Error(`refine failed: ${r.status}`);
  return r.json();
}

export async function refineFile(file, opts = {}) {
  const form = new FormData();
  form.append("file", file);
  for (const k of ["template", "check_links", "summary", "allow_secrets", "redact"]) {
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
      summary: !!opts.summary,
      allow_secrets: !!opts.allow_secrets,
      redact: !!opts.redact,
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

export async function listTemplates() {
  const r = await fetch("/api/templates");
  return r.ok ? (await r.json()).templates : [];
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

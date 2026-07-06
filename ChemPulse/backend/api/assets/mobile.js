const $ = (id) => document.getElementById(id);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
})[char]);

async function loadSummary() {
  const pill = $("connection-pill");
  try {
    const response = await fetch("/api/mobile/summary", {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const kpis = data.kpis || {};
    $("pubs").textContent = kpis.publications ?? 0;
    $("sources").textContent = kpis.journal_sources ?? 0;
    $("scaffolds").textContent = kpis.scaffolds ?? 0;
    $("records").textContent = data.status?.last_success_records ?? 0;
    pill.textContent = data.status?.desktop_mode === "live" ? "Live database" : "Local database";
    renderPublications(data.publication_radar?.items || data.publications?.items || []);
    renderScaffolds(data.scaffolds?.items || []);
  } catch (error) {
    pill.textContent = "Offline";
    $("import-status").textContent = `Could not reach ChemPulse: ${error.message}`;
  }
}

function row(title, meta, badge) {
  return `<article class="row"><div style="flex:1"><strong>${esc(title)}</strong><span>${esc(meta)}</span></div><div class="pill">${esc(badge)}</div></article>`;
}

function renderPublications(items) {
  $("publications").innerHTML = items.length
    ? items.slice(0, 12).map((item) => row(item.title, `${item.journal || "Unknown source"} | ${item.authors || "Unknown authors"}`, item.year || item.relevance_level || "new")).join("")
    : `<p class="muted">No publications available yet.</p>`;
}

function renderScaffolds(items) {
  $("scaffold-list").innerHTML = items.length
    ? items.slice(0, 10).map((item) => row(item.name, item.journal_label || "Publication evidence", item.publication_label || "0 pubs")).join("")
    : `<p class="muted">No publication-evidenced scaffolds yet.</p>`;
}

async function importLead() {
  const source = $("lead").value.trim();
  if (!source) {
    $("import-status").textContent = "Paste a DOI or article URL first.";
    return;
  }
  $("import-status").textContent = "Importing into ChemPulse...";
  try {
    const response = await fetch("/api/publications/import", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({source})
    });
    const result = await response.json();
    if (!response.ok || result.ok === false) throw new Error(result.error || "Import failed");
    $("import-status").textContent = `Imported ${result.inserted || 0} new / ${result.updated || 0} updated.`;
    $("lead").value = "";
    await loadSummary();
  } catch (error) {
    $("import-status").textContent = `Import failed: ${error.message}`;
  }
}

$("import-button").addEventListener("click", importLead);
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/mobile/service-worker.js").catch(() => {});
loadSummary();
setInterval(loadSummary, 30000);
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
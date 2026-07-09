(() => {
  if (window.ChemPulseChemicalIntelligence) return;

  const cache = {
    topic: null,
    structure: null,
    reaction: null,
    reactionNames: null,
    mechanism: null,
    report: null,
    pricing: null,
    pricingHistory: null,
  };

  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;",
  })[char]);
  const value = (id) => document.getElementById(id)?.value || "";
  const setHtml = (id, html) => { const el = document.getElementById(id); if (el) el.innerHTML = html; };
  const setText = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };
  const loading = (message) => `<div class="cp-ci-card"><div class="cp-ci-card-title">${esc(message)}</div></div>`;
  const empty = (payload, fallback) => `<div class="cp-ci-card"><div class="cp-ci-card-meta">${esc(payload?.metadata?.empty_state_reason || fallback || "No local ChemPulse matches found.")}</div>${metadataBar(payload)}</div>`;
  const tag = (label) => `<span class="cp-ci-card-tag">${esc(label)}</span>`;
  const card = (title, body, meta = "", tags = "") => `
    <div class="cp-ci-card">
      <div class="cp-ci-card-title">${esc(title)}</div>
      ${meta ? `<div class="cp-ci-card-meta">${meta}</div>` : ""}
      <div>${body}</div>
      ${tags ? `<div class="cp-ci-card-tags">${tags}</div>` : ""}
    </div>
  `;
  const metadataBar = (payload) => {
    const metadata = payload?.metadata || {};
    const warnings = payload?.warnings || payload?.validation_errors || [];
    const freshness = metadata.freshness ? ` | ${esc(metadata.freshness)}` : "";
    const warningText = warnings.length ? `<div>${esc(warnings.join(" | "))}</div>` : "";
    return `<div class="cp-ci-meta">Updated ${esc(metadata.last_updated || "n/a")} | ${esc(metadata.source || "local")} | ${esc(metadata.record_count || 0)} records${freshness}${warningText}</div>`;
  };
  const backendOrigin = async () => {
    const normalize = (raw) => {
      const url = new URL(raw);
      if (url.hostname === "localhost") url.hostname = "127.0.0.1";
      return url.origin;
    };
    try {
      const response = await fetch("/env.json", {cache: "no-store"});
      if (response.ok) {
        const env = await response.json();
        if (env.PING) return normalize(env.PING);
        if (env.EVENT) return normalize(env.EVENT.replace(/^ws/, "http"));
      }
    } catch (_error) {}
    return window.location.origin || "http://127.0.0.1:3000";
  };

  const request = async (path, payload, method = "POST") => {
    const origin = await backendOrigin();
    const url = new URL(`${origin}${path}`);
    const options = {method, headers: {"Content-Type": "application/json"}};
    if (method === "GET") {
      Object.entries(payload || {}).forEach(([key, rawValue]) => {
        if (rawValue !== undefined && rawValue !== null && String(rawValue).trim() !== "") {
          url.searchParams.set(key, String(rawValue));
        }
      });
    } else {
      options.body = JSON.stringify(payload || {});
    }
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data?.metadata?.last_error || data?.metadata?.empty_state_reason || response.statusText);
    }
    return data;
  };

  const sketch = {atoms: [], bonds: [], selectedAtom: null, atom: "C", bond: 1, charge: 0};
  const reactionSketch = {atoms: [], bonds: [], selectedAtom: null, atom: "C", bond: 1, charge: 0};
  const reactionSlots = {substrate: [], product: [], reagent: [], catalyst: [], byproduct: [], intermediate: []};

  const activeStructureInput = () => document.querySelector(".cp-ci-mode.active")?.dataset.structureInput || "draw";
  const structurePayload = () => {
    const payload = {role: value("cp-ci-structure-role"), mode: value("cp-ci-structure-mode")};
    const inputMode = activeStructureInput();
    if (inputMode === "draw") payload.molblock = molblockFromSketch();
    if (inputMode === "smiles") payload.smiles = value("cp-ci-structure-smiles");
    if (inputMode === "molblock") payload.molblock = value("cp-ci-structure-molblock");
    payload.input_mode = inputMode;
    return payload;
  };
  const reactionPayload = () => {
    const payload = {
      reaction_name: value("cp-ci-reaction-name"),
      mechanism_hint: value("cp-ci-reaction-name"),
    };
    for (const role of Object.keys(reactionSlots)) {
      const fallback = value(`cp-ci-reaction-${role}`);
      payload[role] = [...reactionSlots[role]];
      if (fallback) payload[role].push({smiles: fallback, input_format: "smiles"});
    }
    return payload;
  };
  const pricingPayload = () => ({
    query: value("cp-ci-pricing-query"),
    quantity: value("cp-ci-pricing-quantity"),
    unit: value("cp-ci-pricing-unit"),
    region: value("cp-ci-pricing-region"),
    record_snapshot: true,
  });

  const sortTopicItems = (items) => {
    const mode = value("cp-ci-topic-sort") || "relevance";
    const sorted = [...(items || [])];
    if (mode === "year") return sorted.sort((a, b) => Number(b.year || 0) - Number(a.year || 0));
    if (mode === "title") return sorted.sort((a, b) => String(a.title || "").localeCompare(String(b.title || "")));
    return sorted.sort((a, b) => Number(b.relevance_score || 0) - Number(a.relevance_score || 0));
  };

  const renderPublications = (payload) => {
    const items = sortTopicItems(payload.items || []);
    setText("cp-ci-topic-count", `${items.length} record${items.length === 1 ? "" : "s"}`);
    if (!items.length) return empty(payload, "No local literature matched that query.");
    return items.map((item) => card(
      item.title,
      `<div>${esc((item.highlighted_snippets || [])[0] || item.abstract || "")}</div>`,
      `${esc(item.journal || "Unknown journal")} | ${esc(item.year || "n/a")} | relevance ${esc(item.relevance_score || "0.00")}`,
      (item.linked_scaffolds || []).map(tag).join(""),
    )).join("") + metadataBar(payload);
  };

  const renderStructure = (payload) => {
    const matches = payload.matches || [];
    setText("cp-ci-structure-count", `${matches.length} match${matches.length === 1 ? "" : "es"}`);
    const canonical = payload.query?.canonical_smiles
      ? card("Canonical SMILES", `<code>${esc(payload.query.canonical_smiles)}</code>`, `Input: ${esc(payload.query.input_format)} | role ${esc(payload.query.role)} | mode ${esc(payload.query.mode)}`)
      : "";
    if (payload.validation_error) {
      return canonical + card("Validation", `<div>${esc(payload.validation_error)}</div>`) + metadataBar(payload);
    }
    if (!matches.length) return canonical + empty(payload, "No structure matches were found.");
    return canonical + matches.map((item) => card(
      item.name,
      `<code>${esc(item.canonical_smiles)}</code>`,
      `${esc(item.role)} | ${esc(item.match_type)} | similarity ${esc(item.similarity)} | publications ${(item.matched_publications || []).length}`,
      (item.matched_structure_roles || []).filter(Boolean).map(tag).join(""),
    )).join("") + metadataBar(payload);
  };

  const renderReactionName = (payload) => {
    const items = payload.items || [];
    if (!items.length) return empty(payload, "No named reaction families matched that query.");
    return items.map((item) => card(
      item.name,
      `<div>Aliases: ${esc((item.aliases || []).join(", "))}</div>`,
      `${esc(item.mechanism_class || "Unknown class")} | confidence ${esc(item.confidence || "0.00")} | publications ${(item.matched_publications || []).length}`,
    )).join("") + metadataBar(payload);
  };

  const renderReaction = (payload) => {
    const candidates = payload.candidate_reactions || [];
    if (!candidates.length) return empty(payload, "No reaction candidates were ranked from the current evidence.");
    return candidates.map((item, index) => card(
      `${index + 1}. ${item.mechanism_name}`,
      `<div>${esc((item.evidence || []).join(" | "))}</div><div class="cp-ci-card-tags"><button class="cp-ci-action" data-action="mechanism" data-candidate-name="${esc(item.mechanism_name)}">Explain this mechanism</button></div>`,
      `family ${esc(item.reaction_family || item.mechanism_name)} | confidence ${esc(item.confidence || "0.00")} | score ${esc(item.evidence_score || "0.00")}`,
      (item.matched_aliases || []).map(tag).join(""),
    )).join("") + metadataBar(payload);
  };

  const renderMechanism = (payload) => {
    const steps = payload.steps || [];
    if (!steps.length) return empty(payload, "No mechanism explanation is available for the current context.");
    return card(
      payload.selected_mechanism || "Mechanism",
      `<div>${esc((payload.evidence || []).join(" | "))}</div>`,
      `confidence ${esc(payload.confidence || "0.00")} | ${(payload.warnings || []).length ? esc(payload.warnings.join(" | ")) : "direct local evidence when available"}`,
    ) + steps.map((step) => card(step.title, `<div>${esc(step.description)}</div>`, esc(step.basis || ""))).join("") + metadataBar(payload);
  };

  const renderPricing = (payload) => {
    const offers = payload.offers || [];
    const providerNotes = (payload.providers || []).map((provider) => card(
      provider.display_name,
      `<div>${esc(provider.detail)}</div>`,
      `${provider.enabled ? "Enabled" : "Disabled"} | ${esc(provider.compliance_mode)}`,
    )).join("");
    if (!offers.length) {
      return providerNotes + empty(payload, "No enabled supplier feeds returned offers for that query.");
    }
    return offers.map((offer) => card(
      `${offer.provider_display_name} · ${offer.catalog_id}`,
      `<div>${esc(offer.compound_name)} | ${esc(offer.package_size)} ${esc(offer.package_unit)} | ${esc(offer.availability)}</div><div>${esc(offer.warning || "")}</div>`,
      `${esc(offer.currency)} ${esc(offer.price)} | ${esc(offer.normalized_unit_price)} ${esc(offer.normalized_unit)} | lead time ${esc(offer.lead_time_days)} day(s)`,
      [tag(offer.compliance_status), tag(offer.region)].join(""),
    )).join("") + providerNotes + metadataBar(payload);
  };

  const renderPricingHistory = (payload) => {
    const items = payload.items || [];
    if (!items.length) return empty(payload, "No stored pricing snapshots are available for that query yet.");
    return items.map((item) => card(
      `${item.query?.normalized_query || "query"} · ${item.captured_at || "unknown time"}`,
      `<div>Best offer: ${esc(item.best_offer?.provider || "n/a")} · ${esc(item.best_offer?.normalized_unit_price || "n/a")} ${esc(item.best_offer?.normalized_unit || "")}</div><div>${esc((item.offers || []).length)} offer(s) stored in this snapshot.</div>`,
    )).join("") + metadataBar(payload);
  };

  const renderReport = (payload) => {
    const markdown = payload.markdown || "No report content was returned.";
    return `${esc(markdown)}\n\n`;
  };

  const run = async (action, sourceEvent) => {
    try {
      if (action === "topic") {
        setHtml("cp-ci-topic-results", loading("Searching local literature..."));
        const data = await request("/api/search/literature", {query: value("cp-ci-topic-query")});
        cache.topic = data;
        setHtml("cp-ci-topic-results", renderPublications(data));
        setHtml("cp-ci-topic-summary", metadataBar(data));
      } else if (action === "structure") {
        setHtml("cp-ci-structure-results", loading("Searching structures..."));
        const data = await request("/api/search/structure", structurePayload());
        cache.structure = data;
        setHtml("cp-ci-structure-results", renderStructure(data));
      } else if (action === "reaction-name") {
        setHtml("cp-ci-reaction-name-results", loading("Searching reaction-name catalog..."));
        const data = await request("/api/search/reaction-name", {query: value("cp-ci-reaction-name")});
        cache.reactionNames = data;
        setHtml("cp-ci-reaction-name-results", renderReactionName(data));
      } else if (action === "reaction") {
        setHtml("cp-ci-reaction-results", loading("Ranking reaction candidates..."));
        const data = await request("/api/search/reaction", reactionPayload());
        cache.reaction = data;
        setHtml("cp-ci-reaction-results", renderReaction(data));
      } else if (action === "mechanism") {
        const candidateName = sourceEvent?.target?.closest("[data-candidate-name]")?.dataset.candidateName || "";
        const payload = reactionPayload();
        if (candidateName) payload.reaction_name = candidateName;
        const data = await request("/api/mechanism/explain", payload);
        cache.mechanism = data;
        const html = renderMechanism(data);
        setHtml("cp-ci-mechanism-results", html);
        setHtml("cp-ci-reaction-mechanism-results", html);
        setHtml("cp-ci-mechanism-standalone-results", html);
      } else if (action === "report") {
        setText("cp-ci-report-results", "Generating markdown report...");
        const data = await request("/api/reports/reaction", reactionPayload());
        cache.report = data;
        const markdown = renderReport(data);
        ["cp-ci-report-results", "cp-ci-report-preview", "cp-ci-report-workspace", "cp-ci-mechanism-report-preview"].forEach((id) => setText(id, markdown));
        setHtml("cp-ci-report-status", metadataBar(data));
      } else if (action === "pricing-compare") {
        setHtml("cp-ci-pricing-results", loading("Comparing available pricing feeds..."));
        const data = await request("/api/pricing/compare", pricingPayload());
        cache.pricing = data;
        setHtml("cp-ci-pricing-results", renderPricing(data));
        await run("pricing-history");
      } else if (action === "pricing-history") {
        setHtml("cp-ci-pricing-history", loading("Loading stored pricing snapshots..."));
        const data = await request("/api/pricing/history", {query: value("cp-ci-pricing-query")}, "GET");
        cache.pricingHistory = data;
        setHtml("cp-ci-pricing-history", renderPricingHistory(data));
      } else if (action === "pricing-watch") {
        setHtml("cp-ci-pricing-watch-status", loading("Creating a queued price watch..."));
        const data = await request("/api/pricing/watch", {
          query: value("cp-ci-pricing-query"),
          quantity: value("cp-ci-pricing-quantity"),
          unit: value("cp-ci-pricing-unit"),
          cadence: "daily",
        });
        const item = (data.items || [])[0];
        setHtml("cp-ci-pricing-watch-status", item ? `${card(item.watch_id, `<div>${esc(item.compliance_note)}</div>`, `${esc(item.status)} | cadence ${esc(item.cadence)}`)}${metadataBar(data)}` : empty(data, "The price watch could not be created."));
      }
    } catch (error) {
      const target = {
        topic: "cp-ci-topic-results",
        structure: "cp-ci-structure-results",
        "reaction-name": "cp-ci-reaction-name-results",
        reaction: "cp-ci-reaction-results",
        mechanism: "cp-ci-mechanism-results",
        report: "cp-ci-report-results",
        "pricing-compare": "cp-ci-pricing-results",
        "pricing-history": "cp-ci-pricing-history",
        "pricing-watch": "cp-ci-pricing-watch-status",
      }[action];
      if (target) setHtml(target, `<div class="cp-ci-card"><div class="cp-ci-card-title">ChemPulse request failed</div><div>${esc(error.message)}</div></div>`);
    }
  };

  const exportTarget = async (targetId) => {
    const text = document.getElementById(targetId)?.textContent || "";
    if (!text.trim()) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch (_error) {}
  };

  document.addEventListener("click", (event) => {
    const tab = event.target.closest(".cp-ci-tab");
    if (tab) {
      document.querySelectorAll(".cp-ci-tab").forEach((item) => item.classList.remove("active"));
      document.querySelectorAll(".cp-ci-pane").forEach((item) => item.classList.remove("active"));
      tab.classList.add("active");
      document.querySelector(`[data-pane="${tab.dataset.tab}"]`)?.classList.add("active");
    }
    const action = event.target.closest("[data-action]")?.dataset.action;
    if (action) run(action, event);
    const exportId = event.target.closest("[data-export-target]")?.dataset.exportTarget;
    if (exportId) exportTarget(exportId);
    const inputMode = event.target.closest("[data-structure-input]")?.dataset.structureInput;
    if (inputMode) setStructureInputMode(inputMode);
    const atom = event.target.closest("[data-sketch-atom]")?.dataset.sketchAtom;
    if (atom) setSketchAtom(atom);
    const bond = event.target.closest("[data-sketch-bond]")?.dataset.sketchBond;
    if (bond) setSketchBond(Number(bond));
    const charge = event.target.closest("[data-sketch-charge]")?.dataset.sketchCharge;
    if (charge !== undefined) setSketchCharge(Number(charge));
    const ring = event.target.closest("[data-sketch-ring]")?.dataset.sketchRing;
    if (ring) addRing(ring);
    const sketchAction = event.target.closest("[data-sketch-action]")?.dataset.sketchAction;
    if (sketchAction === "clear") clearSketch();
    if (sketchAction === "undo") undoSketch();
    const reactionAtom = event.target.closest("[data-reaction-atom]")?.dataset.reactionAtom;
    if (reactionAtom) setReactionAtom(reactionAtom);
    const reactionBond = event.target.closest("[data-reaction-bond]")?.dataset.reactionBond;
    if (reactionBond) setReactionBond(Number(reactionBond));
    const reactionCharge = event.target.closest("[data-reaction-charge]")?.dataset.reactionCharge;
    if (reactionCharge !== undefined) setReactionCharge(Number(reactionCharge));
    const reactionRing = event.target.closest("[data-reaction-ring]")?.dataset.reactionRing;
    if (reactionRing) addReactionRing(reactionRing);
    const reactionSketchAction = event.target.closest("[data-reaction-sketch-action]")?.dataset.reactionSketchAction;
    if (reactionSketchAction === "clear") clearReactionSketch();
    if (reactionSketchAction === "undo") undoReactionSketch();
    const slot = event.target.closest("[data-reaction-slot]")?.dataset.reactionSlot;
    if (slot) addReactionSlot(slot);
  });

  document.addEventListener("change", (event) => {
    if (event.target.id === "cp-ci-topic-sort" && cache.topic) {
      setHtml("cp-ci-topic-results", renderPublications(cache.topic));
    }
  });

  function setStructureInputMode(mode) {
    document.querySelectorAll(".cp-ci-mode").forEach((item) => item.classList.toggle("active", item.dataset.structureInput === mode));
    document.querySelectorAll(".cp-ci-structure-panel").forEach((item) => item.classList.toggle("active", item.dataset.structurePanel === mode));
  }

  function setSketchAtom(atom) {
    sketch.atom = atom;
    document.querySelectorAll("[data-sketch-atom]").forEach((item) => item.classList.toggle("active", item.dataset.sketchAtom === atom));
  }

  function setSketchBond(order) {
    sketch.bond = order;
    document.querySelectorAll("[data-sketch-bond]").forEach((item) => item.classList.toggle("active", Number(item.dataset.sketchBond) === order));
  }

  function setSketchCharge(charge) {
    sketch.charge = charge;
    document.querySelectorAll("[data-sketch-charge]").forEach((item) => item.classList.toggle("active", Number(item.dataset.sketchCharge) === charge));
    if (sketch.selectedAtom !== null && sketch.atoms[sketch.selectedAtom]) {
      sketch.atoms[sketch.selectedAtom].charge = charge;
      renderSketch();
    }
  }

  function setupSketcher() {
    const svg = document.getElementById("cp-ci-sketcher");
    if (!svg) return;
    svg.addEventListener("click", (event) => {
      if (event.target.closest("[data-atom-index]")) return;
      const rect = svg.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width) * 720;
      const y = ((event.clientY - rect.top) / rect.height) * 330;
      addAtomAt(x, y);
    });
    addRing("benzene");
    setSketchAtom("C");
    setSketchBond(1);
    setSketchCharge(0);
  }

  function setupReactionSketcher() {
    const svg = document.getElementById("cp-ci-reaction-sketcher");
    if (!svg) return;
    svg.addEventListener("click", (event) => {
      if (event.target.closest("[data-reaction-atom-index]")) return;
      const rect = svg.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width) * 720;
      const y = ((event.clientY - rect.top) / rect.height) * 330;
      addReactionAtomAt(x, y);
    });
    addReactionRing("benzene");
    setReactionAtom("C");
    setReactionBond(1);
    setReactionCharge(0);
  }

  function setReactionAtom(atom) {
    reactionSketch.atom = atom;
    document.querySelectorAll("[data-reaction-atom]").forEach((item) => item.classList.toggle("active", item.dataset.reactionAtom === atom));
  }

  function setReactionBond(order) {
    reactionSketch.bond = order;
    document.querySelectorAll("[data-reaction-bond]").forEach((item) => item.classList.toggle("active", Number(item.dataset.reactionBond) === order));
  }

  function setReactionCharge(charge) {
    reactionSketch.charge = charge;
    document.querySelectorAll("[data-reaction-charge]").forEach((item) => item.classList.toggle("active", Number(item.dataset.reactionCharge) === charge));
    if (reactionSketch.selectedAtom !== null && reactionSketch.atoms[reactionSketch.selectedAtom]) {
      reactionSketch.atoms[reactionSketch.selectedAtom].charge = charge;
      renderReactionSketch();
    }
  }

  function addReactionAtomAt(x, y) {
    const newIndex = reactionSketch.atoms.length;
    reactionSketch.atoms.push({x, y, element: reactionSketch.atom, charge: reactionSketch.charge});
    if (reactionSketch.selectedAtom !== null && reactionSketch.selectedAtom !== newIndex) addReactionBond(reactionSketch.selectedAtom, newIndex, reactionSketch.bond);
    reactionSketch.selectedAtom = newIndex;
    renderReactionSketch();
  }

  function addReactionBond(a, b, order) {
    if (a === b || reactionSketch.bonds.some((bond) => (bond.a === a && bond.b === b) || (bond.a === b && bond.b === a))) return;
    reactionSketch.bonds.push({a, b, order});
  }

  function addReactionRing(type) {
    const cx = 360 + reactionSketch.atoms.length * 5;
    const cy = 165 + reactionSketch.atoms.length * 3;
    const radius = 72;
    const start = reactionSketch.atoms.length;
    for (let i = 0; i < 6; i++) {
      const angle = -Math.PI / 6 + i * Math.PI / 3;
      reactionSketch.atoms.push({x: cx + Math.cos(angle) * radius, y: cy + Math.sin(angle) * radius, element: "C", charge: 0});
    }
    for (let i = 0; i < 6; i++) {
      reactionSketch.bonds.push({a: start + i, b: start + ((i + 1) % 6), order: type === "benzene" && i % 2 === 0 ? 2 : 1});
    }
    reactionSketch.selectedAtom = start;
    renderReactionSketch();
  }

  function clearReactionSketch() {
    reactionSketch.atoms = [];
    reactionSketch.bonds = [];
    reactionSketch.selectedAtom = null;
    renderReactionSketch();
  }

  function undoReactionSketch() {
    if (reactionSketch.bonds.length) {
      reactionSketch.bonds.pop();
    } else if (reactionSketch.atoms.length) {
      const index = reactionSketch.atoms.length - 1;
      reactionSketch.atoms.pop();
      reactionSketch.bonds = reactionSketch.bonds.filter((bond) => bond.a !== index && bond.b !== index);
      reactionSketch.selectedAtom = reactionSketch.atoms.length ? reactionSketch.atoms.length - 1 : null;
    }
    renderReactionSketch();
  }

  function renderReactionSketch() {
    const svg = document.getElementById("cp-ci-reaction-sketcher");
    if (!svg) return;
    svg.innerHTML = sketchMarkup(reactionSketch, "data-reaction-atom-index");
    svg.querySelectorAll("[data-reaction-atom-index]").forEach((node) => {
      node.addEventListener("click", (event) => {
        event.stopPropagation();
        const index = Number(node.getAttribute("data-reaction-atom-index"));
        if (reactionSketch.selectedAtom !== null && reactionSketch.selectedAtom !== index) addReactionBond(reactionSketch.selectedAtom, index, reactionSketch.bond);
        reactionSketch.selectedAtom = index;
        renderReactionSketch();
      });
    });
    const molblockEl = document.getElementById("cp-ci-reaction-drawn-molblock");
    if (molblockEl) molblockEl.value = molblockFromState(reactionSketch);
    setText("cp-ci-reaction-sketch-status", `${reactionSketch.atoms.length} atoms, ${reactionSketch.bonds.length} bonds. Assign the current drawing to a reaction role.`);
  }

  function addReactionSlot(role) {
    const molblock = molblockFromState(reactionSketch);
    if (!molblock) {
      setHtml("cp-ci-reaction-slot-status", `<div class="cp-ci-card"><div>Draw a structure before assigning it to ${esc(role)}.</div></div>`);
      return;
    }
    reactionSlots[role].push({molblock, input_format: "molblock"});
    renderReactionSlots();
  }

  function renderReactionSlots() {
    const roleLabels = {substrate: "Substrates", product: "Products", reagent: "Reagents", catalyst: "Catalysts", byproduct: "By-products", intermediate: "Intermediates"};
    setHtml("cp-ci-reaction-slot-status", Object.keys(reactionSlots).map((role) => card(
      roleLabels[role],
      `${reactionSlots[role].length ? `${reactionSlots[role].length} drawn structure(s) ready for validation` : "No drawn structure assigned"}`,
    )).join(""));
  }

  function addAtomAt(x, y) {
    const newIndex = sketch.atoms.length;
    sketch.atoms.push({x, y, element: sketch.atom, charge: sketch.charge});
    if (sketch.selectedAtom !== null && sketch.selectedAtom !== newIndex) addBond(sketch.selectedAtom, newIndex, sketch.bond);
    sketch.selectedAtom = newIndex;
    renderSketch();
  }

  function addBond(a, b, order) {
    if (a === b || sketch.bonds.some((bond) => (bond.a === a && bond.b === b) || (bond.a === b && bond.b === a))) return;
    sketch.bonds.push({a, b, order});
  }

  function addRing(type) {
    const cx = 360 + sketch.atoms.length * 5;
    const cy = 165 + sketch.atoms.length * 3;
    const radius = 72;
    const start = sketch.atoms.length;
    for (let i = 0; i < 6; i++) {
      const angle = -Math.PI / 6 + i * Math.PI / 3;
      sketch.atoms.push({x: cx + Math.cos(angle) * radius, y: cy + Math.sin(angle) * radius, element: "C", charge: 0});
    }
    for (let i = 0; i < 6; i++) {
      sketch.bonds.push({a: start + i, b: start + ((i + 1) % 6), order: type === "benzene" && i % 2 === 0 ? 2 : 1});
    }
    sketch.selectedAtom = start;
    renderSketch();
  }

  function clearSketch() {
    sketch.atoms = [];
    sketch.bonds = [];
    sketch.selectedAtom = null;
    renderSketch();
  }

  function undoSketch() {
    if (sketch.bonds.length) {
      sketch.bonds.pop();
    } else if (sketch.atoms.length) {
      const index = sketch.atoms.length - 1;
      sketch.atoms.pop();
      sketch.bonds = sketch.bonds.filter((bond) => bond.a !== index && bond.b !== index);
      sketch.selectedAtom = sketch.atoms.length ? sketch.atoms.length - 1 : null;
    }
    renderSketch();
  }

  function renderSketch() {
    const svg = document.getElementById("cp-ci-sketcher");
    if (!svg) return;
    svg.innerHTML = sketchMarkup(sketch, "data-atom-index");
    svg.querySelectorAll("[data-atom-index]").forEach((node) => {
      node.addEventListener("click", (event) => {
        event.stopPropagation();
        const index = Number(node.getAttribute("data-atom-index"));
        if (sketch.selectedAtom !== null && sketch.selectedAtom !== index) addBond(sketch.selectedAtom, index, sketch.bond);
        sketch.selectedAtom = index;
        renderSketch();
      });
    });
    const molblock = molblockFromSketch();
    const molblockEl = document.getElementById("cp-ci-drawn-molblock");
    if (molblockEl) molblockEl.value = molblock;
    setText("cp-ci-sketch-status", `${sketch.atoms.length} atoms, ${sketch.bonds.length} bonds. Export format: V2000 MolBlock.`);
  }

  function sketchMarkup(state, atomAttribute) {
    const lines = [];
    for (const bond of state.bonds) {
      const a = state.atoms[bond.a];
      const b = state.atoms[bond.b];
      if (!a || !b) continue;
      const offsets = bond.order === 1 ? [0] : bond.order === 2 ? [-4, 4] : [-7, 0, 7];
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const length = Math.max(1, Math.sqrt(dx * dx + dy * dy));
      const nx = -dy / length;
      const ny = dx / length;
      for (const offset of offsets) {
        lines.push(`<line x1="${a.x + nx * offset}" y1="${a.y + ny * offset}" x2="${b.x + nx * offset}" y2="${b.y + ny * offset}" stroke="var(--cp-molecule-ink)" stroke-width="3" stroke-linecap="round"/>`);
      }
    }
    const atomMarkup = state.atoms.map((atom, index) => {
      const selected = index === state.selectedAtom;
      const label = atom.element === "C" && atom.charge === 0 ? "" : `${atom.element}${atom.charge === 1 ? "+" : atom.charge === -1 ? "-" : ""}`;
      return `<g ${atomAttribute}="${index}" style="cursor:pointer"><circle cx="${atom.x}" cy="${atom.y}" r="${selected ? 15 : 11}" fill="${selected ? "var(--cp-molecule-node-selected-fill)" : "var(--cp-molecule-node-fill)"}" stroke="${selected ? "var(--cp-molecule-node-selected-stroke)" : "var(--cp-molecule-node-stroke)"}" stroke-width="2"/><text x="${atom.x}" y="${atom.y}" fill="var(--cp-molecule-ink)" font-size="16">${label}</text></g>`;
    }).join("");
    return `${lines.join("")}${atomMarkup}`;
  }

  function molblockFromSketch() {
    return molblockFromState(sketch);
  }

  function molblockFromState(state) {
    if (!state.atoms.length) return "";
    const atomCount = state.atoms.length;
    const bondCount = state.bonds.length;
    const header = ["ChemPulse sketch", "  ChemPulse", ""];
    const counts = `${pad(atomCount, 3)}${pad(bondCount, 3)}  0  0  0  0            999 V2000`;
    const atomLines = state.atoms.map((atom) => {
      const x = ((atom.x - 360) / 80).toFixed(4);
      const y = ((165 - atom.y) / 80).toFixed(4);
      return `${padFloat(x)}${padFloat(y)}${padFloat("0.0000")} ${atom.element.padEnd(3)} 0  0  0  0  0  0  0  0  0  0  0  0`;
    });
    const bondLines = state.bonds.map((bond) => `${pad(bond.a + 1, 3)}${pad(bond.b + 1, 3)}${pad(bond.order, 3)}  0  0  0  0`);
    const chargedAtoms = state.atoms.map((atom, index) => ({atom, index})).filter((item) => item.atom.charge);
    const chargeLines = [];
    for (let i = 0; i < chargedAtoms.length; i += 8) {
      const chunk = chargedAtoms.slice(i, i + 8);
      chargeLines.push(`M  CHG${pad(chunk.length, 3)}${chunk.map((item) => `${pad(item.index + 1, 4)}${pad(item.atom.charge, 4)}`).join("")}`);
    }
    return [...header, counts, ...atomLines, ...bondLines, ...chargeLines, "M  END"].join("\n");
  }

  function pad(value, width) {
    return String(value).padStart(width, " ");
  }

  function padFloat(value) {
    return String(value).padStart(10, " ");
  }

  window.ChemPulseChemicalIntelligence = {run};
  setupSketcher();
  setupReactionSketcher();
})();
(() => {
  if (window.ChemPulseChemicalIntelligence) return;
  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"
  })[char]);
  const value = (id) => document.getElementById(id)?.value || "";
  const set = (id, html) => { const el = document.getElementById(id); if (el) el.innerHTML = html; };
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
  const post = async (path, payload) => {
    const response = await fetch(`${await backendOrigin()}${path}`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload || {})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data?.metadata?.last_error || data?.metadata?.empty_state_reason || response.statusText);
    return data;
  };
  const card = (inner) => `<div class="cp-ci-card">${inner}</div>`;
  const empty = (payload) => `<div class="cp-ci-muted">${esc(payload?.metadata?.empty_state_reason || "No local ChemPulse matches found.")}</div>`;
  const sketch = {
    atoms: [],
    bonds: [],
    selectedAtom: null,
    atom: "C",
    bond: 1,
    charge: 0
  };
  const reactionSketch = {
    atoms: [],
    bonds: [],
    selectedAtom: null,
    atom: "C",
    bond: 1,
    charge: 0
  };
  const reactionSlots = {
    substrate: [],
    product: [],
    reagent: [],
    catalyst: [],
    byproduct: [],
    intermediate: []
  };
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
      mechanism_hint: value("cp-ci-reaction-name")
    };
    for (const role of Object.keys(reactionSlots)) {
      const fallback = value(`cp-ci-reaction-${role}`);
      payload[role] = [...reactionSlots[role]];
      if (fallback) payload[role].push({smiles: fallback, input_format: "smiles"});
    }
    const catalystFallback = value("cp-ci-reaction-catalyst");
    if (catalystFallback && !payload.catalyst.some((entry) => entry.smiles === catalystFallback)) {
      payload.catalyst.push({smiles: catalystFallback, input_format: "smiles"});
    }
    return payload;
  };
  const renderPublications = (payload) => {
    const items = payload.items || [];
    if (!items.length) return empty(payload);
    return items.map((item) => card(
      `<strong style="color:#fff">${esc(item.title)}</strong><div class="cp-ci-muted">${esc(item.journal)} ${esc(item.year)} | score ${esc(item.relevance_score)}</div><div>${esc((item.highlighted_snippets || [])[0] || "")}</div><div class="cp-ci-muted">${esc((item.linked_scaffolds || []).join(", "))}</div>`
    )).join("");
  };
  const renderStructure = (payload) => {
    if (payload.validation_error) return `<div style="color:#fca5a5">${esc(payload.validation_error)}</div>`;
    const matches = payload.matches || [];
    const canonical = payload.query?.canonical_smiles ? card(`<strong style="color:#fff">Canonical SMILES</strong><div><code>${esc(payload.query.canonical_smiles)}</code></div><div class="cp-ci-muted">Input: ${esc(payload.query.input_format)} | role ${esc(payload.query.role)} | mode ${esc(payload.query.mode)}</div>`) : "";
    if (!matches.length) return canonical + empty(payload);
    return canonical + matches.map((item) => card(
      `<strong style="color:#fff">${esc(item.name)}</strong><div class="cp-ci-muted">${esc(item.role)} | ${esc(item.match_type)} | similarity ${esc(item.similarity)} | publications ${(item.matched_publications || []).length}</div><code>${esc(item.canonical_smiles)}</code><div class="cp-ci-muted">${esc((item.matched_structure_roles || []).filter(Boolean).join(" | "))}</div>`
    )).join("");
  };
  const renderReaction = (payload) => {
    const candidates = payload.candidate_reactions || [];
    const validation = (payload.validation_errors || []).length ? card(`<strong style="color:#fca5a5">Validation warnings</strong><div>${esc((payload.validation_errors || []).join(" | "))}</div>`) : "";
    if (!candidates.length) return validation + empty(payload);
    return validation + candidates.map((item, index) => card(
      `<strong style="color:#fff">${index + 1}. ${esc(item.mechanism_name)}</strong><div class="cp-ci-muted">family ${esc(item.reaction_family || item.mechanism_name)} | class ${esc(item.likely_mechanism_class || "")}</div><div class="cp-ci-muted">confidence ${esc(item.confidence)} | evidence score ${esc(item.evidence_score)}</div><div>${esc((item.evidence || []).join(" | "))}</div><div class="cp-ci-muted">aliases: ${esc((item.matched_aliases || []).join(", "))}</div><div class="cp-ci-muted">${esc((item.missing_evidence || []).join(" | "))}</div><button class="cp-ci-action" data-action="mechanism" data-candidate-name="${esc(item.mechanism_name)}">Explain this mechanism</button>`
    )).join("");
  };
  const renderReactionName = (payload) => {
    const items = payload.items || [];
    if (!items.length) return empty(payload);
    return items.map((item) => card(
      `<strong style="color:#fff">${esc(item.name)}</strong><div class="cp-ci-muted">${esc(item.mechanism_class)} | confidence ${esc(item.confidence)}</div><div>Aliases: ${esc((item.aliases || []).join(", "))}</div><div class="cp-ci-muted">publications ${(item.matched_publications || []).length}</div>`
    )).join("");
  };
  const renderMechanism = (payload) => {
    const steps = payload.steps || [];
    return card(`<strong style="color:#fff">${esc(payload.selected_mechanism)}</strong><div class="cp-ci-muted">confidence ${esc(payload.confidence)} | ${esc((payload.warnings || []).join(" | "))}</div>`) +
      steps.map((step) => card(`<strong>${esc(step.title)}</strong><div>${esc(step.description)}</div><div class="cp-ci-muted">${esc(step.basis)}</div>`)).join("");
  };
  window.ChemPulseChemicalIntelligence = {
    async run(action, sourceEvent) {
      try {
        if (action === "topic") {
          set("cp-ci-topic-results", "Searching local literature...");
          const data = await post("/api/search/literature", {query: value("cp-ci-topic-query")});
          set("cp-ci-topic-results", renderPublications(data));
        } else if (action === "structure") {
          set("cp-ci-structure-results", "Searching structures...");
          const data = await post("/api/search/structure", structurePayload());
          set("cp-ci-structure-results", renderStructure(data));
        } else if (action === "reaction") {
          set("cp-ci-reaction-results", "Ranking reaction mechanisms...");
          const data = await post("/api/search/reaction", reactionPayload());
          set("cp-ci-reaction-results", renderReaction(data));
        } else if (action === "reaction-name") {
          set("cp-ci-reaction-name-results", "Searching reaction-name catalog...");
          const data = await post("/api/search/reaction-name", {query: value("cp-ci-reaction-name")});
          set("cp-ci-reaction-name-results", renderReactionName(data));
        } else if (action === "mechanism") {
          const candidateName = sourceEvent?.target?.closest("[data-candidate-name]")?.dataset.candidateName || "";
          set("cp-ci-mechanism-results", "Generating explanation...");
          const payload = reactionPayload();
          if (candidateName) payload.reaction_name = candidateName;
          const data = await post("/api/mechanism/explain", payload);
          set("cp-ci-mechanism-results", renderMechanism(data));
        } else if (action === "report") {
          set("cp-ci-report-results", "Generating markdown report...");
          const data = await post("/api/reports/reaction", reactionPayload());
          const el = document.getElementById("cp-ci-report-results");
          if (el) el.textContent = data.markdown || "";
        }
      } catch (error) {
        const target = {topic:"cp-ci-topic-results",structure:"cp-ci-structure-results",reaction:"cp-ci-reaction-results","reaction-name":"cp-ci-reaction-name-results",mechanism:"cp-ci-mechanism-results",report:"cp-ci-report-results"}[action];
        set(target, `<div style="color:#fca5a5">ChemPulse chemical intelligence request failed: ${esc(error.message)}</div>`);
      }
    }
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
    if (action) window.ChemPulseChemicalIntelligence.run(action, event);
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
    if (reactionSketch.selectedAtom !== null && reactionSketch.selectedAtom !== newIndex) {
      addReactionBond(reactionSketch.selectedAtom, newIndex, reactionSketch.bond);
    }
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
    const status = document.getElementById("cp-ci-reaction-sketch-status");
    if (status) status.textContent = `${reactionSketch.atoms.length} atoms, ${reactionSketch.bonds.length} bonds. Assign the current drawing to a reaction role.`;
  }

  function addReactionSlot(role) {
    const molblock = molblockFromState(reactionSketch);
    if (!molblock) {
      set("cp-ci-reaction-slot-status", `<div style="color:#fca5a5">Draw a structure before assigning it to ${esc(role)}.</div>`);
      return;
    }
    reactionSlots[role].push({molblock, input_format: "molblock"});
    renderReactionSlots();
  }

  function renderReactionSlots() {
    const roleLabels = {substrate:"Substrates", product:"Products", reagent:"Reagents", catalyst:"Catalysts", byproduct:"By-products", intermediate:"Intermediates"};
    const rows = Object.keys(reactionSlots).map((role) => {
      const count = reactionSlots[role].length;
      return `<div class="cp-ci-card"><strong style="color:#fff">${esc(roleLabels[role])}</strong><div class="cp-ci-muted">${count ? `${count} drawn structure(s) ready for validation` : "No drawn structure assigned"}</div></div>`;
    }).join("");
    set("cp-ci-reaction-slot-status", rows);
  }

  function addAtomAt(x, y) {
    const newIndex = sketch.atoms.length;
    sketch.atoms.push({x, y, element: sketch.atom, charge: sketch.charge});
    if (sketch.selectedAtom !== null && sketch.selectedAtom !== newIndex) {
      addBond(sketch.selectedAtom, newIndex, sketch.bond);
    }
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
    const status = document.getElementById("cp-ci-sketch-status");
    if (status) status.textContent = `${sketch.atoms.length} atoms, ${sketch.bonds.length} bonds. Export format: V2000 MolBlock.`;
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
        lines.push(`<line x1="${a.x + nx * offset}" y1="${a.y + ny * offset}" x2="${b.x + nx * offset}" y2="${b.y + ny * offset}" stroke="#111827" stroke-width="3" stroke-linecap="round"/>`);
      }
    }
    const atomMarkup = state.atoms.map((atom, index) => {
      const selected = index === state.selectedAtom;
      const label = atom.element === "C" && atom.charge === 0 ? "" : `${atom.element}${atom.charge === 1 ? "+" : atom.charge === -1 ? "-" : ""}`;
      return `<g ${atomAttribute}="${index}" style="cursor:pointer"><circle cx="${atom.x}" cy="${atom.y}" r="${selected ? 15 : 11}" fill="${selected ? "#bae6fd" : "#f8fafc"}" stroke="${selected ? "#0284c7" : "#334155"}" stroke-width="2"/><text x="${atom.x}" y="${atom.y}" fill="#0f172a" font-size="16">${label}</text></g>`;
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

  setupSketcher();
  setupReactionSketcher();
})();




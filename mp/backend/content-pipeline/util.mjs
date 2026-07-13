// Shared pipeline utilities: normalization, hashing, deterministic RNG.

/** FNV-1a 32-bit hash. Mirrored in backend/src/core/embedding.ts — keep in sync. */
export function fnv1a(str) {
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h >>> 0;
}

/** Deterministic seeded RNG (mulberry32). */
export function rng(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const TYPO_FIXES = [
  [/\brgeression\b/gi, 'regression'],
  [/\bstoichastic\b/gi, 'stochastic'],
  [/\btesing\b/gi, 'testing'],
  [/\bfuncitons?\b/gi, 'functions'],
  [/\bcaculate\b/gi, 'CALCULATE'],
  [/\bnetwrk\b/gi, 'network'],
  [/\bassignemnt\b/gi, 'assignment'],
  [/\brandomizatiojn\b/gi, 'randomization'],
  [/\bintervval\b/gi, 'interval'],
  [/\bproblmes\b/gi, 'problems'],
  [/\bmodleing\b/gi, 'modeling'],
  [/\bdiganostics\b/gi, 'diagnostics'],
  [/\balgorithmatically\b/gi, 'algorithmically'],
  [/\bnumeeric\b/gi, 'numeric'],
  [/\bcatgeorical\b/gi, 'categorical'],
  [/\bdistribvuted\b/gi, 'distributed'],
  [/\bsdtorage\b/gi, 'storage'],
  [/\bmanagae\b/gi, 'manage'],
  [/\bmanagaer\b/gi, 'manager'],
  [/\baddresss\b/gi, 'address'],
  [/\bsecondar\b/gi, 'secondary'],
  [/\bderving\b/gi, 'deriving'],
  [/\bmaskign\b/gi, 'masking'],
  [/\binstrumented variables\b/gi, 'instrumental variables'],
  [/\bratrievers\b/gi, 'retrievers'],
  [/\bveriufy\b/gi, 'verify'],
  [/\bdaatabricks\b/gi, 'databricks'],
  [/\bnotbooklm\b/gi, 'NotebookLM'],
  [/\barchitect\b(?=$|\s*\|)/gi, 'architecture'],
  [/\binterval validity\b/gi, 'internal validity'],
  [/\berros\b/gi, 'errors'],
  [/\bintellgience\b/gi, 'intelligence'],
  [/\bartifical\b/gi, 'artificial'],
  [/\bllinear\b/gi, 'linear'],
  [/\bvaraibles\b/gi, 'variables'],
  [/\bcalcualtion\b/gi, 'calculation'],
  [/\bprobabiltiy\b/gi, 'probability'],
  [/\bquantitiative\b/gi, 'quantitative'],
  [/\bsensitivty\b/gi, 'sensitivity'],
  [/\bupdates\b(?= when| and|$)/gi, 'updated'],
];

/** Clean a raw spreadsheet term for display: fix typos, tidy whitespace. */
export function cleanTerm(raw) {
  let t = String(raw).replace(/\s+/g, ' ').trim();
  for (const [re, fix] of TYPO_FIXES) t = t.replace(re, fix);
  return t;
}

/** Normalize for matching: lowercase, strip punctuation/parentheticals. */
export function norm(s) {
  return cleanTerm(s)
    .toLowerCase()
    .replace(/https?:\/\/\S+/g, ' ')
    .replace(/[()[\]{}]/g, ' ')
    .replace(/[./]/g, ' ')
    .replace(/[^a-z0-9+# -]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function slug(s, max = 48) {
  return norm(s).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, max) || 'x';
}

/** Deterministic Jarvis visual identity for a card. */
export function cardVisual(id) {
  const h = fnv1a(id);
  const hues = [187, 199, 168, 262, 305, 38, 142, 210]; // cyan/teal/violet/magenta/amber/green families
  return {
    hue: hues[h % hues.length],
    glyph: ['◬', '⬡', '◈', '⟁', '✦', '◉', '⌬', '⟐'][(h >>> 3) % 8],
    pattern: ['grid', 'rings', 'scan', 'hex', 'orbit', 'pulse'][(h >>> 6) % 6],
  };
}

export function titleCase(s) {
  return s.replace(/\b([a-z])/g, (m, c) => c.toUpperCase());
}

/** Truncate at a word boundary. */
export function shorten(s, max = 52) {
  if (s.length <= max) return s;
  const cut = s.slice(0, max);
  return cut.slice(0, Math.max(20, cut.lastIndexOf(' '))) + '…';
}
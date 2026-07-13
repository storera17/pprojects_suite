// Mini-lesson synthesis: combines authored glossary entries with their
// subdeck's teaching context into a complete lesson per concept. Curated
// entries mark blankable phrases with «guillemets»; those drive cloze
// generation in cards.mjs.
import { CONTEXTS } from './knowledge/contexts.mjs';
import { GLOSSARY } from './knowledge/glossary/index.mjs';
import { norm } from './util.mjs';

const FALLBACK_CONTEXT = {
  domain: 'analytics', overview: 'A core analytics topic.', why: '',
  workplace: '', mistakes: [], sources: [],
};

export function contextFor(subdeck, contexts = CONTEXTS) {
  return contexts[subdeck.id] ?? FALLBACK_CONTEXT;
}

/** Pre-normalize glossary matchers once (callers may pass a fixture list). */
export function normalizeGlossary(list) {
  return list.map((e) => ({ ...e, nm: e.m.map((s) => norm(s)) }));
}

// Pre-normalize the real authored glossary once.
const ENTRIES = normalizeGlossary(GLOSSARY);

/** Find the most specific glossary entry whose matcher appears in the term. */
export function findEntry(term, entries = ENTRIES) {
  const t = ` ${norm(term)} `;
  let best = null;
  let bestLen = 0;
  for (const e of entries) {
    for (const m of e.nm) {
      if (m.length > bestLen && t.includes(` ${m} `)) {
        best = e;
        bestLen = m.length;
      }
    }
  }
  return best;
}

export const strip = (s) => String(s ?? '').replace(/[«»]/g, '');

function keyTermsFrom(entry, ctx, neighbors) {
  const set = new Set();
  for (const part of [entry?.d, entry?.how, entry?.ex]) {
    if (!part) continue;
    for (const m of String(part).matchAll(/«([^»]+)»/g)) {
      const t = m[1].trim();
      if (t.length > 2 && t.length < 42) set.add(t);
    }
  }
  for (const n of neighbors.slice(0, 3)) set.add(n);
  return [...set].slice(0, 8);
}

/**
 * Build the mini-lesson for one concept.
 * @param concept {term, displayTerm, difficulty}
 * @param ctx     subdeck context
 * @param neighbors display terms of nearby concepts in the same lesson
 */
export function buildLesson(concept, ctx, neighbors = [], entries = ENTRIES) {
  const entry = findEntry(concept.term, entries);
  const term = concept.displayTerm;

  if (entry) {
    return {
      curated: true,
      explanation: strip(entry.d),
      how: strip(entry.how ?? ''),
      why: strip(entry.why ?? ctx.why),
      workplace: strip(entry.ex ?? ctx.workplace),
      workedExample: strip(entry.we ?? ''),
      keyTerms: keyTermsFrom(entry, ctx, neighbors),
      mistakes: [entry.mk ? strip(entry.mk) : null, ...ctx.mistakes].filter(Boolean).slice(0, 3),
      related: neighbors.slice(0, 5),
      sources: entry.src ?? ctx.sources,
      entry,
    };
  }

  // No authored entry yet for this term: clearly flagged so coverage gaps
  // are visible rather than silently invented.
  return {
    curated: false,
    explanation: `“${term}” — not yet authored. ${ctx.overview}`,
    how: `Pending: write a glossary entry for this concept grounded in its source material.`,
    why: ctx.why,
    workplace: ctx.workplace,
    workedExample: '',
    keyTerms: neighbors.slice(0, 5),
    mistakes: ctx.mistakes.slice(0, 2),
    related: neighbors.slice(0, 5),
    sources: ctx.sources,
    entry: null,
  };
}
// Mini-lesson synthesis: combines curated glossary entries, per-class
// teaching contexts, and term parsing into a complete lesson per concept.
// Curated entries mark blankable phrases with «guillemets»; those drive
// cloze generation in cards.mjs.
import { CONTEXTS_A } from './knowledge/contexts-a.mjs';
import { CONTEXTS_B } from './knowledge/contexts-b.mjs';
import { GLOSSARY } from './knowledge/glossary/index.mjs';
import { norm } from './util.mjs';

export const CONTEXTS = { ...CONTEXTS_A, ...CONTEXTS_B };

export function contextFor(subdeck) {
  const key = subdeck.sourceClass ?? `tool:${subdeck.id.replace(/^sd-/, '')}`;
  return CONTEXTS[key] ?? CONTEXTS['Background Vocabulary'];
}

// Pre-normalize glossary matchers once.
const ENTRIES = GLOSSARY.map((e) => ({ ...e, nm: e.m.map((s) => norm(s)) }));

/** Find the most specific glossary entry whose matcher appears in the term. */
export function findEntry(term) {
  const t = ` ${norm(term)} `;
  let best = null;
  let bestLen = 0;
  for (const e of ENTRIES) {
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
 * @param ctx     class context
 * @param neighbors display terms of nearby concepts in the same lesson
 */
export function buildLesson(concept, ctx, neighbors = []) {
  const entry = findEntry(concept.term);
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

  // Context-driven fallback: still factual (class-level), clearly framed
  // around the term, and flagged so coverage can be measured.
  return {
    curated: false,
    explanation: `“${term}” is a core topic within ${ctx.domain}. ${ctx.overview}`,
    how: `Study this concept by connecting it to the ideas around it in this lesson: ${neighbors.slice(0, 3).join('; ') || ctx.domain}.`,
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
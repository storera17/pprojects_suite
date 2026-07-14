// Card generation: cloze-deletion cards from «marked» lesson text, applied
// scenario clozes, and image-occlusion cards over generated SVG diagrams.
import { cardVisual, fnv1a, norm, rng } from './util.mjs';
import { diagramFor } from './diagrams.mjs';
import { strip } from './synthesize.mjs';

/** Max cloze cards per concept, scaled by difficulty tier (1–3). */
export function clozeBudget(difficulty) {
  return [0, 8, 14, 22][difficulty] ?? 10;
}
/** Chooses a minimum number of cards to generate for a concept. */
export function minTarget(difficulty) {
  return [0, 5, 6, 8][difficulty] ?? 5;
}

/** Turn every «phrase» in `text` into its own single-blank cloze string. */
export function clozeVariants(text) {
  const marks = [...String(text).matchAll(/«([^»]+)»/g)];
  return marks.map((_, i) => {
    let out = '';
    let cursor = 0;
    marks.forEach((mm, j) => {
      out += text.slice(cursor, mm.index);
      out += j === i ? `{{c1::${mm[1]}}}` : mm[1];
      cursor = mm.index + mm[0].length;
    });
    out += text.slice(cursor);
    return out;
  });
}

/** Blank the concept term itself inside a sentence (term-recall card). */
export function termRecallCloze(term, sentence) {
  const clean = strip(sentence);
  const re = new RegExp(escapeRe(term), 'i');
  if (re.test(clean)) return clean.replace(re, (m) => `{{c1::${m}}}`);
  return `{{c1::${term}}} — ${clean}`;
}

/** Escapes arbitrary text so it can safely be used inside a RegExp. */
function escapeRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/** Returns the first sentence from source text for concise card prompts. */
function firstSentence(text) {
  const t = strip(text);
  const m = t.match(/^.*?[.!?](?=\s|$)/);
  return m ? m[0] : t;
}

/** Score a diagram region's relevance to a term by token overlap. */
function regionScore(term, region) {
  const tTok = new Set(norm(term).split(' '));
  let score = 0;
  for (const w of norm(region.label).split(' ')) if (w.length > 2 && tTok.has(w)) score++;
  return score;
}

/**
 * Generate all cards for one concept.
 * @returns array of card objects (cloze + occlusion).
 */
export function generateCards(concept, lesson, ctx, diagrams) {
  const cards = [];
  const baseId = `c-${concept.id}`;
  const seenText = new Set();
  const push = (type, fields) => {
    if (fields.text) {
      const key = fields.text.replace(/\s+/g, ' ');
      if (seenText.has(key)) return; // no duplicate clozes
      seenText.add(key);
    }
    const id = `${baseId}-${cards.length}`;
    cards.push({
      id,
      conceptId: concept.id,
      type,
      visual: cardVisual(id),
      evidence: (lesson.sources ?? ctx.sources).slice(0, 5),
      tags: [ctx.domain],
      ...fields,
    });
  };

  const budget = clozeBudget(concept.difficulty);

  // 1) Term-recall card from the lesson's first sentence.
  push('cloze', {
    kind: 'definition',
    text: termRecallCloze(concept.displayTerm, firstSentence(lesson.explanation)),
  });

  // 2) Single-blank variants from every «marked» phrase in curated content.
  const marked = [];
  if (lesson.entry) {
    for (const f of ['d', 'how', 'ex', 'we', 'mk']) {
      const src = lesson.entry[f];
      if (!src) continue;
      const kind = f === 'mk' ? 'mistake' : f === 'ex' || f === 'we' ? 'applied' : 'definition';
      for (const v of clozeVariants(src)) marked.push({ kind, text: v });
    }
  }
  for (const m of marked) {
    if (cards.length >= budget) break;
    push('cloze', m);
  }

  // 3) Why-it-matters cloze (applied understanding).
  if (cards.length < Math.max(minTarget(concept.difficulty), 3) && lesson.why) {
    push('cloze', {
      kind: 'applied',
      text: `Why ${concept.displayTerm} matters: ${termRecallCloze(concept.displayTerm, firstSentence(lesson.why)).replace(/^\{\{c1::[^}]+\}\} — /, '{{c1::' + concept.displayTerm + '}} — ')}`,
    });
  }

  // 4) Applied scenario cloze from the class scenario.
  if (cards.length < minTarget(concept.difficulty) && ctx.scenario) {
    push('cloze', {
      kind: 'applied',
      text: `Scenario (${ctx.domain}): ${strip(ctx.scenario)} A key concept at play here is {{c1::${concept.displayTerm}}}.`,
    });
  }

  // 5) Mistake-awareness cloze from class context if budget remains.
  if (cards.length < minTarget(concept.difficulty) && lesson.mistakes[0]) {
    push('cloze', {
      kind: 'mistake',
      text: `Common mistake near “${concept.displayTerm}”: {{c1::${lesson.mistakes[0]}}}`,
    });
  }

  // 6) Image occlusion when a diagram genuinely matches this concept.
  const digId = diagramFor(concept.term);
  if (digId && diagrams[digId]) {
    const dig = diagrams[digId];
    const ranked = [...dig.regions]
      .map((r) => ({ r, s: regionScore(concept.term, r) }))
      .sort((a, b) => b.s - a.s);
    const rand = rng(fnv1a(concept.id));
    const picks = [];
    if (ranked[0] && ranked[0].s > 0) picks.push(ranked[0].r);
    else picks.push(dig.regions[Math.floor(rand() * dig.regions.length)]);
    if (concept.difficulty >= 2 && dig.regions.length > 2) {
      const other = dig.regions[Math.floor(rand() * dig.regions.length)];
      if (other.id !== picks[0].id) picks.push(other);
    }
    for (const region of picks) {
      push('occlusion', {
        kind: 'occlusion',
        prompt: `${dig.title}: identify the masked element.`,
        occlusion: { diagramId: digId, focusId: region.id, answer: region.label },
      });
    }
  }

  return cards;
}
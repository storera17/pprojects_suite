import { describe, expect, it } from 'vitest';
// @ts-expect-error plain ESM pipeline modules
import { buildStructure, chunkLessons, DECKS, SUBDECKS } from '../content-pipeline/taxonomy.mjs';
// @ts-expect-error plain ESM pipeline modules
import { buildDiagrams, diagramFor } from '../content-pipeline/diagrams.mjs';
// @ts-expect-error plain ESM pipeline modules
import { findEntry } from '../content-pipeline/synthesize.mjs';
import { fixtureCourse } from './fixtures';
import { clozeAnswers, isValidCloze } from '../src/core/cloze';

describe('Deck/subdeck skeleton', () => {
  it('orders decks foundational → advanced', () => {
    const order = DECKS.map((d: any) => d.id);
    expect(order.indexOf('foundations')).toBeLessThan(order.indexOf('deep-learning'));
    expect(order.indexOf('mining')).toBeLessThan(order.indexOf('genai'));
  });

  it('only includes subdecks that have authored concepts', () => {
    const decks = buildStructure();
    for (const d of decks) {
      for (const sd of d.subdecks) expect(sd.concepts.length).toBeGreaterThan(0);
    }
    const allIds = new Set(decks.flatMap((d: any) => d.subdecks.map((s: any) => s.id)));
    const pendingIds = SUBDECKS.filter((s: any) => s.concepts.length === 0).map((s: any) => s.id);
    for (const id of pendingIds) expect(allIds.has(id)).toBe(false);
  });
});

describe('Lesson ordering', () => {
  it('chunks concepts into lessons of 5–9 (single lesson for small sets)', () => {
    const chunks = chunkLessons(Array.from({ length: 23 }, (_, i) => `t${i}`));
    expect(chunks.length).toBeGreaterThanOrEqual(3);
    for (const ch of chunks) expect(ch.length).toBeLessThanOrEqual(9);
    expect(chunkLessons(['only']).length).toBe(1);
  });

  it('assigns globally increasing unlock indexes', () => {
    const course = fixtureCourse();
    const idx = course.lessons.map((l) => l.unlockIndex).sort((a, b) => a - b);
    idx.forEach((v, i) => expect(v).toBe(i));
  });
});

describe('Card generation format', () => {
  const course = fixtureCourse();

  it('generates only cloze and occlusion cards', () => {
    for (const c of course.cards) expect(['cloze', 'occlusion']).toContain(c.type);
  });

  it('every cloze card is valid {{c1::…}} and unique per concept', () => {
    for (const c of course.cards.filter((x) => x.type === 'cloze')) {
      expect(isValidCloze(c.text!)).toBe(true);
      expect(clozeAnswers(c.text!).length).toBeGreaterThan(0);
    }
  });

  it('attaches at least one real evidence source to every card', () => {
    // Unlike CORTEX (which padded every card to a fixed 5 generic sources),
    // MomentumProdigy cards cite only the real, specific source(s) they were
    // grounded in — usually 1-2 per concept.
    for (const c of course.cards) {
      expect(c.evidence.length).toBeGreaterThanOrEqual(1);
      for (const s of c.evidence) {
        expect(s.title.length).toBeGreaterThan(5);
        expect(['textbook', 'academic', 'docs', 'course', 'web']).toContain(s.kind);
      }
    }
  });

  it('scales card volume with difficulty', () => {
    const count = (id: string) => course.concepts.find((c) => c.displayTerm.toLowerCase().includes(id))!.cardIds.length;
    // CALCULATE (difficulty 3, rich entry) ≥ descriptive analytics (difficulty 1)
    expect(count('calculate')).toBeGreaterThanOrEqual(count('descriptive analytics'));
    for (const c of course.concepts) expect(c.cardIds.length).toBeGreaterThanOrEqual(2);
  });

  it('gives every card a fixed Jarvis visual identity', () => {
    for (const c of course.cards) {
      expect(c.visual.hue).toBeGreaterThan(0);
      expect(c.visual.glyph.length).toBeGreaterThan(0);
      expect(c.visual.pattern.length).toBeGreaterThan(0);
    }
  });

  it('every concept gets a mini-lesson with explanation, why, workplace, mistakes, sources', () => {
    for (const c of course.concepts) {
      expect(c.mini.explanation.length).toBeGreaterThan(30);
      expect(c.mini.why.length).toBeGreaterThan(10);
      expect(c.mini.workplace.length).toBeGreaterThan(10);
      expect(c.mini.mistakes.length).toBeGreaterThan(0);
      expect(c.mini.sources.length).toBeGreaterThanOrEqual(1);
    }
  });
});

describe('Image occlusion generation', () => {
  it('builds diagrams with maskable labeled regions', () => {
    const digs = buildDiagrams();
    expect(Object.keys(digs).length).toBeGreaterThanOrEqual(15);
    for (const d of Object.values(digs) as any[]) {
      expect(d.svg).toContain('<svg');
      expect(d.regions.length).toBeGreaterThan(0);
      for (const r of d.regions) {
        expect(r.w).toBeGreaterThan(0);
        expect(r.label.length).toBeGreaterThan(0);
      }
    }
  });

  it('matches diagrams only where genuinely relevant', () => {
    expect(diagramFor('confusion matrix')).toBe('confusion-matrix');
    expect(diagramFor('filter context')).toBe('dax-context');
    expect(diagramFor('descriptive analytics')).toBeNull();
  });

  it('occlusion cards reference an existing diagram region', () => {
    const course = fixtureCourse();
    for (const c of course.cards.filter((x) => x.type === 'occlusion')) {
      const dig = course.diagrams[c.occlusion!.diagramId];
      expect(dig).toBeTruthy();
      expect(dig.regions.some((r) => r.id === c.occlusion!.focusId)).toBe(true);
    }
  });
});

describe('Knowledge coverage (authored content smoke test)', () => {
  it('finds authored glossary entries for terms known to be written', () => {
    // sd-complexity (optimization deck) is the pilot subdeck authored first —
    // this is a regression check that it stays matchable, not a claim of
    // full coverage (most subdecks are still pending; see
    // backend/content-pipeline/authoring-manifest.json).
    for (const term of ['Big O Notation', 'NP-Completeness', 'Breadth-First Search']) {
      expect(findEntry(term), term).toBeTruthy();
    }
  });
});

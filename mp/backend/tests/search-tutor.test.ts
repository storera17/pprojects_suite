import { describe, expect, it } from 'vitest';
import { SearchIndex } from '../src/core/search';
import { Tutor, blankKeyPhrase } from '../src/core/tutor';
import { isValidCloze } from '../src/core/cloze';
import { embed, cosine } from '../src/core/embedding';
// @ts-expect-error plain ESM pipeline module
import { embed as pipelineEmbed } from '../content-pipeline/embed.mjs';
import { fixtureCourse } from './fixtures';

describe('Embedding parity (app ↔ pipeline)', () => {
  it('produces identical vectors for the same text', () => {
    for (const text of ['filter context propagation', 'gradient descent learning rate', 'A/B test power analysis']) {
      const a = embed(text);
      const b = pipelineEmbed(text);
      for (let i = 0; i < a.length; i++) expect(a[i]).toBeCloseTo(b[i], 6);
    }
  });

  it('related texts are closer than unrelated ones', () => {
    const a = embed('decision tree pruning overfitting');
    const b = embed('pruning a tree to avoid overfit');
    const c = embed('snowflake cloud warehouse billing');
    expect(cosine(a, b)).toBeGreaterThan(cosine(a, c));
  });
});

describe('Search (keyword + semantic, offline)', () => {
  const index = new SearchIndex(fixtureCourse());

  it('keyword search finds concepts, lessons, decks, cards, and sources', () => {
    const hits = index.search('confusion matrix');
    expect(hits.length).toBeGreaterThan(0);
    expect(hits[0].title.toLowerCase()).toContain('confusion');
    const types = new Set(index.search('analytics').map((h) => h.type));
    expect(types.size).toBeGreaterThanOrEqual(3);
  });

  it('semantic search matches paraphrases without exact keywords', () => {
    const hits = index.search('memorizing noise instead of generalizing', 20, ['concept']);
    expect(hits.some((h) => /overfit/i.test(h.title))).toBe(true);
  });

  it('type filters narrow results', () => {
    const hits = index.search('CALCULATE', 20, ['source']);
    for (const h of hits) expect(h.type).toBe('source');
  });

  it('indexes AI practice cards once added', () => {
    index.addPracticeCards([{
      id: 'p1', text: '{{c1::Snowflake}} separates storage from compute.', conceptId: null,
      topic: 'Snowflake', createdAt: Date.now(), evidence: [], visual: { hue: 187, glyph: '◬', pattern: 'grid' },
    }]);
    const hits = index.search('separates storage from compute', 20, ['practice']);
    expect(hits.length).toBeGreaterThan(0);
  });
});

describe('Offline tutor fallback behavior', () => {
  const tutor = new Tutor(fixtureCourse());

  it('answers concept questions from the knowledge base without any LLM', async () => {
    const a = await tutor.ask('What is filter context?');
    expect(a.length).toBeGreaterThan(80);
    expect(a.toLowerCase()).toContain('filter');
    // never labels its source tier
    expect(a).not.toMatch(/knowledge base|course material|general knowledge/i);
  });

  it('handles comparison questions', async () => {
    const a = await tutor.ask('descriptive analytics vs predictive analytics');
    expect(a).toMatch(/descriptive/i);
    expect(a).toMatch(/predictive/i);
  });

  it('gives a graceful answer when nothing matches', async () => {
    const a = await tutor.ask('zzqx unrelated nonsense query 9931');
    expect(a.length).toBeGreaterThan(40);
  });

  it('keeps history in memory only (session-scoped)', async () => {
    expect(tutor.history.length).toBeGreaterThan(0);
    const fresh = new Tutor(fixtureCourse());
    expect(fresh.history).toHaveLength(0);
  });

  it('explains a revealed card', () => {
    const card = fixtureCourse().cards.find((c) => c.type === 'cloze')!;
    const text = tutor.explainCard(card.id);
    expect(text.length).toBeGreaterThan(60);
  });

  it('generates valid practice cloze cards with evidence', () => {
    const conceptId = fixtureCourse().concepts[0].id;
    const cards = tutor.generatePractice([conceptId], 2);
    expect(cards.length).toBeGreaterThan(0);
    for (const c of cards) {
      expect(isValidCloze(c.text)).toBe(true);
      expect(c.evidence.length).toBeGreaterThan(0);
      expect(c.visual.glyph.length).toBeGreaterThan(0);
    }
  });

  it('blankKeyPhrase produces a single well-formed blank', () => {
    const out = blankKeyPhrase('Regularization penalizes model complexity to improve generalization on unseen data.');
    expect(isValidCloze(out)).toBe(true);
    expect(out.match(/\{\{c1::/g)!.length).toBe(1);
  });
});

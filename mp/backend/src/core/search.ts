// Offline hybrid search: keyword scoring + semantic similarity over the
// precomputed course embeddings. No network, no model download — query
// vectors are computed with the same hashed-feature embedder used at build
// time (see embedding.ts / backend/content-pipeline/embed.mjs).
import type { Card, Course, PracticeCard } from './types';
import { clozeBack } from './cloze';
import { cosine, embed, unpackVector } from './embedding';

export type SearchHitType = 'concept' | 'lesson' | 'deck' | 'card' | 'source' | 'practice';

export interface SearchHit {
  type: SearchHitType;
  id: string;
  title: string;
  snippet: string;
  score: number;
  deckId?: string;
  lessonId?: string;
  conceptId?: string;
}

interface IndexItem {
  type: SearchHitType;
  id: string;
  title: string;
  body: string;
  vec: Float32Array | null;
  deckId?: string;
  lessonId?: string;
  conceptId?: string;
}

const STOP = new Set(['the', 'and', 'what', 'that', 'with', 'for', 'how', 'why', 'are', 'was', 'does', 'about']);
const tok = (s: string) => s.toLowerCase().split(/[^a-z0-9]+/).filter((w) => w.length > 1 && !STOP.has(w));

export class SearchIndex {
  private items: IndexItem[] = [];

  constructor(course?: Course) {
    if (course) this.buildFromCourse(course);
  }

  buildFromCourse(course: Course) {
    const conceptVec = new Map<string, Float32Array>();
    for (const c of course.concepts) {
      const vec = unpackVector(c.vec, course.meta.embedDims);
      conceptVec.set(c.id, vec);
      this.items.push({
        type: 'concept', id: c.id, title: c.displayTerm,
        body: `${c.mini.explanation} ${c.mini.why} ${c.mini.workplace}`,
        vec, deckId: c.deckId, lessonId: c.lessonId, conceptId: c.id,
      });
    }
    for (const d of course.decks) {
      this.items.push({ type: 'deck', id: d.id, title: d.title, body: d.tagline, vec: null, deckId: d.id });
    }
    const lessonById = new Map(course.lessons.map((l) => [l.id, l]));
    for (const l of course.lessons) {
      this.items.push({ type: 'lesson', id: l.id, title: l.title, body: l.conceptIds.join(' '), vec: null, deckId: l.deckId, lessonId: l.id });
    }
    for (const card of course.cards) {
      const text = card.type === 'cloze' ? clozeBack(card.text ?? '') : `${card.prompt ?? ''} ${card.occlusion?.answer ?? ''}`;
      this.items.push({
        type: 'card', id: card.id, title: text.slice(0, 80),
        body: text, vec: conceptVec.get(card.conceptId) ?? null,
        deckId: card.deckId, lessonId: card.lessonId, conceptId: card.conceptId,
      });
    }
    // sources, deduplicated by title
    const seen = new Set<string>();
    for (const c of course.concepts) {
      for (const s of c.mini.sources) {
        if (seen.has(s.title)) continue;
        seen.add(s.title);
        this.items.push({ type: 'source', id: `src-${seen.size}`, title: s.title, body: `${s.kind} ${s.ref}`, vec: null });
      }
    }
    void lessonById;
  }

  addPracticeCards(cards: PracticeCard[]) {
    this.items = this.items.filter((i) => i.type !== 'practice');
    for (const c of cards) {
      this.items.push({
        type: 'practice', id: c.id, title: `AI Practice: ${c.topic}`,
        body: clozeBack(c.text), vec: null, conceptId: c.conceptId ?? undefined,
      });
    }
  }

  /** Hybrid search. Keyword match dominates; semantic similarity recalls related items. */
  search(query: string, limit = 30, types?: SearchHitType[]): SearchHit[] {
    const q = query.trim();
    if (!q) return [];
    const qTokens = tok(q);
    const qVec = embed(q);
    // Concepts and lessons outrank individual cards so semantic-only queries
    // surface ideas first, not thousands of near-duplicate card lines.
    const TYPE_WEIGHT: Record<SearchHitType, number> = {
      concept: 1.0, lesson: 0.92, deck: 0.92, practice: 0.9, source: 0.85, card: 0.7,
    };
    const hits: SearchHit[] = [];
    for (const item of this.items) {
      if (types && !types.includes(item.type)) continue;
      const hay = `${item.title} ${item.body}`.toLowerCase();
      let kw = 0;
      for (const t of qTokens) {
        if (item.title.toLowerCase().includes(t)) kw += 2;
        else if (hay.includes(t)) kw += 1;
      }
      const kwScore = qTokens.length ? kw / (2 * qTokens.length) : 0;
      const semScore = item.vec ? Math.max(0, cosine(qVec, item.vec)) : 0;
      const score = (kwScore * 0.65 + semScore * 0.35) * TYPE_WEIGHT[item.type];
      if (score > 0.08) {
        hits.push({
          type: item.type, id: item.id, title: item.title,
          snippet: item.body.slice(0, 160), score,
          deckId: item.deckId, lessonId: item.lessonId, conceptId: item.conceptId,
        });
      }
    }
    hits.sort((a, b) => b.score - a.score);
    const seen = new Set<string>();
    const out: SearchHit[] = [];
    for (const h of hits) {
      const key = `${h.type}:${h.title.slice(0, 60)}`;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(h);
      if (out.length >= limit) break;
    }
    return out;
  }
}

// MomentumProdigy offline tutor.
//
// Two-tier design (see docs/OFFLINE_AI.md for the full justification):
//  1. KnowledgeTutor (always available, zero-download): retrieval-augmented
//     answer composition over the bundled course knowledge base — embeddings
//     + keyword retrieval pick the most relevant concepts, and a natural-
//     language composer assembles an answer from their curated lesson
//     content. Works on every platform with no model weights.
//  2. LocalLLMProvider (optional upgrade): if a llama.cpp-compatible bridge
//     is registered (Tauri sidecar on desktop, llama.cpp-swift on iOS), the
//     tutor routes generation through the local model, using retrieval
//     results as grounding context. scripts/fetch-models.mjs downloads the
//     recommended weights (Qwen2.5-3B-Instruct Q4 for desktop, 1.5B for
//     iPhone).
//
// Answers never label which tier produced them. Chat history is held in
// memory only and disappears when the session ends (per product spec).
import type { Concept, Course, PracticeCard, Source } from './types';
import { cosine, embed, unpackVector } from './embedding';
import { cardVisualFor } from './visual';
import { clozeAnswers, clozeBack } from './cloze';

export interface TutorTurn {
  role: 'user' | 'tutor';
  text: string;
}

export interface LLMBridge {
  /** Generate a completion for the prompt; must work fully offline. */
  generate(prompt: string, opts?: { maxTokens?: number }): Promise<string>;
  name: string;
}

declare global {
  interface Window { __MomentumProdigy_LLM?: LLMBridge }
}

interface Retrieved {
  concept: Concept;
  score: number;
}

const STOP = new Set(['the', 'and', 'what', 'that', 'with', 'for', 'how', 'why', 'are', 'is', 'was', 'does', 'between', 'difference', 'versus', 'about', 'tell', 'explain', 'mean', 'means', 'can', 'you', 'use', 'used', 'when', 'which', 'should']);
const tok = (s: string) => s.toLowerCase().split(/[^a-z0-9]+/).filter((w) => w.length > 2 && !STOP.has(w));

export class Tutor {
  private vecs = new Map<string, Float32Array>();
  private concepts: Concept[] = [];
  /** Session-only conversation memory; intentionally never persisted. */
  history: TutorTurn[] = [];

  constructor(private course: Course) {
    this.concepts = course.concepts;
    for (const c of course.concepts) this.vecs.set(c.id, unpackVector(c.vec, course.meta.embedDims));
  }

  private bridge(): LLMBridge | null {
    return (typeof window !== 'undefined' && window.__MomentumProdigy_LLM) || null;
  }

  retrieve(query: string, k = 4): Retrieved[] {
    const qVec = embed(query);
    const qTokens = new Set(tok(query));
    const scored: Retrieved[] = [];
    for (const c of this.concepts) {
      const sem = cosine(qVec, this.vecs.get(c.id)!);
      let kw = 0;
      const title = c.displayTerm.toLowerCase();
      for (const t of qTokens) if (title.includes(t)) kw += 1;
      const kwScore = qTokens.size ? kw / qTokens.size : 0;
      const score = sem * 0.45 + kwScore * 0.55;
      if (score > 0.12) scored.push({ concept: c, score });
    }
    return scored.sort((a, b) => b.score - a.score).slice(0, k);
  }

  /** Main entry: answer a free-form question. */
  async ask(question: string): Promise<string> {
    this.history.push({ role: 'user', text: question });
    const hits = this.retrieve(question);
    const bridge = this.bridge();
    let answer: string;
    if (bridge) {
      const context = hits
        .map((h) => `${h.concept.displayTerm}: ${h.concept.mini.explanation} ${h.concept.mini.how}`)
        .join('\n');
      const prompt =
        `You are MomentumProdigy, a calm, precise analytics tutor. Use the context if relevant; answer naturally and concisely.\n` +
        `Context:\n${context}\n\nQuestion: ${question}\nAnswer:`;
      try {
        answer = (await bridge.generate(prompt, { maxTokens: 400 })).trim();
      } catch {
        answer = this.compose(question, hits);
      }
    } else {
      answer = this.compose(question, hits);
    }
    this.history.push({ role: 'tutor', text: answer });
    return answer;
  }

  /** Retrieval-grounded answer composition (the always-offline tier). */
  compose(question: string, hits: Retrieved[]): string {
    const q = question.toLowerCase();
    if (hits.length === 0) {
      return (
        'I don’t have strong material on that exact phrasing. Try naming the concept directly ' +
        '(for example “filter context”, “gradient descent”, or “difference-in-differences”), ' +
        'or open Search to browse every lesson and card in the course.'
      );
    }

    // Comparison question with two strong matches → contrast them.
    const compares = /\bvs\.?\b|\bversus\b|difference between|compare/.test(q);
    if (compares && hits.length >= 2 && hits[1].score > 0.2) {
      const [a, b] = [hits[0].concept, hits[1].concept];
      return (
        `${a.displayTerm} — ${a.mini.explanation}\n\n` +
        `${b.displayTerm} — ${b.mini.explanation}\n\n` +
        `The practical distinction: ${a.mini.workplace} By contrast, ${lowerFirst(b.mini.workplace)}`
      );
    }

    const c = hits[0].concept;
    const m = c.mini;
    const parts: string[] = [];
    if (/why|matter|care|important/.test(q)) {
      parts.push(m.explanation, `Why it matters: ${m.why}`);
    } else if (/how|work|steps|do i|implement/.test(q)) {
      parts.push(m.explanation);
      if (m.how) parts.push(m.how);
      if (m.workedExample) parts.push(`Worked example: ${m.workedExample}`);
    } else if (/example|use|applied|practice|real/.test(q)) {
      parts.push(m.explanation, `In practice: ${m.workplace}`);
      if (m.workedExample) parts.push(m.workedExample);
    } else if (/mistake|wrong|careful|pitfall|trap/.test(q)) {
      parts.push(m.explanation);
      if (m.mistakes.length) parts.push(`Watch out for: ${m.mistakes.join(' Also: ')}`);
    } else {
      parts.push(m.explanation);
      if (m.why) parts.push(m.why);
      if (m.workplace) parts.push(`In practice: ${m.workplace}`);
    }
    if (m.related.length) parts.push(`Related ideas worth reviewing: ${m.related.slice(0, 3).join('; ')}.`);
    return parts.filter(Boolean).join('\n\n');
  }

  /** Explain a revealed card during review (why the answer is what it is). */
  explainCard(cardId: string): string {
    const card = this.course.cards.find((x) => x.id === cardId);
    if (!card) return 'I can’t find that card.';
    const concept = this.concepts.find((x) => x.id === card.conceptId);
    if (!concept) return 'I can’t find the concept behind that card.';
    const m = concept.mini;
    if (card.type === 'occlusion' && card.occlusion) {
      const dig = this.course.diagrams[card.occlusion.diagramId];
      return (
        `The masked element is “${card.occlusion.answer}” in the ${dig?.title ?? 'diagram'}. ` +
        `${m.explanation}\n\nWhy this placement matters: ${m.why}`
      );
    }
    const answers = clozeAnswers(card.text ?? '');
    const full = clozeBack(card.text ?? '');
    return (
      `The blank${answers.length > 1 ? 's' : ''} ${answers.map((a) => `“${a}”`).join(', ')} ` +
      `complete${answers.length > 1 ? '' : 's'} the statement: ${full}\n\n` +
      `${m.explanation}` +
      (m.mistakes.length ? `\n\nA common slip here: ${m.mistakes[0]}` : '')
    );
  }

  /**
   * Generate extra practice questions for weak concepts → AI Practice deck.
   * Sentences not already used by the locked course cards are clozed so the
   * practice cards supplement rather than duplicate.
   */
  generatePractice(conceptIds: string[], perConcept = 2): PracticeCard[] {
    const out: PracticeCard[] = [];
    for (const id of conceptIds) {
      const c = this.concepts.find((x) => x.id === id);
      if (!c) continue;
      const m = c.mini;
      const candidates: string[] = [];
      if (m.why) candidates.push(`Why ${c.displayTerm} matters: ${blankKeyPhrase(m.why)}`);
      if (m.workplace) candidates.push(`Applied — ${c.displayTerm}: ${blankKeyPhrase(m.workplace)}`);
      if (m.how) candidates.push(`Mechanics of ${c.displayTerm}: ${blankKeyPhrase(m.how)}`);
      if (m.mistakes[0]) candidates.push(`Pitfall near ${c.displayTerm}: {{c1::${m.mistakes[0]}}}`);
      candidates.push(`{{c1::${c.displayTerm}}} — ${firstSentence(m.explanation)}`);
      let added = 0;
      for (const text of candidates) {
        if (added >= perConcept) break;
        if (!/\{\{c1::/.test(text)) continue;
        const pid = `pr-${id}-${out.length}-${Date.now().toString(36)}`;
        out.push({
          id: pid, text, conceptId: id, topic: c.displayTerm,
          createdAt: Date.now(), evidence: m.sources.slice(0, 5) as Source[],
          visual: cardVisualFor(pid),
        });
        added++;
      }
    }
    return out;
  }
}

function firstSentence(text: string): string {
  const m = text.match(/^.*?[.!?](?=\s|$)/);
  return m ? m[0] : text;
}

/** Blank the most content-heavy phrase of a sentence (longest 2–4 word run). */
export function blankKeyPhrase(text: string): string {
  const sentence = firstSentence(text);
  const words = sentence.split(/\s+/);
  if (words.length < 5) return `{{c1::${sentence}}}`;
  let best = { start: 0, len: 2, score: 0 };
  for (let start = 1; start < words.length - 1; start++) {
    for (let len = 2; len <= 4 && start + len <= words.length; len++) {
      const phrase = words.slice(start, start + len);
      const score = phrase.reduce((a, w) => a + (w.length > 4 ? w.length : 0), 0);
      if (score > best.score) best = { start, len, score };
    }
  }
  const blanked = words.slice(best.start, best.start + best.len).join(' ').replace(/[.,;]$/, '');
  const idx = sentence.indexOf(blanked);
  if (idx < 0) return `{{c1::${sentence}}}`;
  return sentence.slice(0, idx) + `{{c1::${blanked}}}` + sentence.slice(idx + blanked.length);
}

function lowerFirst(s: string): string {
  return s ? s[0].toLowerCase() + s.slice(1) : s;
}

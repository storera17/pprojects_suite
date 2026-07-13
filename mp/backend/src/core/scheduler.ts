// Original SM-2-family spaced-repetition scheduler.
// States: new → learning (timed steps) → review (day
// intervals with an ease factor); lapses send cards to relearning.
import type { CardPhase, CardState, Rating } from './types';

export const SCHED = {
  learningStepsMin: [1, 10], // minutes
  relearningStepsMin: [10],
  graduatingIntervalDays: 1,
  easyIntervalDays: 4,
  startingEase: 2.5,
  minEase: 1.3,
  easeBonusEasy: 0.15,
  easePenaltyHard: 0.15,
  easePenaltyAgain: 0.2,
  hardIntervalFactor: 1.2,
  easyIntervalBonus: 1.3,
  lapseIntervalFactor: 0.5,
  maxIntervalDays: 36500,
  fuzz: 0.05,
};

const MIN = 60_000;
const DAY = 86_400_000;

export function newCardState(cardId: string): CardState {
  return {
    cardId, phase: 'new', due: 0, intervalDays: 0, ease: SCHED.startingEase,
    stepIndex: 0, reps: 0, lapses: 0, correctStreak: 0, answers: 0, correct: 0,
    lastReview: null, introducedOn: null,
  };
}

export function dayKey(ts: number): string {
  const d = new Date(ts);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

/** Deterministic fuzz (±5%) so identical answers do not all clump on one day. */
function fuzzed(days: number, seedStr: string): number {
  if (days < 2.5) return days;
  let h = 2166136261;
  for (let i = 0; i < seedStr.length; i++) h = Math.imul(h ^ seedStr.charCodeAt(i), 16777619);
  const r = ((h >>> 0) % 1000) / 1000; // 0..1
  const span = days * SCHED.fuzz * 2;
  return Math.min(SCHED.maxIntervalDays, days - days * SCHED.fuzz + r * span);
}

/**
 * Grade a card. Pure function: returns the next state without mutating input.
 */
export function answerCard(state: CardState, rating: Rating, now: number): CardState {
  const s: CardState = { ...state };
  s.answers += 1;
  if (rating !== 'again') {
    s.correct += 1;
    s.correctStreak += 1;
  } else {
    s.correctStreak = 0;
  }
  s.lastReview = now;
  s.reps += 1;
  if (s.introducedOn === null) s.introducedOn = dayKey(now);

  const phase: CardPhase = s.phase === 'new' ? 'learning' : s.phase;

  if (phase === 'learning' || phase === 'relearning') {
    const steps = phase === 'learning' ? SCHED.learningStepsMin : SCHED.relearningStepsMin;
    if (rating === 'again') {
      s.phase = phase;
      s.stepIndex = 0;
      s.due = now + steps[0] * MIN;
    } else if (rating === 'easy') {
      graduate(s, now, true);
    } else if (rating === 'good') {
      const next = s.stepIndex + 1;
      if (next >= steps.length) graduate(s, now, false);
      else {
        s.phase = phase;
        s.stepIndex = next;
        s.due = now + steps[next] * MIN;
      }
    } else {
      // Hard repeats the current step with a deterministic delay.
      s.phase = phase;
      s.due = now + steps[Math.min(s.stepIndex, steps.length - 1)] * MIN * 1.5;
    }
    return s;
  }

  // review phase
  if (rating === 'again') {
    s.lapses += 1;
    s.ease = Math.max(SCHED.minEase, s.ease - SCHED.easePenaltyAgain);
    s.phase = 'relearning';
    s.stepIndex = 0;
    s.intervalDays = Math.max(1, Math.round(s.intervalDays * SCHED.lapseIntervalFactor));
    s.due = now + SCHED.relearningStepsMin[0] * MIN;
    return s;
  }

  let interval = s.intervalDays;
  if (rating === 'hard') {
    s.ease = Math.max(SCHED.minEase, s.ease - SCHED.easePenaltyHard);
    interval = Math.max(interval + 1, interval * SCHED.hardIntervalFactor);
  } else if (rating === 'good') {
    interval = Math.max(interval + 1, interval * s.ease);
  } else {
    s.ease = s.ease + SCHED.easeBonusEasy;
    interval = Math.max(interval + 1, interval * s.ease * SCHED.easyIntervalBonus);
  }
  s.intervalDays = Math.min(SCHED.maxIntervalDays, fuzzed(interval, s.cardId + s.reps));
  s.phase = 'review';
  s.due = now + s.intervalDays * DAY;
  return s;
}

function graduate(s: CardState, now: number, easy: boolean) {
  s.phase = 'review';
  s.stepIndex = 0;
  s.intervalDays = easy ? SCHED.easyIntervalDays : SCHED.graduatingIntervalDays;
  s.due = now + s.intervalDays * DAY;
}

/** Preview the response-button intervals ("10m", "1d", "4d", …). */
export function previewIntervals(state: CardState, now: number): Record<Rating, string> {
  const fmt = (next: CardState) => {
    const ms = next.due - now;
    if (ms < 50 * MIN) return `${Math.max(1, Math.round(ms / MIN))}m`;
    if (ms < DAY * 1.5) return '1d';
    return `${Math.round(ms / DAY)}d`;
  };
  return {
    again: fmt(answerCard(state, 'again', now)),
    hard: fmt(answerCard(state, 'hard', now)),
    good: fmt(answerCard(state, 'good', now)),
    easy: fmt(answerCard(state, 'easy', now)),
  };
}

export function isDue(state: CardState, now: number): boolean {
  return state.phase !== 'new' && state.due <= now;
}

/**
 * Automatic new-card pacing (no manual limit): the heavier today's review
 * load, the fewer new cards are introduced — clamped to [4, 20] per day.
 */
export function newCardAllowance(dueReviewCount: number, introducedToday: number): number {
  const budget = Math.max(4, 20 - Math.floor(dueReviewCount / 8));
  return Math.max(0, budget - introducedToday);
}

export interface QueueResult {
  learning: string[];
  review: string[];
  newCards: string[];
}

/**
 * Build today's queue: due learning cards first (by due time),
 * then due reviews, then new cards introduced lesson-by-lesson in unlock
 * order, paced by newCardAllowance.
 * @param lessonOrder card ids of unlocked lessons, in course order
 */
export function buildQueue(
  states: Map<string, CardState>,
  lessonOrderedCardIds: string[],
  now: number,
  introducedToday: number,
): QueueResult {
  const learning: { id: string; due: number }[] = [];
  const review: { id: string; due: number }[] = [];
  for (const st of states.values()) {
    if (!isDue(st, now)) continue;
    if (st.phase === 'learning' || st.phase === 'relearning') learning.push({ id: st.cardId, due: st.due });
    else review.push({ id: st.cardId, due: st.due });
  }
  learning.sort((a, b) => a.due - b.due);
  review.sort((a, b) => a.due - b.due);

  const allowance = newCardAllowance(review.length, introducedToday);
  const newCards: string[] = [];
  for (const id of lessonOrderedCardIds) {
    if (newCards.length >= allowance) break;
    const st = states.get(id);
    if (!st || st.phase === 'new') newCards.push(id);
  }
  return {
    learning: learning.map((x) => x.id),
    review: review.map((x) => x.id),
    newCards,
  };
}

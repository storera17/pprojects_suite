// Mastery scoring and lesson unlocking.
// A lesson unlocks when the previous lesson reaches the configured mastery and
// readiness thresholds. Mini-lesson reading is never gated.
import type { CardState, Lesson } from './types';

export const MASTERY_THRESHOLD = 0.9;
export const READINESS_THRESHOLD = 0.8;

/** Mastery of one card in [0,1]: grows with graduation, streak, and interval. */
export function cardMastery(st: CardState | undefined): number {
  if (!st || st.phase === 'new') return 0;
  if (st.phase === 'learning') return 0.25;
  if (st.phase === 'relearning') return 0.35;
  // review: base credit for graduating, plus streak and interval maturity.
  const streak = Math.min(1, st.correctStreak / 3);
  const maturity = Math.min(1, st.intervalDays / 10);
  const accuracy = st.answers > 0 ? st.correct / st.answers : 1;
  return Math.min(1, (0.55 + 0.25 * streak + 0.2 * maturity) * (0.6 + 0.4 * accuracy));
}

export function lessonMastery(lesson: Lesson, states: Map<string, CardState>): number {
  if (lesson.cardIds.length === 0) return 0;
  let sum = 0;
  for (const id of lesson.cardIds) sum += cardMastery(states.get(id));
  return sum / lesson.cardIds.length;
}

export function lessonReadiness(lesson: Lesson, states: Map<string, CardState>): number {
  if (lesson.cardIds.length === 0) return 0;
  let ready = 0;
  for (const id of lesson.cardIds) {
    const st = states.get(id);
    if (st && st.phase === 'review') ready++;
  }
  return ready / lesson.cardIds.length;
}

export function lessonComplete(lesson: Lesson, states: Map<string, CardState>): boolean {
  return (
    lessonMastery(lesson, states) >= MASTERY_THRESHOLD &&
    lessonReadiness(lesson, states) >= READINESS_THRESHOLD
  );
}

/**
 * Number of unlocked lessons (prefix of the unlock-ordered list). Lesson 0 is
 * always unlocked; lesson i+1 unlocks when lesson i is complete.
 */
export function unlockedLessonCount(lessonsInOrder: Lesson[], states: Map<string, CardState>): number {
  let unlocked = 1;
  for (let i = 0; i < lessonsInOrder.length - 1; i++) {
    if (lessonComplete(lessonsInOrder[i], states)) unlocked = i + 2;
    else break;
  }
  return Math.min(unlocked, lessonsInOrder.length);
}

/** Average accuracy per concept; low values mark weak topics. */
export interface WeakTopic {
  conceptId: string;
  accuracy: number;
  lapses: number;
  answers: number;
}

export function weakTopics(
  conceptCards: Map<string, string[]>, // conceptId -> cardIds
  states: Map<string, CardState>,
  minAnswers = 2,
): WeakTopic[] {
  const out: WeakTopic[] = [];
  for (const [conceptId, cardIds] of conceptCards) {
    let answers = 0, correct = 0, lapses = 0;
    for (const id of cardIds) {
      const st = states.get(id);
      if (!st) continue;
      answers += st.answers;
      correct += st.correct;
      lapses += st.lapses;
    }
    if (answers < minAnswers) continue;
    const accuracy = correct / answers;
    if (accuracy < 0.75 || lapses >= 2) out.push({ conceptId, accuracy, lapses, answers });
  }
  return out.sort((a, b) => a.accuracy - b.accuracy);
}

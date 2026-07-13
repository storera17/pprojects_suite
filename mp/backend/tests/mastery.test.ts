import { describe, expect, it } from 'vitest';
import { cardMastery, lessonComplete, lessonMastery, unlockedLessonCount, weakTopics } from '../src/core/mastery';
import { newCardState } from '../src/core/scheduler';
import type { CardState, Lesson } from '../src/core/types';

const lesson = (id: string, cardIds: string[]): Lesson => ({
  id, subdeckId: 's', deckId: 'd', title: id, order: 0, unlockIndex: 0, conceptIds: [], cardIds,
});

const mastered = (id: string): CardState => ({
  ...newCardState(id), phase: 'review', intervalDays: 15, correctStreak: 4, answers: 5, correct: 5, due: 0,
});

describe('Mastery calculation', () => {
  it('new cards have zero mastery; review cards approach 1.0', () => {
    expect(cardMastery(undefined)).toBe(0);
    expect(cardMastery(newCardState('c'))).toBe(0);
    expect(cardMastery(mastered('c'))).toBeGreaterThan(0.9);
  });

  it('mastery rises with streak and interval maturity', () => {
    const young: CardState = { ...mastered('c'), intervalDays: 1, correctStreak: 1 };
    expect(cardMastery(young)).toBeLessThan(cardMastery(mastered('c')));
  });

  it('lesson mastery averages its cards', () => {
    const l = lesson('L', ['a', 'b']);
    const states = new Map([['a', mastered('a')], ['b', newCardState('b')]]);
    const m = lessonMastery(l, states);
    expect(m).toBeGreaterThan(0.4);
    expect(m).toBeLessThan(0.6);
  });
});

describe('Lesson unlocking (90% mastery + review readiness)', () => {
  const l1 = lesson('L1', ['a', 'b', 'c']);
  const l2 = lesson('L2', ['d', 'e']);
  const l3 = lesson('L3', ['f']);

  it('only the first lesson is unlocked at the start', () => {
    expect(unlockedLessonCount([l1, l2, l3], new Map())).toBe(1);
  });

  it('unlocks the next lesson once the previous is mastered AND review-ready', () => {
    const states = new Map([['a', mastered('a')], ['b', mastered('b')], ['c', mastered('c')]]);
    expect(lessonComplete(l1, states)).toBe(true);
    expect(unlockedLessonCount([l1, l2, l3], states)).toBe(2);
  });

  it('90% mastery alone is not enough without readiness', () => {
    // two mastered, one still in learning → readiness 2/3 < 80%
    const states = new Map<string, CardState>([
      ['a', mastered('a')], ['b', mastered('b')],
      ['c', { ...mastered('c'), phase: 'learning' }],
    ]);
    expect(unlockedLessonCount([l1, l2], states)).toBe(1);
  });

  it('unlock chain stops at the first incomplete lesson', () => {
    const states = new Map([
      ['a', mastered('a')], ['b', mastered('b')], ['c', mastered('c')],
      // L2 untouched
    ]);
    expect(unlockedLessonCount([l1, l2, l3], states)).toBe(2);
  });
});

describe('Weak topic detection', () => {
  it('flags concepts with low accuracy or repeated lapses', () => {
    const conceptCards = new Map([
      ['weak', ['w1', 'w2']],
      ['strong', ['s1']],
    ]);
    const states = new Map<string, CardState>([
      ['w1', { ...mastered('w1'), answers: 6, correct: 2, lapses: 3 }],
      ['w2', { ...mastered('w2'), answers: 4, correct: 2, lapses: 1 }],
      ['s1', { ...mastered('s1'), answers: 8, correct: 8, lapses: 0 }],
    ]);
    const weak = weakTopics(conceptCards, states);
    expect(weak.map((w) => w.conceptId)).toContain('weak');
    expect(weak.map((w) => w.conceptId)).not.toContain('strong');
    expect(weak[0].accuracy).toBeLessThan(0.75);
  });
});

import { describe, expect, it } from 'vitest';
import { answerCard, buildQueue, newCardAllowance, newCardState, previewIntervals, SCHED } from '../src/core/scheduler';
import type { CardState } from '../src/core/types';

const NOW = Date.UTC(2026, 5, 12, 15, 0, 0);
const MIN = 60_000;
const DAY = 86_400_000;

describe('Spaced repetition scheduling', () => {
  it('new card enters learning on first answer', () => {
    const s = answerCard(newCardState('c1'), 'good', NOW);
    expect(s.phase).toBe('learning');
    expect(s.due - NOW).toBe(10 * MIN); // second learning step
  });

  it('again restarts the learning steps', () => {
    let s = answerCard(newCardState('c1'), 'good', NOW);
    s = answerCard(s, 'again', NOW + 10 * MIN);
    expect(s.phase).toBe('learning');
    expect(s.stepIndex).toBe(0);
    expect(s.due - (NOW + 10 * MIN)).toBe(1 * MIN);
  });

  it('good through all steps graduates to review at 1 day', () => {
    let s = answerCard(newCardState('c1'), 'good', NOW);
    s = answerCard(s, 'good', NOW + 10 * MIN);
    expect(s.phase).toBe('review');
    expect(s.intervalDays).toBe(SCHED.graduatingIntervalDays);
  });

  it('easy on a learning card graduates immediately at 4 days', () => {
    const s = answerCard(newCardState('c1'), 'easy', NOW);
    expect(s.phase).toBe('review');
    expect(s.intervalDays).toBe(SCHED.easyIntervalDays);
  });

  it('review-good multiplies the interval by ease', () => {
    let s: CardState = { ...newCardState('c1'), phase: 'review', intervalDays: 10, ease: 2.5, due: NOW };
    s = answerCard(s, 'good', NOW);
    expect(s.intervalDays).toBeGreaterThanOrEqual(10 * 2.5 * (1 - SCHED.fuzz));
    expect(s.intervalDays).toBeLessThanOrEqual(10 * 2.5 * (1 + SCHED.fuzz));
    expect(s.ease).toBe(2.5); // good leaves ease unchanged
  });

  it('hard shrinks growth and reduces ease; easy boosts both', () => {
    const base: CardState = { ...newCardState('c1'), phase: 'review', intervalDays: 10, ease: 2.5, due: NOW };
    const hard = answerCard(base, 'hard', NOW);
    expect(hard.ease).toBeCloseTo(2.35, 5);
    expect(hard.intervalDays).toBeLessThan(15);
    const easy = answerCard(base, 'easy', NOW);
    expect(easy.ease).toBeCloseTo(2.65, 5);
    expect(easy.intervalDays).toBeGreaterThan(hard.intervalDays);
  });

  it('again on a review card lapses to relearning, halves interval, drops ease', () => {
    const base: CardState = { ...newCardState('c1'), phase: 'review', intervalDays: 20, ease: 2.5, due: NOW };
    const s = answerCard(base, 'again', NOW);
    expect(s.phase).toBe('relearning');
    expect(s.lapses).toBe(1);
    expect(s.intervalDays).toBe(10);
    expect(s.ease).toBeCloseTo(2.3, 5);
    expect(s.due - NOW).toBe(10 * MIN);
  });

  it('ease never drops below the floor', () => {
    let s: CardState = { ...newCardState('c1'), phase: 'review', intervalDays: 5, ease: 1.32, due: NOW };
    s = answerCard(s, 'again', NOW);
    expect(s.ease).toBe(SCHED.minEase);
  });

  it('intervals grow across repeated good answers', () => {
    let s = answerCard(newCardState('c1'), 'easy', NOW);
    let t = NOW;
    const seen: number[] = [];
    for (let i = 0; i < 5; i++) {
      t = s.due;
      s = answerCard(s, 'good', t);
      seen.push(s.intervalDays);
    }
    for (let i = 1; i < seen.length; i++) expect(seen[i]).toBeGreaterThan(seen[i - 1]);
  });
});

describe('Review button behavior (previews)', () => {
  it('shows interval previews for a new card', () => {
    const p = previewIntervals(newCardState('c1'), NOW);
    expect(p.again).toBe('1m');
    expect(p.good).toBe('10m');
    expect(p.easy).toBe('4d');
  });

  it('shows day previews for a mature review card', () => {
    const s: CardState = { ...newCardState('c1'), phase: 'review', intervalDays: 10, ease: 2.5, due: NOW };
    const p = previewIntervals(s, NOW);
    expect(p.again).toBe('10m');
    expect(parseInt(p.good)).toBeGreaterThanOrEqual(23);
    expect(parseInt(p.easy)).toBeGreaterThan(parseInt(p.good));
  });
});

describe('Queue building and automatic pacing', () => {
  it('orders learning before review, introduces new cards lesson-by-lesson', () => {
    const states = new Map<string, CardState>();
    states.set('L1', { ...newCardState('L1'), phase: 'learning', due: NOW - MIN });
    states.set('R1', { ...newCardState('R1'), phase: 'review', due: NOW - DAY });
    const q = buildQueue(states, ['L1', 'R1', 'N1', 'N2', 'N3'], NOW, 0);
    expect(q.learning).toEqual(['L1']);
    expect(q.review).toEqual(['R1']);
    expect(q.newCards.slice(0, 2)).toEqual(['N1', 'N2']); // in lesson order
  });

  it('throttles new cards as review load grows (no manual limit)', () => {
    expect(newCardAllowance(0, 0)).toBe(20);
    expect(newCardAllowance(200, 0)).toBe(4); // floor
    expect(newCardAllowance(0, 18)).toBe(2);
    expect(newCardAllowance(0, 25)).toBe(0);
  });

  it('does not surface cards that are not yet due', () => {
    const states = new Map<string, CardState>();
    states.set('R1', { ...newCardState('R1'), phase: 'review', due: NOW + DAY });
    const q = buildQueue(states, [], NOW, 0);
    expect(q.review).toEqual([]);
  });
});

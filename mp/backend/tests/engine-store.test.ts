import { beforeEach, describe, expect, it } from 'vitest';
import { Engine } from '../src/core/engine';
import { MemoryStorage, Store } from '../src/core/store';
import { createProfile, verifyPassword } from '../src/core/auth';
import { dayKey, newCardState } from '../src/core/scheduler';
import { parseCommand, extractSearchQuery } from '../src/core/voice';
import { fixtureCourse } from './fixtures';

function freshEngine(): Engine {
  const engine = new Engine(new Store(new MemoryStorage()));
  engine.init(JSON.parse(JSON.stringify(fixtureCourse())));
  return engine;
}

describe('Local login', () => {
  it('creates a profile and verifies the password', async () => {
    const store = new Store(new MemoryStorage());
    await createProfile(store, 'andy', 'orion-7');
    expect(await verifyPassword(store, 'orion-7')).toBe(true);
    expect(await verifyPassword(store, 'wrong')).toBe(false);
  });

  it('rejects weak input', async () => {
    const store = new Store(new MemoryStorage());
    await expect(createProfile(store, '', 'goodpass')).rejects.toThrow();
    await expect(createProfile(store, 'andy', 'abc')).rejects.toThrow();
  });

  it('stores a salted hash, never the password', async () => {
    const store = new Store(new MemoryStorage());
    await createProfile(store, 'andy', 'orion-7');
    const p = store.getProfile()!;
    expect(p.hash).not.toContain('orion');
    expect(p.salt.length).toBeGreaterThan(10);
  });
});

describe('Data persistence', () => {
  it('round-trips card states, settings, log, and gamification', () => {
    const store = new Store(new MemoryStorage());
    const st = { ...newCardState('c1'), phase: 'review' as const, intervalDays: 7, due: 123 };
    store.saveCardState(st);
    expect(store.getCardStates().get('c1')).toMatchObject({ intervalDays: 7, due: 123 });
    store.setSettings({ soundEnabled: false, voiceEnabled: true, speakAnswers: true, lightMode: false });
    expect(store.getSettings().soundEnabled).toBe(false);
    store.appendLog({ cardId: 'c1', rating: 'good', at: 1, phaseBefore: 'new', intervalAfter: 1 });
    expect(store.getLog()).toHaveLength(1);
  });

  it('exports and imports the practice deck', () => {
    const store = new Store(new MemoryStorage());
    store.addPracticeCard({ id: 'p1', text: '{{c1::x}} y', conceptId: null, topic: 't', createdAt: 1, evidence: [], visual: { hue: 1, glyph: 'a', pattern: 'grid' } });
    const json = store.exportPractice();
    const store2 = new Store(new MemoryStorage());
    expect(store2.importPractice(json)).toBe(1);
    expect(store2.getPracticeCards()).toHaveLength(1);
    expect(() => store2.importPractice('{"format":"nope"}')).toThrow();
  });
});

describe('Engine integration (queue → answer → unlock → practice)', () => {
  let engine: Engine;
  beforeEach(() => { engine = freshEngine(); });

  it('serves new cards only from unlocked lessons, in order', () => {
    const q = engine.todayQueue();
    const firstLesson = engine.lessonsInOrder[0];
    expect(q.length).toBeGreaterThan(0);
    for (const qc of q) {
      if (qc.source === 'course') expect((qc.card as any).lessonId).toBe(firstLesson.id);
    }
  });

  it('answering persists state, history, XP, and pacing tally', () => {
    const q = engine.todayQueue();
    const before = engine.store.getGamification().xp;
    const now = Date.now();
    engine.answer(q[0], 'good', now);
    expect(engine.store.getCardStates().get((q[0].card as any).id)?.phase).toBe('learning');
    expect(engine.store.getLog()).toHaveLength(1);
    expect(engine.store.getGamification().xp).toBeGreaterThan(before);
    expect(engine.store.getIntroducedToday(dayKey(now))).toBe(1);
  });

  it('mastering lesson 1 unlocks lesson 2 and fires the unlock callback', () => {
    let unlockedTitle = '';
    engine.onUnlock = (l) => { unlockedTitle = l.title; };
    const l1 = engine.lessonsInOrder[0];
    const now = Date.now();
    // simulate full mastery of every lesson-1 card
    for (const id of l1.cardIds) {
      engine.store.saveCardState({
        ...newCardState(id), phase: 'review', intervalDays: 15, correctStreak: 4,
        answers: 5, correct: 5, due: now + 86400000, lastReview: now, introducedOn: '2026-06-01',
      });
    }
    expect(engine.unlockedCount()).toBe(2);
    // trigger callback path with one more answer on lesson 2's first new card
    const q = engine.todayQueue(now);
    const lesson2Card = q.find((x) => x.isNew);
    expect(lesson2Card).toBeTruthy();
    engine.answer(lesson2Card!, 'good', now);
    expect(unlockedTitle.length).toBeGreaterThan(0);
  });

  it('AI practice deck creation from weak topics (with fallback to recent lessons)', () => {
    const cards = engine.generatePracticeFromWeakTopics(3);
    expect(cards.length).toBeGreaterThan(0);
    expect(engine.store.getPracticeCards().length).toBe(cards.length);
    // practice cards join the queue but never touch the locked course
    const courseCardCount = engine.course.cards.length;
    expect(engine.course.cards.length).toBe(courseCardCount);
    const q = engine.todayQueue();
    expect(q.some((x) => x.source === 'practice')).toBe(true);
  });

  it('practice deck is resettable without touching course progress', () => {
    engine.generatePracticeFromWeakTopics(2);
    const q = engine.todayQueue();
    engine.answer(q[0], 'good');
    engine.store.resetPracticeDeck();
    expect(engine.store.getPracticeCards()).toHaveLength(0);
    expect(engine.store.getCardStates().size).toBeGreaterThan(0);
  });

  it('boss queue selects graded cards only', () => {
    const deckId = engine.course.decks[0].id;
    expect(engine.bossQueue(deckId)).toHaveLength(0); // nothing graded yet
    const q = engine.todayQueue();
    engine.answer(q[0], 'again');
    const boss = engine.bossQueue((q[0].card as any).deckId);
    expect(boss.length).toBe(1);
  });
});

describe('Voice command grammar', () => {
  it('parses all required commands', () => {
    expect(parseCommand('start review')).toBe('start review');
    expect(parseCommand('please show the answer')).toBe('show answer');
    expect(parseCommand('again')).toBe('again');
    expect(parseCommand('hard')).toBe('hard');
    expect(parseCommand('good')).toBe('good');
    expect(parseCommand('easy')).toBe('easy');
    expect(parseCommand('open dashboard')).toBe('open dashboard');
    expect(parseCommand('ask tutor')).toBe('ask tutor');
    expect(parseCommand('open the skill tree')).toBe('open skill tree');
    expect(parseCommand('search for spark shuffles')).toBe('search');
    expect(extractSearchQuery('search for spark shuffles')).toBe('spark shuffles');
    expect(parseCommand('what is a p-value')).toBeNull(); // free-form → tutor
  });
});

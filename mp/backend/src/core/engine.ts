// Engine: binds the bundled course, persistence, scheduler, mastery, and
// gamification into one API the UI consumes.
import type { Card, CardState, Course, Lesson, PracticeCard, Rating } from './types';
import { answerCard, buildQueue, dayKey, isDue, newCardState, previewIntervals } from './scheduler';
import { cardMastery, lessonComplete, lessonMastery, lessonReadiness, unlockedLessonCount, weakTopics } from './mastery';
import type { WeakTopic } from './mastery';
import { recordReview, type BadgeDef } from './gamification';
import { Store } from './store';
import { SearchIndex } from './search';
import { Tutor } from './tutor';

export interface QueueCard {
  card: Card | PracticeCard;
  state: CardState;
  source: 'course' | 'practice';
  isNew: boolean;
}

export class Engine {
  course!: Course;
  store: Store;
  search!: SearchIndex;
  tutor!: Tutor;
  cardById = new Map<string, Card>();
  lessonById = new Map<string, Lesson>();
  conceptById = new Map<string, Course['concepts'][number]>();
  lessonsInOrder: Lesson[] = [];
  conceptCards = new Map<string, string[]>();
  onUnlock: ((lesson: Lesson) => void) | null = null;
  onBadges: ((badges: BadgeDef[]) => void) | null = null;
  private unlockedBefore = 0;

  constructor(store?: Store) {
    this.store = store ?? new Store();
  }

  async load(courseUrl = './course/course.json'): Promise<void> {
    const res = await fetch(courseUrl);
    this.init((await res.json()) as Course);
  }

  /** Synchronous init for tests and preloaded data. */
  init(course: Course) {
    this.course = course;
    for (const c of course.cards) this.cardById.set(c.id, c);
    for (const l of course.lessons) this.lessonById.set(l.id, l);
    for (const c of course.concepts) {
      this.conceptById.set(c.id, c);
      this.conceptCards.set(c.id, c.cardIds);
    }
    this.lessonsInOrder = [...course.lessons].sort((a, b) => a.unlockIndex - b.unlockIndex);
    this.search = new SearchIndex(course);
    this.search.addPracticeCards(this.store.getPracticeCards());
    this.tutor = new Tutor(course);
    this.unlockedBefore = this.unlockedCount();
  }

  // --- unlocking ---
  unlockedCount(): number {
    return unlockedLessonCount(this.lessonsInOrder, this.store.getCardStates());
  }
  unlockedLessons(): Lesson[] {
    return this.lessonsInOrder.slice(0, this.unlockedCount());
  }
  isLessonUnlocked(lessonId: string): boolean {
    return this.unlockedLessons().some((l) => l.id === lessonId);
  }

  /** Cards of unlocked lessons in course order (new-card introduction order). */
  lessonOrderedCardIds(): string[] {
    return this.unlockedLessons().flatMap((l) => l.cardIds);
  }

  // --- queue ---
  todayQueue(now = Date.now()): QueueCard[] {
    const states = this.store.getCardStates();
    const q = buildQueue(states, this.lessonOrderedCardIds(), now, this.store.getIntroducedToday(dayKey(now)));
    const out: QueueCard[] = [];
    const push = (id: string, isNew: boolean) => {
      const card = this.cardById.get(id);
      if (!card) return;
      out.push({ card, state: states.get(id) ?? newCardState(id), source: 'course', isNew });
    };
    q.learning.forEach((id) => push(id, false));
    q.review.forEach((id) => push(id, false));
    q.newCards.forEach((id) => push(id, true));
    // due practice cards ride along after course learning/review
    const pStates = this.store.getPracticeStates();
    const practice = this.store.getPracticeCards();
    for (const pc of practice) {
      const st = pStates.get(pc.id) ?? newCardState(pc.id);
      if (st.phase === 'new' || isDue(st, now)) {
        out.push({ card: pc, state: st, source: 'practice', isNew: st.phase === 'new' });
      }
    }
    return out;
  }

  previewButtons(state: CardState, now = Date.now()) {
    return previewIntervals(state, now);
  }

  /** Grade a card: persists state, history, pacing tally, XP/streak/badges. */
  answer(qc: QueueCard, rating: Rating, now = Date.now()): CardState {
    const before = qc.state;
    const after = answerCard(before, rating, now);
    if (qc.source === 'course') {
      this.store.saveCardState(after);
      if (before.phase === 'new') this.store.bumpIntroduced(dayKey(now));
      this.store.appendLog({
        cardId: after.cardId, rating, at: now,
        phaseBefore: before.phase, intervalAfter: after.intervalDays,
      });
      const g = this.store.getGamification();
      const ctx = {
        lessonsCompleted: this.completedLessonCount(),
        decksCompleted: this.completedDeckCount(),
        reviewsToday: this.reviewsToday(now) + 1,
      };
      const { state, newBadges } = recordReview(g, rating, dayKey(now), ctx);
      this.store.setGamification(state);
      if (newBadges.length && this.onBadges) this.onBadges(newBadges);
      const unlockedNow = this.unlockedCount();
      if (unlockedNow > this.unlockedBefore && this.onUnlock) {
        this.onUnlock(this.lessonsInOrder[unlockedNow - 1]);
      }
      this.unlockedBefore = unlockedNow;
    } else {
      this.store.savePracticeState(after);
    }
    return after;
  }

  // --- stats ---
  reviewsToday(now = Date.now()): number {
    const key = dayKey(now);
    return this.store.getLog().filter((e) => dayKey(e.at) === key).length;
  }

  counts(now = Date.now()) {
    const states = this.store.getCardStates();
    let learning = 0, review = 0;
    for (const st of states.values()) {
      if (!isDue(st, now)) continue;
      if (st.phase === 'learning' || st.phase === 'relearning') learning++;
      else review++;
    }
    const q = buildQueue(states, this.lessonOrderedCardIds(), now, this.store.getIntroducedToday(dayKey(now)));
    return { learning, review, newCards: q.newCards.length };
  }

  /** Reviews coming due over the next `days` days (for the dashboard chart). */
  upcoming(days = 7, now = Date.now()): number[] {
    const states = this.store.getCardStates();
    const out = new Array(days).fill(0);
    for (const st of states.values()) {
      if (st.phase === 'new') continue;
      const inDays = Math.floor((st.due - now) / 86_400_000);
      if (inDays >= 0 && inDays < days) out[inDays]++;
    }
    return out;
  }

  lessonMastery(lessonId: string): number {
    const l = this.lessonById.get(lessonId);
    return l ? lessonMastery(l, this.store.getCardStates()) : 0;
  }
  lessonReadiness(lessonId: string): number {
    const l = this.lessonById.get(lessonId);
    return l ? lessonReadiness(l, this.store.getCardStates()) : 0;
  }
  deckMastery(deckId: string): number {
    const lessons = this.lessonsInOrder.filter((l) => l.deckId === deckId);
    if (!lessons.length) return 0;
    const states = this.store.getCardStates();
    return lessons.reduce((a, l) => a + lessonMastery(l, states), 0) / lessons.length;
  }
  completedLessonCount(): number {
    const states = this.store.getCardStates();
    return this.lessonsInOrder.filter((l) => lessonComplete(l, states)).length;
  }
  completedDeckCount(): number {
    const states = this.store.getCardStates();
    return this.course.decks.filter((d) =>
      this.lessonsInOrder.filter((l) => l.deckId === d.id).every((l) => lessonComplete(l, states)),
    ).length;
  }
  cardMasteryOf(cardId: string): number {
    return cardMastery(this.store.getCardStates().get(cardId));
  }

  weakTopics(limit = 8): (WeakTopic & { term: string; subdeckId: string })[] {
    return weakTopics(this.conceptCards, this.store.getCardStates())
      .slice(0, limit)
      .map((w) => {
        const c = this.conceptById.get(w.conceptId)!;
        return { ...w, term: c.displayTerm, subdeckId: c.subdeckId };
      });
  }

  // --- boss review: hardest mastered-area cards of a deck ---
  bossQueue(deckId: string, size = 12, now = Date.now()): QueueCard[] {
    const states = this.store.getCardStates();
    const candidates = this.course.cards
      .filter((c) => c.deckId === deckId)
      .map((c) => ({ card: c, state: states.get(c.id) }))
      .filter((x): x is { card: Card; state: CardState } => Boolean(x.state && x.state.phase !== 'new'))
      .sort((a, b) => (b.state.lapses - a.state.lapses) || (a.state.ease - b.state.ease))
      .slice(0, size);
    void now;
    return candidates.map(({ card, state }) => ({ card, state, source: 'course' as const, isNew: false }));
  }

  // --- AI Practice deck ---
  generatePracticeFromWeakTopics(maxConcepts = 4): PracticeCard[] {
    const weak = this.weakTopics(maxConcepts);
    const ids = weak.length
      ? weak.map((w) => w.conceptId)
      : this.unlockedLessons().slice(-1).flatMap((l) => l.conceptIds.slice(0, maxConcepts));
    const cards = this.tutor.generatePractice(ids);
    for (const c of cards) this.store.addPracticeCard(c);
    this.search.addPracticeCards(this.store.getPracticeCards());
    return cards;
  }
}

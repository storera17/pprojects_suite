import React from 'react';
import { useApp } from '../App';
import type { Concept, Lesson } from '../../../../backend/src/core/types';

/** Library: decks → subdecks → lessons → concept mini-lessons. */
export function Library({ deckId, lessonId }: { deckId?: string; lessonId?: string }) {
  const { engine, nav } = useApp();

  /** Performs the if operation for this class. */
  if (lessonId) {
    const lesson = engine.lessonById.get(lessonId);
    if (lesson) return <LessonView lesson={lesson} />;
  }

  /** Performs the if operation for this class. */
  if (deckId) {
    const deck = engine.course.decks.find((d) => d.id === deckId);
    if (!deck) return null;
    const unlockedIds = new Set(engine.unlockedLessons().map((l) => l.id));
    return (
      <div>
        <div className="crumb" onClick={() => nav({ name: 'library' })}>← All decks</div>
        <h1 className="screen-title">{deck.title}</h1>
        <p className="screen-sub">{deck.tagline}</p>
        {deck.subdecks.map((sd) => (
          <div className="panel" key={sd.id} style={{ marginBottom: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
              <b>{sd.title}</b>
              <span className="chip">{'◆'.repeat(sd.difficulty)} {sd.domain}</span>
            </div>
            {sd.lessonIds.map((lid) => {
              const lesson = engine.lessonById.get(lid)!;
              const unlocked = unlockedIds.has(lid);
              const m = engine.lessonMastery(lid);
              return (
                <div className="deck-row" key={lid} onClick={() => unlocked && nav({ name: 'library', deckId, lessonId: lid })}>
                  <span className="lock">{unlocked ? (m >= 0.9 ? '◉' : '◈') : '🔒'}</span>
                  <div className="t">
                    <b style={{ color: unlocked ? undefined : 'var(--fg-dim)' }}>{lesson.title}</b>
                    <span>{lesson.conceptIds.length} concepts · {lesson.cardIds.length} cards</span>
                  </div>
                  <div className="m">
                    <div className={`bar ${m >= 0.9 ? 'green' : ''}`}><div style={{ width: `${m * 100}%` }} /></div>
                  </div>
                </div>
              );
            })}
            <button className="btn ghost" style={{ marginTop: 10 }} onClick={() => nav({ name: 'review', boss: deck.id })}>
              ⚔ Boss review — hardest cards of this deck
            </button>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div>
      <h1 className="screen-title">Course Library</h1>
      <p className="screen-sub">
        The locked MomentumProdigy course — {engine.course.meta.counts.concepts} concepts, {engine.course.meta.counts.cards} cards,
        generated from “Concepts to learn and include.xlsx”. Course content is read-only; the AI Practice deck is yours to edit.
      </p>
      <div className="panel">
        {engine.course.decks.map((d) => {
          const m = engine.deckMastery(d.id);
          const lessons = engine.lessonsInOrder.filter((l) => l.deckId === d.id);
          return (
            <div className="deck-row" key={d.id} onClick={() => nav({ name: 'library', deckId: d.id })}>
              <span className="lock">⬡</span>
              <div className="t">
                <b>{d.title}</b>
                <span>{d.tagline} · {lessons.length} lessons</span>
              </div>
              <div className="m"><div className="bar"><div style={{ width: `${m * 100}%` }} /></div></div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/** Detailed lesson reader that explains each concept before or between review sessions. */
function LessonView({ lesson }: { lesson: Lesson }) {
  const { engine, nav } = useApp();
  const deck = engine.course.decks.find((d) => d.id === lesson.deckId);
  const concepts = lesson.conceptIds
    .map((id) => engine.conceptById.get(id))
    .filter((c): c is Concept => Boolean(c));
  const m = engine.lessonMastery(lesson.id);
  const ready = engine.lessonReadiness(lesson.id);

  return (
    <div>
      <div className="crumb" onClick={() => nav({ name: 'library', deckId: lesson.deckId })}>← {deck?.title}</div>
      <h1 className="screen-title">{lesson.title}</h1>
      <p className="screen-sub">
        Mastery {Math.round(m * 100)}% · review-ready {Math.round(ready * 100)}% · unlocks the next lesson at 90% + 80% ready
      </p>
      <div style={{ display: 'flex', gap: 10, marginBottom: 18 }}>
        <button className="btn primary" onClick={() => nav({ name: 'review' })}>◈ Study due & new cards</button>
      </div>
      {concepts.map((c) => (
        <div className="panel concept-block" key={c.id}>
          <details open={concepts.length <= 3}>
            <summary>{c.displayTerm}</summary>
            <div className="mini">
              <p>{c.mini.explanation}</p>
              {c.mini.how && (<><div className="lbl">How it works</div><p>{c.mini.how}</p></>)}
              <div className="lbl">Why it matters</div>
              <p>{c.mini.why}</p>
              <div className="lbl">In the workplace</div>
              <p>{c.mini.workplace}</p>
              {c.mini.workedExample && (<><div className="lbl">Worked example</div><p>{c.mini.workedExample}</p></>)}
              {c.mini.keyTerms.length > 0 && (
                <>
                  <div className="lbl">Key terms</div>
                  <p>{c.mini.keyTerms.map((t) => <span className="chip" key={t} style={{ marginRight: 6 }}>{t}</span>)}</p>
                </>
              )}
              <div className="lbl">Common mistakes</div>
              <ul>{c.mini.mistakes.map((mk, i) => <li key={i}>{mk}</li>)}</ul>
              {c.mini.related.length > 0 && (<><div className="lbl">Connected concepts</div><p style={{ color: 'var(--fg-dim)' }}>{c.mini.related.join(' · ')}</p></>)}
              <details className="evidence">
                <summary>Sources / Evidence</summary>
                <ul>
                  {c.mini.sources.map((s, i) => (
                    <li key={i}><b>{s.title}</b> — <i>{s.kind}</i> · {s.ref}</li>
                  ))}
                </ul>
              </details>
              <div style={{ fontSize: 12, color: 'var(--fg-dim)', marginTop: 10 }}>
                {c.cardIds.length} cards · difficulty {'◆'.repeat(c.difficulty)}
              </div>
            </div>
          </details>
        </div>
      ))}
    </div>
  );
}

import React from 'react';
import { useApp } from '../App';

/**
 * Jarvis-style skill tree: each deck is a glowing branch node on a central
 * spine; its lessons orbit outward as small nodes — locked, unlocked, or
 * mastered. Clicking an unlocked lesson opens it in the Library.
 */
export function SkillTree() {
  const { engine, nav } = useApp();
  const decks = engine.course.decks;
  const unlockedIds = new Set(engine.unlockedLessons().map((l) => l.id));

  const colW = 230;
  const width = Math.max(900, decks.length * colW);
  const height = 640;

  return (
    <div>
      <h1 className="screen-title">Skill Tree</h1>
      <p className="screen-sub">
        The course unlocks lesson-by-lesson: master a lesson (≥90% mastery, review-ready) to power the next node.
      </p>
      <div className="tree-wrap panel" style={{ padding: 8 }}>
        <svg className="tree-svg" width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
          <defs>
            <linearGradient id="spine" x1="0" x2="1">
              <stop offset="0%" stopColor="#0e7d9e" /><stop offset="100%" stopColor="#7df9ff" />
            </linearGradient>
          </defs>
          {/* spine */}
          <line x1={40} y1={70} x2={width - 40} y2={70} stroke="url(#spine)" strokeWidth={2.5} opacity={0.8} />
          {decks.map((deck, di) => {
            const x = 60 + di * colW + colW / 2 - 40;
            const lessons = engine.lessonsInOrder.filter((l) => l.deckId === deck.id);
            const mastery = engine.deckMastery(deck.id);
            return (
              <g key={deck.id}>
                <circle cx={x} cy={70} r={16} fill="rgba(13,38,56,0.9)" stroke="#19b8e0" strokeWidth={2}
                  style={{ filter: `drop-shadow(0 0 ${6 + mastery * 10}px rgba(25,184,224,${0.3 + mastery * 0.5}))` }} />
                <text x={x} y={75} textAnchor="middle" fill="#7df9ff" fontSize="11">{Math.round(mastery * 100)}</text>
                <text x={x} y={40} textAnchor="middle" fill="#9be8f7" fontSize="11.5" style={{ letterSpacing: 1 }}>
                  {deck.title.length > 26 ? deck.title.slice(0, 25) + '…' : deck.title}
                </text>
                <line x1={x} y1={86} x2={x} y2={110} stroke="#3a7d96" strokeWidth={1.2} />
                {lessons.map((lesson, li) => {
                  const ly = 120 + li * Math.min(34, 500 / Math.max(1, lessons.length));
                  const unlocked = unlockedIds.has(lesson.id);
                  const m = engine.lessonMastery(lesson.id);
                  const done = m >= 0.9;
                  const color = done ? '#7dffb0' : unlocked ? '#7df9ff' : '#3a5566';
                  return (
                    <g
                      key={lesson.id}
                      className={`tree-node ${unlocked ? '' : 'locked'}`}
                      onClick={() => unlocked && nav({ name: 'library', deckId: deck.id, lessonId: lesson.id })}
                    >
                      {li > 0 && <line x1={x} y1={ly - 26} x2={x} y2={ly - 8} stroke="#28505f" strokeWidth={1} />}
                      <circle cx={x} cy={ly} r={done ? 8 : 6.5} fill={done ? 'rgba(125,255,176,0.25)' : 'rgba(13,38,56,0.9)'}
                        stroke={color} strokeWidth={1.6}
                        style={done ? { filter: 'drop-shadow(0 0 6px rgba(125,255,176,0.6))' } : undefined} />
                      {!unlocked && <text x={x} y={ly + 3.5} textAnchor="middle" fontSize="7" fill="#3a5566">✕</text>}
                      <title>{`${lesson.title} — mastery ${Math.round(m * 100)}%${unlocked ? '' : ' (locked)'}`}</title>
                      <text x={x + 14} y={ly + 4} fontSize="9.5" fill={unlocked ? '#7fa9bd' : '#3a5566'}>
                        {lesson.title.length > 24 ? lesson.title.slice(0, 23) + '…' : lesson.title}
                      </text>
                    </g>
                  );
                })}
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

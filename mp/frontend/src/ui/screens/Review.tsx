import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useApp } from '../App';
import type { Card, PracticeCard, Rating } from '../../../../backend/src/core/types';
import type { QueueCard } from '../../../../backend/src/core/engine';
import { parseCloze } from '../../../../backend/src/core/cloze';
import { parseCommand } from '../../../../backend/src/core/voice';
import { sfx } from '../../../../backend/src/core/audio';
import { occlusionSvg } from '../../../../backend/src/core/occlusion';

/** Handles the isCourseCard step in this module’s workflow. */
const isCourseCard = (c: Card | PracticeCard): c is Card => 'type' in c;

/** Renders cloze text either as blanks on the front or answers on the back. */
function ClozeView({ text, revealed }: { text: string; revealed: boolean }) {
  const segs = useMemo(() => parseCloze(text), [text]);
  return (
    <div className="cloze-text">
      {segs.map((s, i) =>
        s.type === 'text'
          ? <span key={i}>{s.text}</span>
          : revealed
            ? <span key={i} className="answer">{s.text}</span>
            : <span key={i} className="blank">{s.hint ?? '?'}</span>,
      )}
    </div>
  );
}

/** Study session screen that reveals cards, handles ratings, and applies scheduler updates. */
export function Review({ boss, onGlobalCommand }: { boss?: string; onGlobalCommand: (t: string) => boolean }) {
  const { engine, nav, settings, voice, speak, toast } = useApp();
  const [queue, setQueue] = useState<QueueCard[]>(() => (boss ? engine.bossQueue(boss) : engine.todayQueue()));
  const [idx, setIdx] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [doneCount, setDoneCount] = useState(0);
  const [explain, setExplain] = useState<string | null>(null);
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const stopRef = useRef<(() => void) | null>(null);
  const bossMissesRef = useRef(0);

  const current = queue[idx];

  const grade = (rating: Rating) => {
    if (!current || !revealed) return;
    engine.answer(current, rating, Date.now());
    if (rating === 'again') { sfx.again(); if (boss) bossMissesRef.current++; }
    else sfx.good();
    setExplain(null);
    setRevealed(false);
    setDoneCount((d) => d + 1);
    if (rating === 'again' && !boss) {
      // Failed cards return within the current session.
      setQueue((q) => [...q.slice(0, idx), ...q.slice(idx + 1), current && { ...current, state: engine.store.getCardStates().get((current.card as Card).id) ?? current.state }].filter(Boolean) as QueueCard[]);
    } else {
      setIdx((i) => i + 1);
    }
    if (boss && idx + 1 >= queue.length) {
      const g = engine.store.getGamification();
      if (bossMissesRef.current <= Math.ceil(queue.length * 0.2)) {
        engine.store.setGamification({ ...g, bossWins: g.bossWins + 1, xp: g.xp + 80 });
        toast('⚔ Boss review cleared — +80 XP', true);
        sfx.complete();
      }
    }
  };

  const reveal = () => {
    if (!revealed) { setRevealed(true); sfx.reveal(); }
  };

  // keyboard: space reveals, 1–4 grade
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.code === 'Space') { e.preventDefault(); reveal(); }
      if (revealed) {
        if (e.key === '1') grade('again');
        if (e.key === '2') grade('hard');
        if (e.key === '3') grade('good');
        if (e.key === '4') grade('easy');
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  const startVoice = () => {
    if (listening) { stopRef.current?.(); setListening(false); return; }
    setListening(true);
    stopRef.current = voice.listen(
      (text, final) => {
        setTranscript(text);
        if (!final) return;
        const cmd = parseCommand(text);
        if (cmd === 'show answer') reveal();
        else if (cmd === 'again' || cmd === 'hard' || cmd === 'good' || cmd === 'easy') grade(cmd);
        else if (cmd && onGlobalCommand(text)) { /* navigated away */ }
        setTranscript('');
      },
      () => setListening(false),
    );
  };
  useEffect(() => () => stopRef.current?.(), []);

  /** Performs the if operation for this class. */
  if (!current) {
    return (
      <div className="review-stage">
        <div className="panel done-burst">
          <div className="big">◉</div>
          <h1 className="screen-title">{doneCount > 0 ? 'Session complete' : 'All clear'}</h1>
          <p className="screen-sub">
            {doneCount > 0
              ? `${doneCount} cards reviewed. The scheduler has queued your next reviews.`
              : 'No cards are due right now. New cards unlock automatically as lessons progress.'}
          </p>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
            <button className="btn primary" onClick={() => nav({ name: 'dashboard' })}>Return to dashboard</button>
            <button className="btn" onClick={() => nav({ name: 'tree' })}>Open skill tree</button>
          </div>
        </div>
      </div>
    );
  }

  const card = current.card;
  const course = isCourseCard(card) ? card : null;
  const visual = card.visual;
  const previews = engine.previewButtons(current.state);
  const concept = course ? engine.conceptById.get(course.conceptId) : null;
  const diagram = course?.occlusion ? engine.course.diagrams[course.occlusion.diagramId] : null;
  const region = diagram?.regions.find((r) => r.id === course!.occlusion!.focusId);
  const evidence = isCourseCard(card) ? card.evidence : card.evidence;

  const cardStyle = {
    '--card-accent': `hsl(${visual.hue} 90% 70%)`,
    '--card-glow': `hsla(${visual.hue} 90% 60% / 0.18)`,
    '--card-border': `hsla(${visual.hue} 70% 60% / 0.35)`,
  } as React.CSSProperties;

  return (
    <div className="review-stage">
      <div className="qmeta">
        <span>{boss ? '⚔ BOSS REVIEW' : current.source === 'practice' ? '⟐ AI PRACTICE' : concept ? concept.displayTerm.slice(0, 60).toUpperCase() : ''}</span>
        <span>
          {idx + 1} / {queue.length} {current.isNew ? '· NEW' : `· ${current.state.phase.toUpperCase()}`}
          {settings.voiceEnabled && voice.available && (
            <button className={`btn ghost micbtn ${listening ? 'live' : ''}`} style={{ marginLeft: 10, width: 36, padding: 4 }} onClick={startVoice} title="Voice control">🎙</button>
          )}
        </span>
      </div>
      {listening && transcript && <div style={{ textAlign: 'center', color: 'var(--fg-dim)', fontSize: 12, marginBottom: 8 }}>“{transcript}”</div>}

      <div className="card3d">
        <div className={`cardface ${revealed ? 'revealed' : ''}`} style={cardStyle} key={`${card.id}-${revealed}`}>
          <span className="corner tl" style={{ color: 'var(--card-accent)' }}>{visual.glyph}</span>
          <span className="corner br" style={{ color: 'var(--card-accent)' }}>{visual.glyph}</span>
          <Pattern kind={visual.pattern} hue={visual.hue} />
          <div className="card-kind">
            {course
              ? course.type === 'occlusion' ? 'Image occlusion' : course.kind === 'applied' ? 'Applied scenario' : course.kind === 'mistake' ? 'Pitfall check' : 'Cloze recall'
              : 'AI practice · cloze'}
          </div>

          {course?.type === 'occlusion' && diagram && region ? (
            <div className="occ-wrap">
              <p style={{ marginTop: 0, fontSize: 14, color: 'var(--fg-dim)' }}>{course.prompt}</p>
              <div dangerouslySetInnerHTML={{ __html: occlusionSvg(diagram.svg, region, revealed) }} />
              {revealed && <p style={{ color: 'var(--green)', fontWeight: 600 }}>{course.occlusion!.answer}</p>}
            </div>
          ) : (
            <ClozeView text={(course ? course.text : (card as PracticeCard).text) ?? ''} revealed={revealed} />
          )}

          {revealed && (
            <>
              {explain && <div className="tutor-panel">{explain}</div>}
              <details className="evidence">
                <summary>Extra / Evidence — sources</summary>
                <ul>
                  {evidence.map((s, i) => <li key={i}><b>{s.title}</b> — <i>{s.kind}</i> · {s.ref}</li>)}
                </ul>
              </details>
            </>
          )}
        </div>
      </div>

      {!revealed ? (
        <div className="answer-row">
          <button className="btn primary" style={{ minWidth: 220, padding: '14px 0' }} onClick={reveal}>
            Show answer <span style={{ opacity: 0.6, fontSize: 12 }}>(space)</span>
          </button>
        </div>
      ) : (
        <>
          <div className="answer-row">
            <button className="gradebtn again" onClick={() => grade('again')}>Again<small>{previews.again} · 1</small></button>
            <button className="gradebtn hard" onClick={() => grade('hard')}>Hard<small>{previews.hard} · 2</small></button>
            <button className="gradebtn good" onClick={() => grade('good')}>Good<small>{previews.good} · 3</small></button>
            <button className="gradebtn easy" onClick={() => grade('easy')}>Easy<small>{previews.easy} · 4</small></button>
          </div>
          {course && (
            <div className="answer-row" style={{ marginTop: 8 }}>
              <button
                className="btn ghost"
                onClick={() => {
                  const text = engine.tutor.explainCard(course.id);
                  setExplain(text);
                  if (settings.speakAnswers) speak(text);
                }}
              >
                ⌬ Tutor: explain this answer
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

/** Faint per-card generative background pattern (Jarvis identity). */
function Pattern({ kind, hue }: { kind: string; hue: number }) {
  const stroke = `hsl(${hue} 80% 65%)`;
  const els: React.ReactNode[] = [];
  if (kind === 'rings') for (let i = 1; i <= 4; i++) els.push(<circle key={i} cx="85%" cy="20%" r={i * 38} fill="none" stroke={stroke} strokeWidth="1" />);
  else if (kind === 'grid') for (let i = 0; i < 8; i++) { els.push(<line key={`v${i}`} x1={`${i * 14}%`} y1="0" x2={`${i * 14}%`} y2="100%" stroke={stroke} strokeWidth="0.5" />); els.push(<line key={`h${i}`} x1="0" y1={`${i * 18}%`} x2="100%" y2={`${i * 18}%`} stroke={stroke} strokeWidth="0.5" />); }
  else if (kind === 'scan') for (let i = 0; i < 12; i++) els.push(<line key={i} x1="0" y1={`${i * 9}%`} x2="100%" y2={`${i * 9 + 4}%`} stroke={stroke} strokeWidth="0.6" />);
  else if (kind === 'hex') for (let i = 0; i < 5; i++) els.push(<polygon key={i} points="30,8 52,20 52,44 30,56 8,44 8,20" transform={`translate(${i * 90 + 480}, ${i % 2 === 0 ? 10 : 60}) scale(0.9)`} fill="none" stroke={stroke} strokeWidth="1" />);
  else if (kind === 'orbit') { els.push(<ellipse key="a" cx="80%" cy="80%" rx="180" ry="60" fill="none" stroke={stroke} strokeWidth="0.8" />); els.push(<ellipse key="b" cx="80%" cy="80%" rx="120" ry="110" fill="none" stroke={stroke} strokeWidth="0.8" />); }
  else for (let i = 1; i <= 3; i++) els.push(<circle key={i} cx="12%" cy="85%" r={i * 30} fill="none" stroke={stroke} strokeWidth="1" strokeDasharray="3 6" />);
  return <svg className="pattern" width="100%" height="100%">{els}</svg>;
}

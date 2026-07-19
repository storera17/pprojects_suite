import React from 'react';
import { useApp } from '../App';
import { levelForXp, BADGES } from '../../../../backend/src/core/gamification';

/** Reusable circular progress indicator for lesson mastery and dashboard metrics. */
function Ring({ pct, label, value }: { pct: number; label: string; value: string }) {
  const r = 52, c = 2 * Math.PI * r;
  return (
    <div className="ring">
      <svg width="124" height="124">
        <circle cx="62" cy="62" r={r} fill="none" stroke="rgba(127,169,189,0.15)" strokeWidth="8" />
        <circle
          cx="62" cy="62" r={r} fill="none" stroke="url(#rg)" strokeWidth="8" strokeLinecap="round"
          strokeDasharray={`${c * Math.min(1, pct)} ${c}`} style={{ transition: 'stroke-dasharray .8s cubic-bezier(.22,1,.36,1)' }}
        />
        <defs>
          <linearGradient id="rg"><stop offset="0%" stopColor="#0e7d9e" /><stop offset="100%" stopColor="#7df9ff" /></linearGradient>
        </defs>
      </svg>
      <div className="val"><b>{value}</b><span>{label}</span></div>
    </div>
  );
}

/** Home screen summarizing due work, mastery progress, weak topics, badges, and next study action. */
export function Dashboard() {
  const { engine, nav } = useApp();
  const counts = engine.counts();
  const g = engine.store.getGamification();
  const lvl = levelForXp(g.xp);
  const upcoming = engine.upcoming(7);
  const maxUp = Math.max(1, ...upcoming);
  const weak = engine.weakTopics(6);
  const unlocked = engine.unlockedCount();
  const totalLessons = engine.lessonsInOrder.length;
  const completed = engine.completedLessonCount();
  const practice = engine.store.getPracticeCards();
  const dueTotal = counts.learning + counts.review;
  const profile = engine.store.getProfile();
  const days = ['Today', '+1', '+2', '+3', '+4', '+5', '+6'];

  return (
    <div>
      <div className="dash-head">
        <div>
          <h1 className="screen-title">Command Center</h1>
          <p className="screen-sub">Operator {profile?.username} · Level {lvl.level} · {g.streakDays}-day streak</p>
        </div>
        <button className="btn primary" onClick={() => nav({ name: 'review' })}>
          ◈ Start Review {dueTotal + counts.newCards > 0 ? `(${dueTotal + counts.newCards})` : ''}
        </button>
      </div>

      <div className="grid cols-3">
        <div className="panel">
          <div className="statline">
            <div className="stat"><div className="num">{counts.review}</div><div className="lbl">Due reviews</div></div>
            <div className="stat amber"><div className="num">{counts.learning}</div><div className="lbl">Learning</div></div>
            <div className="stat green"><div className="num">{counts.newCards}</div><div className="lbl">New today</div></div>
          </div>
          <div style={{ marginTop: 16 }}>
            <div className="lbl" style={{ fontSize: 11, color: 'var(--fg-dim)', letterSpacing: 1.5, marginBottom: 6 }}>UPCOMING REVIEWS</div>
            <div className="upbar">
              {upcoming.map((v, i) => <div key={i} className="b" style={{ height: `${(v / maxUp) * 100}%` }} title={`${v} cards`} />)}
            </div>
            <div className="upbar-lbls">{days.map((d) => <span key={d}>{d}</span>)}</div>
          </div>
        </div>

        <div className="panel" style={{ display: 'flex', gap: 18, alignItems: 'center', justifyContent: 'space-around', flexWrap: 'wrap' }}>
          <Ring pct={completed / Math.max(1, totalLessons)} label="LESSONS MASTERED" value={`${completed}/${totalLessons}`} />
          <div>
            <div className="stat violet"><div className="num">{g.xp}</div><div className="lbl">XP · Level {lvl.level}</div></div>
            <div className="bar" style={{ width: 140, marginTop: 6 }}><div style={{ width: `${(lvl.into / lvl.needed) * 100}%` }} /></div>
            <div style={{ fontSize: 11, color: 'var(--fg-dim)', marginTop: 4 }}>{lvl.needed - lvl.into} XP to level {lvl.level + 1}</div>
            <div className="stat" style={{ marginTop: 14 }}><div className="num">{unlocked}</div><div className="lbl">Lessons unlocked</div></div>
          </div>
        </div>

        <div className="panel">
          <div className="lbl" style={{ fontSize: 11, color: 'var(--fg-dim)', letterSpacing: 1.5, marginBottom: 4 }}>WEAK TOPICS</div>
          {weak.length === 0 && <div style={{ color: 'var(--fg-dim)', fontSize: 13, padding: '12px 0' }}>No weak topics detected yet. Keep reviewing — MomentumProdigy tracks lapses and accuracy per concept.</div>}
          {weak.map((w) => (
            <div className="weak-item" key={w.conceptId}>
              <span>{w.term.slice(0, 46)}</span>
              <span className="pct">{Math.round(w.accuracy * 100)}%</span>
            </div>
          ))}
          {weak.length > 0 && (
            <button className="btn" style={{ marginTop: 10, width: '100%' }} onClick={() => nav({ name: 'practice' })}>
              ⟐ Generate AI practice for weak topics
            </button>
          )}
        </div>
      </div>

      <div className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="panel">
          <div className="lbl" style={{ fontSize: 11, color: 'var(--fg-dim)', letterSpacing: 1.5, marginBottom: 10 }}>DECK MASTERY</div>
          {engine.course.decks.map((d) => {
            const m = engine.deckMastery(d.id);
            return (
              <div key={d.id} style={{ marginBottom: 10, cursor: 'pointer' }} onClick={() => nav({ name: 'library', deckId: d.id })}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                  <span>{d.title}</span><span style={{ color: 'var(--fg-dim)' }}>{Math.round(m * 100)}%</span>
                </div>
                <div className="bar"><div style={{ width: `${m * 100}%` }} /></div>
              </div>
            );
          })}
        </div>

        <div className="panel">
          <div className="lbl" style={{ fontSize: 11, color: 'var(--fg-dim)', letterSpacing: 1.5, marginBottom: 10 }}>BADGES</div>
          <div className="badge-row">
            {BADGES.map((b) => (
              <div key={b.id} className={`badge ${g.badges.includes(b.id) ? 'earned' : ''}`} title={b.desc}>
                <span>{g.badges.includes(b.id) ? '★' : '☆'}</span>{b.title}
              </div>
            ))}
          </div>
          <div style={{ marginTop: 16, fontSize: 13, color: 'var(--fg-dim)' }}>
            AI Practice deck: {practice.length} cards · {g.reviewsTotal} total reviews · {g.bossWins} boss wins
          </div>
        </div>
      </div>
    </div>
  );
}

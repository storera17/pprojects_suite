import React, { useMemo, useState } from 'react';
import { useApp } from '../App';
import type { SearchHitType } from '../../../../backend/src/core/search';

const TYPES: { id: SearchHitType; label: string }[] = [
  { id: 'concept', label: 'Concepts' },
  { id: 'lesson', label: 'Lessons' },
  { id: 'deck', label: 'Decks' },
  { id: 'card', label: 'Cards' },
  { id: 'source', label: 'Sources' },
  { id: 'practice', label: 'AI Practice' },
];

/** Offline search screen across concepts, lessons, cards, sources, and practice cards. */
export function SearchScreen({ initialQuery }: { initialQuery?: string }) {
  const { engine, nav } = useApp();
  const [q, setQ] = useState(initialQuery ?? '');
  const [active, setActive] = useState<Set<SearchHitType>>(new Set(TYPES.map((t) => t.id)));

  const hits = useMemo(
    () => (q.trim() ? engine.search.search(q, 40, [...active]) : []),
    [q, active, engine],
  );

  const toggle = (t: SearchHitType) => {
    const next = new Set(active);
    if (next.has(t)) next.delete(t); else next.add(t);
    setActive(next);
  };

  const open = (hit: (typeof hits)[number]) => {
    if (hit.type === 'deck') nav({ name: 'library', deckId: hit.deckId });
    else if (hit.lessonId) nav({ name: 'library', deckId: hit.deckId, lessonId: hit.lessonId });
    else if (hit.type === 'practice') nav({ name: 'practice' });
  };

  return (
    <div>
      <h1 className="screen-title">Search</h1>
      <p className="screen-sub">Keyword + semantic search across the whole course — fully offline, powered by the local embedding index.</p>
      <div className="panel">
        <input
          type="text" placeholder="Search lessons, cards, sources, weak topics… (try “making models not overfit”)"
          value={q} onChange={(e) => setQ(e.target.value)} autoFocus
        />
        <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
          {TYPES.map((t) => (
            <button key={t.id} className={`chip ${active.has(t.id) ? 'on' : ''}`} style={{ cursor: 'pointer', background: 'none' }} onClick={() => toggle(t.id)}>
              {t.label}
            </button>
          ))}
        </div>
        <div style={{ marginTop: 12 }}>
          {q.trim() && hits.length === 0 && <div style={{ color: 'var(--fg-dim)', padding: '14px 0' }}>No matches.</div>}
          {hits.map((h) => (
            <div className="hit" key={`${h.type}-${h.id}`} onClick={() => open(h)}>
              <div className="ty">{h.type} · score {h.score.toFixed(2)}</div>
              <div className="ti">{h.title}</div>
              <div className="sn">{h.snippet}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

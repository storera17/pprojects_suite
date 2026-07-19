import React, { useEffect, useRef, useState } from 'react';
import { useApp } from '../App';
import { parseCommand } from '../../../../backend/src/core/voice';

/**
 * Standalone AI Tutor screen. Conversations are session-only by design —
 * nothing here is persisted (closing the screen or app clears history).
 */
export function TutorChat({ onGlobalCommand }: { onGlobalCommand: (t: string) => boolean }) {
  const { engine, settings, voice, speak, toast, nav } = useApp();
  const [turns, setTurns] = useState(engine.tutor.history);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const stopRef = useRef<(() => void) | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' });
  }, [turns, busy]);

  const send = async (text: string) => {
    const q = text.trim();
    if (!q || busy) return;
    setInput('');
    setBusy(true);
    setTurns([...engine.tutor.history, { role: 'user', text: q }]);
    const answer = await engine.tutor.ask(q);
    setTurns([...engine.tutor.history]);
    setBusy(false);
    if (settings.speakAnswers) speak(answer);
  };

  const startVoice = () => {
    if (listening) { stopRef.current?.(); setListening(false); return; }
    setListening(true);
    stopRef.current = voice.listen(
      (text, final) => {
        setInput(text);
        if (!final) return;
        const cmd = parseCommand(text);
        if (cmd && cmd !== 'ask tutor' && onGlobalCommand(text)) { setInput(''); return; }
        send(text);
      },
      () => setListening(false),
    );
  };
  useEffect(() => () => stopRef.current?.(), []);

  const makePractice = () => {
    const cards = engine.generatePracticeFromWeakTopics();
    toast(cards.length ? `⟐ ${cards.length} practice cards added to the AI Practice deck` : 'No weak topics yet — review more cards first.');
    if (cards.length) nav({ name: 'practice' });
  };

  return (
    <div>
      <h1 className="screen-title">AI Tutor</h1>
      <p className="screen-sub">
        Fully offline. Ask about any course concept — or broader analytics, data, and coding questions.
        Conversations are not saved after this session.
      </p>
      <div className="chat panel">
        <div className="chat-log" ref={logRef}>
          {turns.length === 0 && (
            <div className="msg tutor">
              Online. Ask me anything — “What is filter context?”, “gradient descent vs SGD”,
              “give me an example of difference-in-differences”, or “why does my model overfit?”.
              I can also generate practice cards for your weak topics.
            </div>
          )}
          {turns.map((t, i) => <div key={i} className={`msg ${t.role}`}>{t.text}</div>)}
          {busy && <div className="msg tutor">…</div>}
        </div>
        <div className="chat-input">
          {voice.available && settings.voiceEnabled && (
            <button className={`btn ghost micbtn ${listening ? 'live' : ''}`} onClick={startVoice} title="Voice input">🎙</button>
          )}
          <input
            type="text" placeholder="Ask MomentumProdigy…" value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send(input)}
          />
          <button className="btn primary" onClick={() => send(input)} disabled={busy}>Send</button>
          <button className="btn" onClick={makePractice} title="Generate practice cards from weak topics">⟐ Practice</button>
        </div>
      </div>
    </div>
  );
}

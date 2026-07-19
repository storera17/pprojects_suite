import React, { useState } from 'react';
import { useApp } from '../App';
import { biometricsSupported, enrollBiometrics } from '../../../../backend/src/core/auth';

/** Local settings and course metadata screen. */
export function SettingsScreen() {
  const { engine, settings, saveSettings, toast } = useApp();
  const profile = engine.store.getProfile();
  const [enrolled, setEnrolled] = useState(Boolean(profile?.webauthnId));
  const meta = engine.course.meta;

  const Toggle = ({ label, value, onChange, hint }: { label: string; value: boolean; onChange: (v: boolean) => void; hint?: string }) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid rgba(72,187,224,0.08)' }}>
      <div>
        <div style={{ fontSize: 14.5 }}>{label}</div>
        {hint && <div style={{ fontSize: 12, color: 'var(--fg-dim)' }}>{hint}</div>}
      </div>
      <button className={`chip ${value ? 'on' : ''}`} style={{ cursor: 'pointer', background: 'none', padding: '6px 14px' }} onClick={() => onChange(!value)}>
        {value ? 'ON' : 'OFF'}
      </button>
    </div>
  );

  return (
    <div>
      <h1 className="screen-title">System</h1>
      <p className="screen-sub">Local settings — nothing syncs, nothing leaves this device.</p>

      <div className="panel" style={{ marginBottom: 16 }}>
        <Toggle label="☀ Sun mode" hint="Light palette for studying outdoors in bright light" value={settings.lightMode ?? false} onChange={(v) => saveSettings({ ...settings, lightMode: v })} />
        <Toggle label="UI sounds" hint="Subtle Jarvis-style interface audio" value={settings.soundEnabled} onChange={(v) => saveSettings({ ...settings, soundEnabled: v })} />
        <Toggle label="Voice interaction" hint="Microphone commands and voice input" value={settings.voiceEnabled} onChange={(v) => saveSettings({ ...settings, voiceEnabled: v })} />
        <Toggle label="Speak tutor answers" hint="Text-to-speech for tutor responses and card explanations" value={settings.speakAnswers} onChange={(v) => saveSettings({ ...settings, speakAnswers: v })} />
      </div>

      <div className="panel" style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 14.5, marginBottom: 8 }}>Biometric unlock</div>
        {biometricsSupported() ? (
          enrolled ? (
            <div style={{ color: 'var(--green)', fontSize: 13 }}>⬡ Enrolled — Face ID / Touch ID / Windows Hello can unlock MomentumProdigy (and recover access if the password is forgotten).</div>
          ) : (
            <button className="btn" onClick={async () => { const ok = await enrollBiometrics(engine.store); setEnrolled(ok); toast(ok ? 'Biometric unlock enrolled.' : 'Enrollment failed or was cancelled.'); }}>
              Enroll Face ID / Touch ID / Windows Hello
            </button>
          )
        ) : (
          <div style={{ color: 'var(--fg-dim)', fontSize: 13 }}>Platform authenticator not available in this environment — password unlock remains active.</div>
        )}
      </div>

      <div className="panel">
        <div style={{ fontSize: 14.5, marginBottom: 8 }}>About this course</div>
        <div style={{ fontSize: 13, color: 'var(--fg-dim)', lineHeight: 1.8 }}>
          {meta.name}<br />
          Generated {new Date(meta.generatedAt).toLocaleString()} · {meta.counts.decks} decks · {meta.counts.subdecks} subdecks · {meta.counts.lessons} lessons<br />
          {meta.counts.concepts} concepts · {meta.counts.cards} cards ({meta.counts.clozeCards} cloze, {meta.counts.occlusionCards} image occlusion)<br />
          The course is locked by design; study progress lives only on this device.<br />
          Practice-deck cloze text uses the portable {'{{c1::…}}'} syntax included in JSON exports.
        </div>
      </div>
    </div>
  );
}

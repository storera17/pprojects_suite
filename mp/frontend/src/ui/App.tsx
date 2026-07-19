import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Engine } from '../../../backend/src/core/engine';
import { setMuted, sfx } from '../../../backend/src/core/audio';
import { webSpeechBridge, parseCommand, extractSearchQuery } from '../../../backend/src/core/voice';
import type { Settings } from '../../../backend/src/core/store';
import { AppCtx, type AppContextValue, useApp } from '../app/AppContext';
import { NAV_ITEMS } from '../app/navigation';
import type { Route } from '../app/routes';
import { Toasts, type Toast } from '../app/toasts';
import { Login } from './screens/Login';
import { Dashboard } from './screens/Dashboard';
import { SkillTree } from './screens/SkillTree';
import { Library } from './screens/Library';
import { Review } from './screens/Review';
import { TutorChat } from './screens/TutorChat';
import { SearchScreen } from './screens/SearchScreen';
import { Practice } from './screens/Practice';
import { SettingsScreen } from './screens/SettingsScreen';

export { useApp };

/** Top-level React shell: bootstraps the engine, controls auth/ready states, and renders the active route. */
export function App() {
  // The Engine is intentionally stored in a ref so React re-renders do not
  // recreate the course, scheduler, search index, tutor, or local storage API.
  const engineRef = useRef(new Engine());

  // `phase` is the app lifecycle gate: loading course data → login/unlock →
  // normal app. Keeping this explicit is easier to reason about than several
  // unrelated booleans.
  const [phase, setPhase] = useState<'boot' | 'auth' | 'ready'>('boot');

  // `route` is the lightweight in-app navigation state. There is no server
  // routing because MomentumProdigy is designed to run offline.
  const [route, setRoute] = useState<Route>({ name: 'dashboard' });

  // Toasts are short-lived messages for unlocks, badges, saves, and errors.
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Settings are initialized from local persistence and mirrored back through
  // `saveSettings` below so every screen sees the same preferences.
  const [settings, setSettings] = useState<Settings>(() => engineRef.current.store.getSettings());

  // `tick` has no visible value; bumping it forces screens to refresh after
  // local-only data changes such as editing the practice deck.
  const [, setTick] = useState(0);

  // Voice is created once because speech-recognition setup can be expensive or
  // platform-specific.
  const voice = useMemo(() => webSpeechBridge(), []);

  /** Shows a temporary notification and automatically removes it after a delay. */
  const toast = (text: string, gold = false) => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, text, gold }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4200);
  };

  useEffect(() => {
    setMuted(!settings.soundEnabled);
  }, [settings.soundEnabled]);

  useEffect(() => {
    document.documentElement.dataset.theme = settings.lightMode ? 'light' : '';
  }, [settings.lightMode]);

  useEffect(() => {
    const engine = engineRef.current;
    engine.load().then(() => {
      engine.onUnlock = (lesson) => {
        sfx.unlock();
        toast(`⟁ Lesson unlocked: ${lesson.title}`, true);
      };
      engine.onBadges = (badges) => {
        sfx.levelup();
        for (const b of badges) toast(`★ Badge earned — ${b.title}: ${b.desc}`, true);
      };
      setPhase('auth');
    }).catch((e) => toast(`Failed to load course: ${e}`));
  }, []);

  const ctx: AppContextValue = {
    engine: engineRef.current,
    route,
    nav: (r) => { sfx.tap(); setRoute(r); },
    toast,
    settings,
    saveSettings: (s) => { setSettings(s); engineRef.current.store.setSettings(s); },
    voice,
    speak: (text) => { if (settings.voiceEnabled) voice.speak(text); },
    bump: () => setTick((t) => t + 1),
  };

  /** Handles navigation/settings voice commands that are valid from most screens. */
  const handleGlobalCommand = (transcript: string): boolean => {
    const cmd = parseCommand(transcript);
    if (!cmd) return false;
    switch (cmd) {
      case 'open dashboard': setRoute({ name: 'dashboard' }); return true;
      case 'open skill tree': setRoute({ name: 'tree' }); return true;
      case 'ask tutor': setRoute({ name: 'tutor' }); return true;
      case 'start review': setRoute({ name: 'review' }); return true;
      case 'search': setRoute({ name: 'search', query: extractSearchQuery(transcript) }); return true;
      case 'mute': ctx.saveSettings({ ...settings, soundEnabled: false }); return true;
      case 'unmute': ctx.saveSettings({ ...settings, soundEnabled: true }); return true;
      default: return false;
    }
  };

  /** Performs the if operation for this class. */
  if (phase === 'boot') {
    return (
      <div className="login-wrap">
        <div className="login panel">
          <img className="orb" src="./icon.svg" alt="" />
          <h1>MomentumProdigy</h1>
          <div className="tag">INITIALIZING KNOWLEDGE CORE…</div>
        </div>
      </div>
    );
  }

  /** Performs the if operation for this class. */
  if (phase === 'auth') {
    return (
      <AppCtx.Provider value={ctx}>
        <Login onUnlocked={() => { setPhase('ready'); sfx.complete(); }} />
      </AppCtx.Provider>
    );
  }

  return (
    <AppCtx.Provider value={ctx}>
      <div className="scanline" />
      <div className="app">
        <nav className="rail">
          <img className="logo" src="./icon.svg" alt="MomentumProdigy" />
          {NAV_ITEMS.map((n) => (
            <button
              key={n.route}
              className={`railbtn ${route.name === n.route ? 'active' : ''}`}
              onClick={() => ctx.nav({ name: n.route } as Route)}
            >
              <span className="ic">{n.ic}</span>
              {n.label}
            </button>
          ))}
        </nav>
        <main className="main">
          {route.name === 'dashboard' && <Dashboard />}
          {route.name === 'tree' && <SkillTree />}
          {route.name === 'library' && <Library deckId={route.deckId} lessonId={route.lessonId} />}
          {route.name === 'review' && <Review boss={route.boss} onGlobalCommand={handleGlobalCommand} />}
          {route.name === 'tutor' && <TutorChat onGlobalCommand={handleGlobalCommand} />}
          {route.name === 'search' && <SearchScreen initialQuery={route.query} />}
          {route.name === 'practice' && <Practice />}
          {route.name === 'settings' && <SettingsScreen />}
        </main>
      </div>
      <Toasts toasts={toasts} />
    </AppCtx.Provider>
  );
}

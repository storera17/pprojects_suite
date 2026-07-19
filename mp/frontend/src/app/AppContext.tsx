import { createContext, useContext } from 'react';
import type { Engine } from '../../../backend/src/core/engine';
import type { Settings } from '../../../backend/src/core/store';
import type { VoiceBridge } from '../../../backend/src/core/voice';
import type { Route } from './routes';

/** Shared app services made available to every screen through React context. */
export interface AppContextValue {
  engine: Engine;
  route: Route;
  nav: (route: Route) => void;
  toast: (text: string, gold?: boolean) => void;
  settings: Settings;
  saveSettings: (settings: Settings) => void;
  voice: VoiceBridge;
  speak: (text: string) => void;
  bump: () => void;
}

/** React context object that carries the engine, navigation, settings, and utility actions. */
export const AppCtx = createContext<AppContextValue | null>(null);

/** Convenience hook that gives screens access to the shared app services and fails fast if misused. */
export function useApp() {
  const ctx = useContext(AppCtx);
  if (!ctx) throw new Error('useApp must be used inside AppCtx.Provider');
  return ctx;
}
=
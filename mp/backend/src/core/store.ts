// Local-only persistence. Backed by localStorage in the app (Tauri/Capacitor
// WebViews persist it per-install) with an in-memory fallback for tests.
// Nothing ever leaves the device.
import type { CardState, PracticeCard, ReviewLogEntry } from './types';
import type { GamificationState } from './gamification';
import { initialGamification } from './gamification';

export interface StorageAdapter {
  get(key: string): string | null;
  set(key: string, value: string): void;
  remove(key: string): void;
}

export class MemoryStorage implements StorageAdapter {
  private map = new Map<string, string>();
  get(k: string) { return this.map.has(k) ? this.map.get(k)! : null; }
  set(k: string, v: string) { this.map.set(k, v); }
  remove(k: string) { this.map.delete(k); }
}

function defaultAdapter(): StorageAdapter {
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('__mp_probe', '1');
      localStorage.removeItem('__mp_probe');
      return {
        get: (k) => localStorage.getItem(k),
        set: (k, v) => localStorage.setItem(k, v),
        remove: (k) => localStorage.removeItem(k),
      };
    }
  } catch { /* fall through */ }
  return new MemoryStorage();
}

export interface Settings {
  soundEnabled: boolean;
  voiceEnabled: boolean;
  speakAnswers: boolean;
  lightMode: boolean;
}

export interface Profile {
  username: string;
  salt: string;
  hash: string;
  webauthnId: string | null;
  createdAt: number;
}

const K = {
  profile: 'momentumprodigy.profile',
  settings: 'momentumprodigy.settings',
  states: 'momentumprodigy.cardStates',
  log: 'momentumprodigy.reviewLog',
  game: 'momentumprodigy.gamification',
  practice: 'momentumprodigy.practiceCards',
  practiceStates: 'momentumprodigy.practiceStates',
  introduced: 'momentumprodigy.introducedByDay',
};

export class Store {
  constructor(private adapter: StorageAdapter = defaultAdapter()) {}

  private read<T>(key: string, fallback: T): T {
    const raw = this.adapter.get(key);
    if (!raw) return fallback;
    try { return JSON.parse(raw) as T; } catch { return fallback; }
  }
  private write(key: string, value: unknown) {
    this.adapter.set(key, JSON.stringify(value));
  }

  // --- profile / auth ---
  getProfile(): Profile | null { return this.read<Profile | null>(K.profile, null); }
  setProfile(p: Profile) { this.write(K.profile, p); }

  // --- settings ---
  getSettings(): Settings {
    return this.read<Settings>(K.settings, { soundEnabled: true, voiceEnabled: true, speakAnswers: false, lightMode: false });
  }
  setSettings(s: Settings) { this.write(K.settings, s); }

  // --- card states (locked course) ---
  getCardStates(): Map<string, CardState> {
    return new Map(Object.entries(this.read<Record<string, CardState>>(K.states, {})));
  }
  saveCardState(st: CardState) {
    const all = this.read<Record<string, CardState>>(K.states, {});
    all[st.cardId] = st;
    this.write(K.states, all);
  }
  saveCardStates(states: Map<string, CardState>) {
    this.write(K.states, Object.fromEntries(states));
  }

  // --- review history ---
  appendLog(entry: ReviewLogEntry) {
    const log = this.read<ReviewLogEntry[]>(K.log, []);
    log.push(entry);
    if (log.length > 20000) log.splice(0, log.length - 20000);
    this.write(K.log, log);
  }
  getLog(): ReviewLogEntry[] { return this.read<ReviewLogEntry[]>(K.log, []); }

  // --- new-card introduction tally (for automatic pacing) ---
  getIntroducedToday(dayKey: string): number {
    return this.read<Record<string, number>>(K.introduced, {})[dayKey] ?? 0;
  }
  bumpIntroduced(dayKey: string) {
    const all = this.read<Record<string, number>>(K.introduced, {});
    all[dayKey] = (all[dayKey] ?? 0) + 1;
    this.write(K.introduced, all);
  }

  // --- gamification ---
  getGamification(): GamificationState { return this.read(K.game, initialGamification()); }
  setGamification(g: GamificationState) { this.write(K.game, g); }

  // --- AI Practice deck (editable, deletable, resettable) ---
  getPracticeCards(): PracticeCard[] { return this.read<PracticeCard[]>(K.practice, []); }
  setPracticeCards(cards: PracticeCard[]) { this.write(K.practice, cards); }
  addPracticeCard(card: PracticeCard) {
    const all = this.getPracticeCards();
    all.push(card);
    this.setPracticeCards(all);
  }
  deletePracticeCard(id: string) {
    this.setPracticeCards(this.getPracticeCards().filter((c) => c.id !== id));
    const states = this.getPracticeStates();
    states.delete(id);
    this.write(K.practiceStates, Object.fromEntries(states));
  }
  resetPracticeDeck() {
    this.write(K.practice, []);
    this.write(K.practiceStates, {});
  }
  getPracticeStates(): Map<string, CardState> {
    return new Map(Object.entries(this.read<Record<string, CardState>>(K.practiceStates, {})));
  }
  savePracticeState(st: CardState) {
    const all = this.read<Record<string, CardState>>(K.practiceStates, {});
    all[st.cardId] = st;
    this.write(K.practiceStates, all);
  }

  /** Export the practice deck as portable JSON with cloze text. */
  exportPractice(): string {
    return JSON.stringify({ format: 'momentumprodigy-practice-v1', cards: this.getPracticeCards() }, null, 2);
  }
  importPractice(json: string): number {
    const parsed = JSON.parse(json);
    if (parsed?.format !== 'momentumprodigy-practice-v1' || !Array.isArray(parsed.cards)) {
      throw new Error('Unrecognized practice deck format');
    }
    const existing = this.getPracticeCards();
    const ids = new Set(existing.map((c) => c.id));
    let added = 0;
    for (const c of parsed.cards) {
      if (c && typeof c.id === 'string' && typeof c.text === 'string' && !ids.has(c.id)) {
        existing.push(c);
        added++;
      }
    }
    this.setPracticeCards(existing);
    return added;
  }
}

// Subtle Jarvis-like UI sounds, synthesized with WebAudio — zero assets,
// fully offline, and mutable from Settings.
let ctx: AudioContext | null = null;
let muted = false;

export function setMuted(m: boolean) { muted = m; }

function ac(): AudioContext | null {
  if (typeof window === 'undefined' || !(window.AudioContext || (window as any).webkitAudioContext)) return null;
  if (!ctx) ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
  return ctx;
}

function tone(freq: number, dur: number, type: OscillatorType, gainPeak: number, delay = 0, glideTo?: number) {
  const a = ac();
  if (!a || muted) return;
  const t0 = a.currentTime + delay;
  const osc = a.createOscillator();
  const gain = a.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, t0);
  if (glideTo) osc.frequency.exponentialRampToValueAtTime(glideTo, t0 + dur);
  gain.gain.setValueAtTime(0.0001, t0);
  gain.gain.exponentialRampToValueAtTime(gainPeak, t0 + 0.012);
  gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
  osc.connect(gain).connect(a.destination);
  osc.start(t0);
  osc.stop(t0 + dur + 0.02);
}

export const sfx = {
  tap: () => tone(720, 0.06, 'sine', 0.05),
  flip: () => { tone(420, 0.1, 'sine', 0.06, 0, 880); },
  reveal: () => { tone(520, 0.12, 'triangle', 0.06, 0, 1040); tone(1560, 0.08, 'sine', 0.025, 0.05); },
  good: () => { tone(660, 0.09, 'sine', 0.06); tone(990, 0.12, 'sine', 0.05, 0.07); },
  again: () => tone(220, 0.16, 'triangle', 0.06, 0, 160),
  complete: () => { tone(523, 0.1, 'sine', 0.06); tone(659, 0.1, 'sine', 0.06, 0.09); tone(784, 0.18, 'sine', 0.07, 0.18); },
  unlock: () => { tone(392, 0.12, 'triangle', 0.06, 0, 784); tone(1175, 0.16, 'sine', 0.04, 0.1); },
  levelup: () => { tone(523, 0.1, 'sine', 0.07); tone(784, 0.1, 'sine', 0.06, 0.08); tone(1046, 0.22, 'sine', 0.07, 0.16); },
};

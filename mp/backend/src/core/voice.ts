// Voice interaction: on-device speech-to-text, text-to-speech, and a
// command grammar for hands-free navigation and review.
//
// Engines: the platform speech stack via the Web Speech API —
//  • iOS/macOS WKWebView: Apple's on-device Siri speech engines.
//  • Windows WebView2: Windows speech platform.
// These run locally on modern devices (iOS 13+ on-device dictation; Windows
// local speech models). For guaranteed-offline STT/TTS regardless of OS
// settings, docs/OFFLINE_AI.md describes the whisper.cpp + piper sidecar
// upgrade path wired through the same VoiceBridge interface.

export interface VoiceBridge {
  listen(onResult: (text: string, final: boolean) => void, onEnd: () => void): () => void;
  speak(text: string): void;
  stopSpeaking(): void;
  available: boolean;
}

export type VoiceCommand =
  | 'start review' | 'show answer' | 'again' | 'hard' | 'good' | 'easy'
  | 'open dashboard' | 'ask tutor' | 'open skill tree' | 'search' | 'mute' | 'unmute';

const COMMAND_PATTERNS: [RegExp, VoiceCommand][] = [
  [/\b(start|begin)\b.*\b(review|studying|study|session)\b/, 'start review'],
  [/\b(show|reveal|flip)\b.*\b(answer|card|back)\b/, 'show answer'],
  [/^again\b|\bgrade again\b|\banswer again\b/, 'again'],
  [/^hard\b|\bgrade hard\b|\bthat was hard\b/, 'hard'],
  [/^good\b|\bgrade good\b/, 'good'],
  [/^easy\b|\bgrade easy\b|\bthat was easy\b/, 'easy'],
  [/\b(open|go to|show)\b.*\bdashboard\b|^dashboard$/, 'open dashboard'],
  [/\b(ask|open|talk to)\b.*\btutor\b|^tutor$/, 'ask tutor'],
  [/\b(open|show)\b.*\b(skill ?tree|tree|map)\b|^skill ?tree$/, 'open skill tree'],
  [/^search\b|\bopen search\b|\bsearch for\b/, 'search'],
  [/^mute\b|\bturn off sound\b/, 'mute'],
  [/^unmute\b|\bturn on sound\b/, 'unmute'],
];

/** Map a transcript to a command (null = free-form speech, e.g. a tutor question). */
export function parseCommand(transcript: string): VoiceCommand | null {
  const t = transcript.trim().toLowerCase();
  for (const [re, cmd] of COMMAND_PATTERNS) if (re.test(t)) return cmd;
  return null;
}

/** Extract the query from "search for spark shuffles" style utterances. */
export function extractSearchQuery(transcript: string): string {
  return transcript.toLowerCase().replace(/^.*?\bsearch( for)?\b/, '').trim();
}

export function webSpeechBridge(): VoiceBridge {
  const SR: any =
    typeof window !== 'undefined' &&
    ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition);
  const synth = typeof window !== 'undefined' ? window.speechSynthesis : undefined;
  return {
    available: Boolean(SR || synth),
    listen(onResult, onEnd) {
      if (!SR) { onEnd(); return () => {}; }
      const rec = new SR();
      rec.continuous = false;
      rec.interimResults = true;
      rec.lang = 'en-US';
      rec.onresult = (e: any) => {
        let text = '';
        let final = false;
        for (const r of e.results) {
          text += r[0].transcript;
          if (r.isFinal) final = true;
        }
        onResult(text, final);
      };
      rec.onend = onEnd;
      rec.onerror = onEnd;
      try { rec.start(); } catch { onEnd(); }
      return () => { try { rec.stop(); } catch { /* noop */ } };
    },
    speak(text) {
      if (!synth) return;
      synth.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.rate = 1.04;
      u.pitch = 0.92; // calm, low — the MomentumProdigy voice
      const voices = synth.getVoices();
      const preferred = voices.find((v) => /en[-_]/.test(v.lang) && /Daniel|David|Alex|Samantha|Aria|Guy/i.test(v.name));
      if (preferred) u.voice = preferred;
      synth.speak(u);
    },
    stopSpeaking() { synth?.cancel(); },
  };
}

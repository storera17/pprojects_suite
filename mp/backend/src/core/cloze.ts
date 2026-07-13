// Cloze deletion parsing and rendering model. Supported forms:
// {{c1::answer}} and {{c1::answer::hint}}.

export interface ClozeSegment {
  type: 'text' | 'blank';
  text: string; // for blanks: the hidden answer
  hint?: string;
}

export function parseCloze(text: string): ClozeSegment[] {
  const segments: ClozeSegment[] = [];
  const re = /\{\{c(\d+)::((?:[^:}]|:(?!:)|\}(?!\}))*?)(?:::((?:[^}]|\}(?!\}))*?))?\}\}/g;
  let cursor = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    if (m.index > cursor) segments.push({ type: 'text', text: text.slice(cursor, m.index) });
    segments.push({ type: 'blank', text: m[2], hint: m[3] });
    cursor = m.index + m[0].length;
  }
  if (cursor < text.length) segments.push({ type: 'text', text: text.slice(cursor) });
  return segments;
}

/** The card front: blanks replaced by […] (or hint). */
export function clozeFront(text: string): string {
  return parseCloze(text)
    .map((s) => (s.type === 'blank' ? `[${s.hint ?? '…'}]` : s.text))
    .join('');
}

/** The card back: full text (answers revealed). */
export function clozeBack(text: string): string {
  return parseCloze(text)
    .map((s) => s.text)
    .join('');
}

/** Answers hidden by this card. */
export function clozeAnswers(text: string): string[] {
  return parseCloze(text)
    .filter((s) => s.type === 'blank')
    .map((s) => s.text);
}

export function isValidCloze(text: string): boolean {
  return clozeAnswers(text).length > 0;
}

/** Export a cloze card in MomentumProdigy's portable text format. */
export function exportClozeText(text: string): string {
  return text;
}

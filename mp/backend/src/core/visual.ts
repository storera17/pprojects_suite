// Deterministic Jarvis-style visual identity per card — mirrors the
// pipeline's cardVisual() so runtime-generated practice cards match the
// locked course aesthetic. Users cannot edit card themes (by design).
import type { CardVisual } from './types';
import { fnv1a } from './embedding';

const HUES = [187, 199, 168, 262, 305, 38, 142, 210];
const GLYPHS = ['◬', '⬡', '◈', '⟁', '✦', '◉', '⌬', '⟐'];
const PATTERNS = ['grid', 'rings', 'scan', 'hex', 'orbit', 'pulse'];

export function cardVisualFor(id: string): CardVisual {
  const h = fnv1a(id);
  return {
    hue: HUES[h % HUES.length],
    glyph: GLYPHS[(h >>> 3) % GLYPHS.length],
    pattern: PATTERNS[(h >>> 6) % PATTERNS.length],
  };
}

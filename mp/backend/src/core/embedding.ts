// Offline semantic embedding — hashed word + character-trigram features.
// MUST stay in algorithmic lockstep with backend/content-pipeline/embed.mjs (verified by
// tests/embedding-parity.test.ts): query vectors computed here live in the
// same space as the course vectors precomputed at build time.

export const EMBED_DIMS = 192;

export function fnv1a(str: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h >>> 0;
}

export function tokenize(text: string): { words: string[]; grams: string[] } {
  const t = String(text).toLowerCase().replace(/[^a-z0-9 ]+/g, ' ');
  const words = t.split(/\s+/).filter((w) => w.length > 1);
  const grams: string[] = [];
  for (const w of words) {
    const padded = `^${w}$`;
    for (let i = 0; i + 3 <= padded.length; i++) grams.push(padded.slice(i, i + 3));
  }
  return { words, grams };
}

export function embed(text: string, dims = EMBED_DIMS): Float32Array {
  const v = new Float32Array(dims);
  const { words, grams } = tokenize(text);
  for (const w of words) {
    const h = fnv1a(`w:${w}`);
    v[h % dims] += h & 0x10000 ? 1.5 : -1.5;
  }
  for (const g of grams) {
    const h = fnv1a(`g:${g}`);
    v[h % dims] += h & 0x10000 ? 1 : -1;
  }
  let norm = 0;
  for (let i = 0; i < dims; i++) norm += v[i] * v[i];
  norm = Math.sqrt(norm) || 1;
  for (let i = 0; i < dims; i++) v[i] /= norm;
  return v;
}

/** Decode a base64 int8-quantized vector (as packed by the pipeline). */
export function unpackVector(b64: string, dims = EMBED_DIMS): Float32Array {
  const bin = atob(b64); // global in browsers and Node 16+
  const v = new Float32Array(dims);
  for (let i = 0; i < dims && i < bin.length; i++) {
    v[i] = (bin.charCodeAt(i) - 128) / 127;
  }
  return v;
}

export function cosine(a: Float32Array, b: Float32Array): number {
  let dot = 0;
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) dot += a[i] * b[i];
  return dot;
}

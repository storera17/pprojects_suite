// Offline semantic embeddings via hashed word + character-trigram features.
// The identical algorithm is implemented in backend/src/core/embedding.ts so that
// query vectors computed in the app live in the same space as the vectors
// precomputed here. A parity test (tests/embedding-parity.test.ts) keeps
// the two implementations in sync.
import { fnv1a } from './util.mjs';

/** Vector size shared by runtime search and the content-generation pipeline. */
export const EMBED_DIMS = 192;

/** Normalizes text into word and character-trigram features for semantic matching. */
export function tokenize(text) {
  const t = String(text).toLowerCase().replace(/[^a-z0-9 ]+/g, ' ');
  const words = t.split(/\s+/).filter((w) => w.length > 1);
  const grams = [];
  for (const w of words) {
    const padded = `^${w}$`;
    for (let i = 0; i + 3 <= padded.length; i++) grams.push(padded.slice(i, i + 3));
  }
  return { words, grams };
}

/** Embed text into a signed hashed feature vector (Float32Array). */
export function embed(text, dims = EMBED_DIMS) {
  const v = new Float32Array(dims);
  const { words, grams } = tokenize(text);
  for (const w of words) {
    const h = fnv1a(`w:${w}`);
    v[h % dims] += (h & 0x10000) ? 1.5 : -1.5; // words weigh more than grams
  }
  for (const g of grams) {
    const h = fnv1a(`g:${g}`);
    v[h % dims] += (h & 0x10000) ? 1 : -1;
  }
  // L2 normalize
  let norm = 0;
  for (let i = 0; i < dims; i++) norm += v[i] * v[i];
  norm = Math.sqrt(norm) || 1;
  for (let i = 0; i < dims; i++) v[i] /= norm;
  return v;
}

/** Quantize a unit vector to int8 and base64-encode for compact JSON. */
export function packVector(v) {
  const bytes = new Uint8Array(v.length);
  for (let i = 0; i < v.length; i++) {
    bytes[i] = Math.max(0, Math.min(255, Math.round(v[i] * 127) + 128));
  }
  return Buffer.from(bytes).toString('base64');
}

/** Computes similarity between two normalized vectors. */
export function cosine(a, b) {
  let dot = 0;
  for (let i = 0; i < a.length; i++) dot += a[i] * b[i];
  return dot; // unit vectors
}
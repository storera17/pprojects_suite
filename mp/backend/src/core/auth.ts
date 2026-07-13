// Local-only login: password (PBKDF2 via WebCrypto) plus platform biometrics
// (Face ID / Touch ID / Windows Hello) through WebAuthn where available.
// No cloud account; data stays on this device. If the password is forgotten,
// biometric unlock still works while enrolled (per product spec).
import type { Profile, Store } from './store';

const ITERATIONS = 120_000;

function bytesToB64(bytes: ArrayBuffer): string {
  const arr = new Uint8Array(bytes);
  let s = '';
  for (const b of arr) s += String.fromCharCode(b);
  return btoa(s); // atob/btoa are global in browsers and Node 16+
}

function b64ToBytes(b64: string): Uint8Array<ArrayBuffer> {
  const bin = atob(b64);
  const out = new Uint8Array(new ArrayBuffer(bin.length));
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function randomSalt(): Uint8Array<ArrayBuffer> {
  const salt = new Uint8Array(new ArrayBuffer(16));
  globalThis.crypto.getRandomValues(salt); // WebCrypto: browsers + Node 18+
  return salt;
}

async function pbkdf2(password: string, saltB64: string): Promise<string> {
  const subtle = globalThis.crypto.subtle;
  const enc = new TextEncoder();
  const salt = b64ToBytes(saltB64);
  const key = await subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveBits']);
  const bits = await subtle.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt, iterations: ITERATIONS }, key, 256);
  return bytesToB64(bits);
}

export async function createProfile(store: Store, username: string, password: string): Promise<Profile> {
  if (!username.trim()) throw new Error('Username required');
  if (password.length < 4) throw new Error('Password must be at least 4 characters');
  const salt = bytesToB64(randomSalt().buffer);
  const hash = await pbkdf2(password, salt);
  const profile: Profile = { username: username.trim(), salt, hash, webauthnId: null, createdAt: Date.now() };
  store.setProfile(profile);
  return profile;
}

export async function verifyPassword(store: Store, password: string): Promise<boolean> {
  const profile = store.getProfile();
  if (!profile) return false;
  const hash = await pbkdf2(password, profile.salt);
  return hash === profile.hash;
}

export function biometricsSupported(): boolean {
  return typeof window !== 'undefined' && 'PublicKeyCredential' in window;
}

/** Enroll the platform authenticator (Face ID / Touch ID / Windows Hello). */
export async function enrollBiometrics(store: Store): Promise<boolean> {
  const profile = store.getProfile();
  if (!profile || !biometricsSupported()) return false;
  try {
    const challenge = randomSalt();
    const cred = (await navigator.credentials.create({
      publicKey: {
        challenge,
        rp: { name: 'MomentumProdigy', id: location.hostname || 'localhost' },
        user: { id: new TextEncoder().encode(profile.username), name: profile.username, displayName: profile.username },
        pubKeyCredParams: [{ alg: -7, type: 'public-key' }, { alg: -257, type: 'public-key' }],
        authenticatorSelection: { authenticatorAttachment: 'platform', userVerification: 'required' },
        timeout: 60_000,
      },
    })) as PublicKeyCredential | null;
    if (!cred) return false;
    store.setProfile({ ...profile, webauthnId: bytesToB64(cred.rawId) });
    return true;
  } catch {
    return false;
  }
}

/** Unlock with biometrics; succeeds only while a credential is enrolled. */
export async function biometricUnlock(store: Store): Promise<boolean> {
  const profile = store.getProfile();
  if (!profile?.webauthnId || !biometricsSupported()) return false;
  try {
    const challenge = randomSalt();
    const rawId = b64ToBytes(profile.webauthnId);
    const assertion = await navigator.credentials.get({
      publicKey: {
        challenge,
        allowCredentials: [{ id: rawId, type: 'public-key' }],
        userVerification: 'required',
        timeout: 60_000,
      },
    });
    return assertion !== null;
  } catch {
    return false;
  }
}

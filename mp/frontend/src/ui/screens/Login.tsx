import React, { useEffect, useState } from 'react';
import { useApp } from '../App';
import { biometricUnlock, biometricsSupported, createProfile, verifyPassword } from '../../../../backend/src/core/auth';

/** Local-only account gate used to create or unlock the profile stored on the device. */
export function Login({ onUnlocked }: { onUnlocked: () => void }) {
  const { engine } = useApp();
  const profile = engine.store.getProfile();
  const [mode] = useState<'create' | 'unlock'>(profile ? 'unlock' : 'create');
  const [username, setUsername] = useState(profile?.username ?? '');
  const [password, setPassword] = useState('');
  const [err, setErr] = useState('');
  const canBio = Boolean(profile?.webauthnId) && biometricsSupported();

  // Offer Face ID / Touch ID / Hello immediately when enrolled.
  useEffect(() => {
    if (mode === 'unlock' && canBio) {
      biometricUnlock(engine.store).then((ok) => ok && onUnlocked());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr('');
    try {
      if (mode === 'create') {
        await createProfile(engine.store, username, password);
        onUnlocked();
      } else {
        const ok = await verifyPassword(engine.store, password);
        if (ok) onUnlocked();
        else setErr(canBio ? 'Incorrect password — or use biometric unlock.' : 'Incorrect password.');
      }
    } catch (ex: any) {
      setErr(ex.message ?? String(ex));
    }
  };

  return (
    <div className="login-wrap">
      <div className="login panel">
        <img className="orb" src="./icon.svg" alt="" />
        <h1>MomentumProdigy</h1>
        <div className="tag">{mode === 'create' ? 'CREATE LOCAL OPERATOR PROFILE' : `WELCOME BACK, ${(profile?.username ?? '').toUpperCase()}`}</div>
        <form onSubmit={submit}>
          {mode === 'create' && (
            <input type="text" placeholder="Operator name" value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
          )}
          <input
            type="password"
            placeholder={mode === 'create' ? 'Choose a password' : 'Password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus={mode === 'unlock'}
          />
          <div className="err">{err}</div>
          <button className="btn primary" type="submit">
            {mode === 'create' ? 'Initialize' : 'Unlock'}
          </button>
          {canBio && (
            <button type="button" className="btn ghost" onClick={() => biometricUnlock(engine.store).then((ok) => (ok ? onUnlocked() : setErr('Biometric unlock failed.')))}>
              ⬡ Use Face ID / Touch ID / Hello
            </button>
          )}
          <div style={{ fontSize: 11, color: 'var(--fg-dim)', marginTop: 6 }}>
            Local profile only — no cloud account, all data stays on this device.
          </div>
        </form>
      </div>
    </div>
  );
}

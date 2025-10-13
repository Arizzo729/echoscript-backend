// src/lib/authClient.js
export async function getMe() {
  const r = await fetch('/api/auth/me', { credentials: 'include' });
  if (r.status === 401) return null;          // not logged in → null
  if (!r.ok) throw new Error(await r.text()); // other errors bubble up
  return r.json();
}

export async function login(email, password) {
  const r = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ email, password })
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function logout() {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' }).catch(() => {});
}

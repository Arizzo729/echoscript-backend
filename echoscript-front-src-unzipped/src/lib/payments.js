// src/lib/payments.js
export async function startCheckout(plan = 'pro') {
  const base = import.meta.env.VITE_API_BASE_URL || '';
  const res = await fetch(`${base}/api/stripe/create-checkout-session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ plan })
  });

  const text = await res.text();
  let data = {};
  try { data = JSON.parse(text); } catch {}

  if (!res.ok) {
    const msg = data?.detail || data?.error || `Checkout failed (HTTP ${res.status})`;
    throw new Error(msg);
  }

  if (data?.url) {
    window.location.assign(data.url);
    return;
  }
  throw new Error('Checkout failed: missing URL from server');
}

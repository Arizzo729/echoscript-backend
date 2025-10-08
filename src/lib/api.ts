/**
 * Central API client — forces absolute backend base to avoid Netlify rewrites.
 * Works even if VITE_API_URL isn't set.
 */
const ENV_BASE = (import.meta as any).env?.VITE_API_URL || (import.meta as any).env?.VITE_API_BASE;
const BASE: string = (ENV_BASE || "https://api.echoscript.ai/api").replace(/\/+$/,"");

async function parse(res: Response) {
  const text = await res.text();
  try { return JSON.parse(text); } catch { return text; }
}
async function request(path: string, init?: RequestInit) {
  const url = `${BASE}${path}`;
  const res = await fetch(url, init);
  const data = await parse(res);
  if (!res.ok) {
    const msg = typeof data === "string" ? data : (data?.message || data?.error || res.statusText);
    throw new Error(`${res.status} ${msg}`);
  }
  return data;
}

const api = {
  base: BASE,
  // health
  health: () => request("/healthz"),

  // stripe
  stripeDebugPrices: () => request("/stripe/_debug-prices"),
  createCheckoutSession: (plan: string) =>
    request("/stripe/create-checkout-session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plan }),
    }),
  // alias (some components call this name)
  stripeCreateCheckout: (plan: string) => api.createCheckoutSession(plan),

  // paypal
  paypalHealth: () => request("/paypal/health"),
  paypalCreateOrder: (amount: string, currency = "USD", plan?: string) =>
    request("/paypal/create-order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount, currency, plan }),
    }),
  createPayPalOrder: (amount: string, currency = "USD", plan?: string) =>
    api.paypalCreateOrder(amount, currency, plan),
  paypalCaptureOrder: (orderId: string) =>
    request(`/paypal/capture-order/${orderId}`, { method: "POST" }),
};

export default api;

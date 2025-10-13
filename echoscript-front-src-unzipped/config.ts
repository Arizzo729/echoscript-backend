// src/config.ts
export const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";
export const STRIPE_PK = import.meta.env.VITE_STRIPE_PUBLIC_KEY ?? "";
export const PAYPAL_ID = import.meta.env.VITE_PAYPAL_CLIENT_ID ?? "";

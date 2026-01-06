// CommonJS so it runs without "type":"module"
const express = require("express");
const Stripe = require("stripe");

const router = express.Router();

// Prefer STRIPE_SECRET_KEY, fallback to STRIPE_SECRET (since I saw both in your code)
const STRIPE_SECRET = process.env.STRIPE_SECRET_KEY || process.env.STRIPE_SECRET;
if (!STRIPE_SECRET) {
  console.error("❌ Missing STRIPE_SECRET_KEY (or STRIPE_SECRET) in the backend environment.");
}
const stripe = new Stripe(STRIPE_SECRET, { apiVersion: "2024-06-20" });

// Map plan -> price id from your env
const PRICE_IDS = {
  pro: process.env.STRIPE_PRICE_PRO,
  premium: process.env.STRIPE_PRICE_PREMIUM,
  edu: process.env.STRIPE_PRICE_EDU,
};

router.post("/create-checkout-session", async (req, res) => {
  try {
    const plan = (req.body?.plan || "pro").toLowerCase();
    const price = PRICE_IDS[plan];
    if (!STRIPE_SECRET) throw new Error("No API key provided (set STRIPE_SECRET_KEY).");
    if (!price) throw new Error(`No Stripe price configured for plan "${plan}".`);

    const successUrl =
      process.env.STRIPE_SUCCESS_URL ||
      `${process.env.FRONTEND_URL || "http://localhost:5173"}/purchase/success`;
    const cancelUrl =
      process.env.STRIPE_CANCEL_URL ||
      `${process.env.FRONTEND_URL || "http://localhost:5173"}/purchase`;

    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      line_items: [{ price, quantity: 1 }],
      success_url: `${successUrl}?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: cancelUrl,
      // Optional but recommended:
      automatic_tax: { enabled: true },
    });

    return res.json({ url: session.url });
  } catch (err) {
    console.error("Stripe error:", err);
    return res.status(400).json({ error: err.message || "Stripe checkout failed" });
  }
});

module.exports = router;

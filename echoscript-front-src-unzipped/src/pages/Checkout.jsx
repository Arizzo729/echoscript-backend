// src/pages/Checkout.jsx
import React, { useEffect, useState } from "react";

function useQuery() {
  const params = new URLSearchParams(window.location.search);
  return {
    success: params.get("success"),
    canceled: params.get("canceled"),
    session_id: params.get("session_id"),
    paypal: params.get("paypal"),
  };
}

export default function Checkout() {
  const [status, setStatus] = useState("Checking…");
  const [details, setDetails] = useState(null);
  const q = useQuery();

  useEffect(() => {
    const run = async () => {
      if (q.paypal === "success") {
        setStatus("PayPal payment captured ✅");
        return;
      }
      if (q.success === "1" && q.session_id) {
        try {
          const res = await fetch(`/api/stripe/checkout/session?session_id=${encodeURIComponent(q.session_id)}`);
          if (res.ok) {
            const data = await res.json();
            setDetails(data);
            setStatus("Stripe checkout complete ✅");
          } else {
            setStatus("Completed (unable to verify session)");
          }
        } catch {
          setStatus("Completed (unable to verify session)");
        }
        return;
      }
      if (q.canceled === "1") {
        setStatus("Checkout canceled.");
        return;
      }
      setStatus("Ready.");
    };
    run();
  }, []); // eslint-disable-line

  return (
    <div style={{ maxWidth: 720, margin: "40px auto", padding: 16 }}>
      <h1>Checkout</h1>
      <p>{status}</p>
      {details ? (
        <pre
          style={{
            background: "#0b1220",
            color: "#cbd5e1",
            padding: 16,
            borderRadius: 12,
            overflowX: "auto",
          }}
        >
{JSON.stringify(details, null, 2)}
        </pre>
      ) : null}
      <a href="/purchase" style={{ display: "inline-block", marginTop: 16 }}>
        ← Back to purchase
      </a>
    </div>
  );
}

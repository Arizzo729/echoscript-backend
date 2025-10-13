// src/pages/ResetPassword.jsx
import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mail, ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

const API = (import.meta?.env?.VITE_API_BASE || "https://api.echoscript.ai").replace(/\/+$/,"");

export default function ResetPassword() {
  const { t } = useTranslation();
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const sendCode = async () => {
    if (!email) return;
    setError(""); setBusy(true);
    try {
      const res = await fetch(`${API}/api/auth/send-reset-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email }),
      });
      const result = await res.json().catch(() => ({}));
      if (res.ok && result?.status === "ok") {
        setStep(2);
        setMessage(t("reset.code_sent") || "Reset code sent.");
      } else {
        setError(result?.error || t("reset.email_not_found") || "Email not found.");
      }
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  };

  const verifyCode = async () => {
    if (!code || !newPassword) return;
    setError(""); setBusy(true);
    try {
      const res = await fetch(`${API}/api/auth/verify-reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, code, new_password: newPassword }),
      });
      const result = await res.json().catch(() => ({}));
      if (res.ok && result?.status === "ok") {
        setMessage(t("reset.success") || "Password reset successful.");
        setStep(3);
      } else {
        setError(t("reset.failure") || "Reset failed. Check your code.");
      }
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <motion.div
      className="flex items-center justify-center min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-800 px-6"
      initial={{ opacity: 0, y: 32 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="w-full max-w-md p-8 space-y-6 rounded-2xl shadow-xl bg-zinc-900 border border-zinc-700">
        <h1 className="text-3xl font-bold text-center text-white">
          {t("reset.title") || "Reset Password"}
        </h1>
        <p className="text-sm text-center text-zinc-400">
          {t("reset.subtitle") || "We’ll email you a code to reset your password."}
        </p>

        {error && <div className="bg-red-500/10 text-red-300 px-4 py-2 rounded-md text-sm text-center">{error}</div>}
        {message && <div className="bg-green-500/10 text-green-300 px-4 py-2 rounded-md text-sm text-center">{message}</div>}

        <AnimatePresence mode="wait">
          {step === 1 && (
            <motion.div key="step1" initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 24 }} transition={{ duration: 0.3 }} className="space-y-4">
              <div className="flex flex-col gap-1">
                <label htmlFor="email" className="text-sm font-medium text-zinc-300">{t("reset.email") || "Email"}</label>
                <div className="relative">
                  <input
                    id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                    placeholder={t("reset.email_placeholder") || "you@example.com"}
                    className="w-full px-4 py-2 pr-10 rounded-lg border border-zinc-700 bg-zinc-800 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-teal-500"
                    disabled={busy}
                  />
                  <Mail className="absolute right-3 top-2.5 w-5 h-5 text-zinc-400" />
                </div>
              </div>
              <button
                onClick={sendCode} disabled={busy || !email}
                className={`w-full text-white font-semibold py-2 rounded-lg transition-all duration-300 shadow-md ${busy ? "bg-teal-700 cursor-not-allowed opacity-80" : "bg-teal-500 hover:bg-teal-400"}`}
              >
                {busy ? (t("reset.sending") || "Sending…") : (t("reset.send_code") || "Send code")}
              </button>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div key="step2" initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: 0.3 }} className="space-y-4">
              <div className="flex flex-col gap-1">
                <label htmlFor="code" className="text-sm font-medium text-zinc-300">{t("reset.code") || "Code"}</label>
                <input
                  id="code" type="text" value={code} onChange={(e) => setCode(e.target.value)}
                  placeholder={t("reset.code_placeholder") || "6-digit code"}
                  className="w-full px-4 py-2 rounded-lg border border-zinc-700 bg-zinc-800 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={busy}
                />
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="newPass" className="text-sm font-medium text-zinc-300">{t("reset.new_password") || "New password"}</label>
                <input
                  id="newPass" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)}
                  placeholder={t("reset.new_password_placeholder") || "••••••••"}
                  className="w-full px-4 py-2 rounded-lg border border-zinc-700 bg-zinc-800 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={busy}
                />
              </div>

              <button
                onClick={verifyCode} disabled={busy || !code || !newPassword}
                className={`w-full text-white font-semibold py-2 rounded-lg transition-all duration-300 shadow-md ${busy ? "bg-blue-700 cursor-not-allowed opacity-80" : "bg-blue-600 hover:bg-blue-500"}`}
              >
                {busy ? (t("reset.processing") || "Processing…") : (t("reset.reset_button") || "Reset password")}
              </button>
            </motion.div>
          )}

          {step === 3 && (
            <motion.div key="step3" initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 24 }} transition={{ duration: 0.3 }}
              className="text-center text-sm text-zinc-300 space-y-4">
              <ShieldCheck className="w-12 h-12 mx-auto text-green-400" />
              <p>{t("reset.done") || "All set! You can sign in with your new password."}</p>
              <Link to="/signin" className="inline-block text-teal-400 hover:underline font-medium">
                {t("reset.return_signin") || "Return to sign in"}
              </Link>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}


// ✅ EchoScript.AI — Payment Success Page
import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { CheckCircle, Home } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function Success() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    const timer = setTimeout(() => {
      navigate("/account");
    }, 7000);
    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <motion.div
      className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-zinc-950 via-zinc-900 to-zinc-950 px-2 sm:px-0"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="w-full max-w-md">
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl px-7 py-10 text-center">
          <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-5" />
          <h1 className="text-3xl font-extrabold mb-2">{t("success.title", "Payment Successful!")}</h1>
          <p className="text-zinc-400 mb-8 text-base">
            {t("success.message", "Thank you! Your payment was processed successfully.")}
          </p>

          <button
            onClick={() => navigate("/account")}
            className="inline-flex items-center gap-2 px-7 py-3 bg-teal-600 hover:bg-teal-500 text-lg font-semibold rounded-xl shadow transition focus-visible:ring-2 focus-visible:ring-teal-400"
          >
            <Home className="w-5 h-5" />
            {t("success.cta", "Go to Dashboard")}
          </button>

          <p className="text-xs text-zinc-600 mt-7">
            {t("success.redirect_note", "You’ll be redirected shortly...")}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

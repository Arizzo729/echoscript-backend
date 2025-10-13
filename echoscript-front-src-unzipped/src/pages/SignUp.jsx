// src/pages/SignUp.jsx
import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Mail, Lock, Eye, EyeOff, ArrowLeft } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext";

export default function SignUp() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { signUp, user } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { if (user?.email) navigate("/dashboard"); }, [user, navigate]);

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError("");
    if (!email.includes("@")) return setError(t("signup_error_invalid_email") || "Enter a valid email.");
    if (password.length < 6) return setError(t("signup_error_short_password") || "Password must be at least 6 chars.");
    if (password !== confirm) return setError(t("signup_error_password_mismatch") || "Passwords do not match.");

    setLoading(true);
    try {
      await signUp({ email, password });
      navigate("/dashboard");
    } catch (err) {
      setError(err?.message || t("signup_error_general") || "Sign up failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      className="flex items-center justify-center min-h-screen bg-gradient-to-br from-zinc-950 to-zinc-900 px-2 sm:px-0"
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
    >
      <motion.div
        className="w-full max-w-[410px] space-y-5 p-6 xs:p-8 bg-gradient-to-br from-zinc-900/90 to-zinc-800/90 border border-zinc-800 rounded-3xl shadow-2xl backdrop-blur-lg"
        initial={{ y: 30, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.35, type: "spring" }}
      >
        <Link
          to={user ? "/dashboard" : "/"}
          className="flex items-center text-sm font-semibold text-teal-400 hover:underline focus-visible:ring-2 focus-visible:ring-teal-400 w-max"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          {user ? t("dashboard", "Dashboard") : t("home", "Home")}
        </Link>

        <div className="space-y-1 text-center">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight drop-shadow-lg">
            {t("signup_title") || "Create Account"}
          </h1>
          <p className="text-base text-zinc-400 font-medium">
            {t("signup_subtitle")}&nbsp;
            <span className="text-teal-400 font-bold">EchoScript.AI</span>
          </p>
        </div>

        {error && (
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
            className="px-4 py-2 text-sm text-red-300 bg-red-700/15 rounded-lg text-center border border-red-500/30 shadow">
            {error}
          </motion.div>
        )}

        <form onSubmit={handleSignUp} className="space-y-4">
          <div className="space-y-1">
            <label htmlFor="email" className="block text-xs font-medium text-zinc-400 tracking-wide">
              {t("email")}
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
              <input
                id="email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t("email")}
                required
                disabled={loading}
                className="w-full pl-11 pr-4 py-3 rounded-xl bg-zinc-800 border border-zinc-700 text-white text-base placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-teal-500 transition focus:bg-zinc-900/60 shadow-sm"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label htmlFor="password" className="block text-xs font-medium text-zinc-400 tracking-wide">
              {t("password_label")}
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t("password_placeholder")}
                required
                disabled={loading}
                className="w-full pl-11 pr-11 py-3 rounded-xl bg-zinc-800 border border-zinc-700 text-white text-base placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-zinc-900/60 transition shadow-sm"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-full focus-visible:ring-2 focus-visible:ring-teal-400"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="w-5 h-5 text-zinc-400 hover:text-white" /> : <Eye className="w-5 h-5 text-zinc-400 hover:text-white" />}
              </button>
            </div>
          </div>

          <div className="space-y-1">
            <label htmlFor="confirm" className="block text-xs font-medium text-zinc-400 tracking-wide">
              {t("confirm_password")}
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
              <input
                id="confirm"
                type={showPassword ? "text" : "password"}
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder={t("confirm_password") || t("password")}
                required
                disabled={loading}
                className="w-full pl-11 pr-4 py-3 rounded-xl bg-zinc-800 border border-zinc-700 text-white text-base placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-zinc-900/60 transition shadow-sm"
              />
            </div>
          </div>

          <motion.button
            type="submit"
            whileTap={{ scale: 0.96 }}
            disabled={loading}
            className={`w-full py-3 text-base font-semibold rounded-xl shadow-xl transition
              ${loading ? "bg-teal-700 cursor-not-allowed opacity-80" : "bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400"}
              focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400`}
          >
            {loading ? t("creating_account") : t("create_account_button")}
          </motion.button>
        </form>

        <div className="text-center text-xs text-zinc-500 mt-3">
          {t("already_have_account", "Already have an account?")}&nbsp;
          <Link to="/signin" className="font-semibold text-teal-400 hover:underline focus-visible:ring-2 focus-visible:ring-teal-400 rounded">
            {t("sign_in_here", "Sign in here.")}
          </Link>
        </div>
      </motion.div>
    </motion.div>
  );
}

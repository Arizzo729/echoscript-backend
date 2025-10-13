// src/pages/Dashboard.jsx
import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Mic,
  FileText,
  Sparkles,
  Video,
  Clock,
  User,
  Settings2,
  ShieldCheck,
  AlertTriangle,
} from "lucide-react";

/**
 * API base (Netlify -> Environment: VITE_API_URL = https://api.echoscript.ai)
 */
const API = import.meta.env.VITE_API_URL?.replace(/\/+$/, "") || "";

/**
 * Plan limits – adjust easily here (minutes per billing period).
 */
const PLAN_LIMITS = {
  guest: 10,
  free: 30,
  pro: 120,
  premium: 300,
};

/**
 * Safely fetch JSON. Returns { ok, data } or { ok:false, error }.
 */
async function getJSON(url, opts = {}) {
  try {
    const res = await fetch(url, {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      ...opts,
    });
    const ct = res.headers.get("content-type") || "";
    const data = ct.includes("application/json") ? await res.json() : null;
    if (!res.ok) return { ok: false, error: data?.detail || res.statusText || "Request failed" };
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: e?.message || "Network error" };
  }
}

/**
 * Derive a normalized user record with plan + limits from /api/auth/me
 * If unauthenticated or the endpoint isn't present, return a guest profile.
 */
async function resolveViewer() {
  if (!API) return { isGuest: true, name: "Guest", email: "guest", planKey: "guest", limit: PLAN_LIMITS.guest };
  const r = await getJSON(`${API}/api/auth/me`);
  if (!r.ok) return { isGuest: true, name: "Guest", email: "guest", planKey: "guest", limit: PLAN_LIMITS.guest };

  // Map your backend's fields → local shape
  const me = r.data || {};
  // Expect something like me.plan or me.subscription.plan
  const rawPlan = (me.plan || me.subscription?.plan || "free").toString().toLowerCase();
  const planKey = ["guest", "free", "pro", "premium"].includes(rawPlan) ? rawPlan : "free";
  return {
    isGuest: false,
    name: me.name || me.email?.split("@")[0] || "Member",
    email: me.email || "",
    planKey,
    limit: PLAN_LIMITS[planKey],
  };
}

/**
 * Fetch usage summary. Expected backend response shape:
 * { minutesUsed: number, sessions: number }
 * Falls back to zeros if the endpoint is missing.
 */
async function resolveUsage() {
  if (!API) return { minutesUsed: 0, sessions: 0 };
  // Try your primary endpoint
  let r = await getJSON(`${API}/api/usage/summary`);
  if (r.ok && r.data) return { minutesUsed: Number(r.data.minutesUsed || 0), sessions: Number(r.data.sessions || 0) };

  // Fallback attempt (if you named it differently)
  r = await getJSON(`${API}/api/users/usage`);
  if (r.ok && r.data) return { minutesUsed: Number(r.data.minutesUsed || 0), sessions: Number(r.data.sessions || 0) };

  // Final fallback: zero usage so the UI still renders
  return { minutesUsed: 0, sessions: 0 };
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [viewer, setViewer] = useState({
    isGuest: true,
    name: "Guest",
    email: "",
    planKey: "guest",
    limit: PLAN_LIMITS.guest,
  });
  const [usage, setUsage] = useState({ minutesUsed: 0, sessions: 0 });
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    let mounted = true;
    (async () => {
      setLoading(true);
      setErr("");
      const v = await resolveViewer();
      const u = v.isGuest ? { minutesUsed: 0, sessions: 0 } : await resolveUsage();
      if (!mounted) return;
      setViewer(v);
      setUsage(u);
      setLoading(false);
    })();
    return () => { mounted = false; };
  }, []);

  const planLabel = useMemo(() => {
    const map = { guest: "Guest", free: "Free Plan", pro: "Pro Plan", premium: "Premium Plan" };
    return map[viewer.planKey] || "Free Plan";
  }, [viewer.planKey]);

  const percentUsed = useMemo(() => {
    const pct = (usage.minutesUsed / Math.max(1, viewer.limit)) * 100;
    return Math.min(100, Math.max(0, pct));
  }, [usage.minutesUsed, viewer.limit]);

  const sections = [
    { icon: <Mic />, label: "Upload Audio", desc: "Transcribe audio files instantly.", route: "/upload", color: "from-teal-500 to-teal-700" },
    { icon: <FileText />, label: "Transcripts", desc: "Browse & manage your transcripts.", route: "/transcripts", color: "from-indigo-500 to-indigo-700" },
    { icon: <Sparkles />, label: "Summarize", desc: "Get instant AI-powered summaries.", route: "/summary", color: "from-purple-500 to-purple-700" },
    { icon: <Video />, label: "Video Upload", desc: "Extract audio & transcript from videos.", route: "/video", color: "from-rose-500 to-rose-700" },
    { icon: <Clock />, label: "History", desc: "See your previous sessions.", route: "/history", color: "from-yellow-400 to-yellow-600" },
    { icon: <Settings2 />, label: "Settings", desc: "Customize your preferences.", route: "/settings", color: "from-zinc-600 to-zinc-800" },
  ];

  return (
    <motion.div
      className="max-w-7xl mx-auto px-2 md:px-6 py-10 min-h-[90vh]"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
        className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-3"
      >
        <div>
          <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight drop-shadow">
            👋 {viewer.isGuest ? "Welcome!" : "Welcome back,"}{" "}
            {!viewer.isGuest && <span className="text-teal-400">{viewer.name}</span>}
          </h1>
          <p className="text-base text-zinc-400 mt-2">
            Your EchoScript dashboard. Upload, transcribe, and manage content with AI.
          </p>
        </div>

        <button
          onClick={() => navigate("/account")}
          className="inline-flex items-center gap-2 py-2 px-4 rounded-xl bg-gradient-to-r from-teal-600 to-cyan-500 text-white font-semibold shadow hover:from-teal-500 hover:to-cyan-400 focus-visible:ring-2 focus-visible:ring-teal-400 transition"
        >
          <User className="w-5 h-5" />
          {viewer.isGuest ? "Sign In" : viewer.email || "Account"}
        </button>
      </motion.header>

      {/* Action Grid */}
      <motion.div
        className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
        initial="hidden"
        animate="visible"
        variants={{ visible: { transition: { staggerChildren: 0.05 } }, hidden: {} }}
      >
        {sections.map(({ icon, label, route, desc, color }) => (
          <DashboardActionCard
            key={label}
            icon={icon}
            label={label}
            desc={desc}
            color={color}
            onClick={() => navigate(route)}
          />
        ))}
      </motion.div>

      {/* Usage / Profile / Plan */}
      <div className="grid md:grid-cols-3 gap-6 mb-10">
        {/* Usage */}
        <motion.div
          className="rounded-2xl border border-zinc-700 bg-zinc-900 shadow-lg p-6 flex flex-col justify-between"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div>
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5 text-yellow-400" />
              Usage Summary
            </h2>

            {loading ? (
              <p className="text-sm text-zinc-400">Loading your usage…</p>
            ) : (
              <>
                {err && (
                  <p className="text-sm text-amber-400 flex items-center gap-2 mb-2">
                    <AlertTriangle className="w-4 h-4" />
                    {err}
                  </p>
                )}
                <ul className="space-y-2 text-sm text-zinc-300">
                  <li>
                    <strong className="text-white">Plan:</strong>{" "}
                    {planLabel}
                  </li>
                  <li>
                    <strong className="text-white">Minutes Used:</strong>{" "}
                    {usage.minutesUsed} / {viewer.limit}
                  </li>
                  <li>
                    <strong className="text-white">Sessions:</strong>{" "}
                    {usage.sessions}
                  </li>
                </ul>
                <div className="mt-5 h-3 bg-zinc-800 rounded-full overflow-hidden shadow-inner">
                  <motion.div
                    className="h-full bg-gradient-to-r from-teal-400 to-blue-500 rounded-full"
                    style={{ width: `${percentUsed}%` }}
                    initial={{ width: 0 }}
                    animate={{ width: `${percentUsed}%` }}
                    transition={{ duration: 0.7 }}
                  />
                </div>
                <p className="text-right text-xs text-zinc-500 mt-2 italic">
                  {percentUsed.toFixed(1)}% used
                </p>
              </>
            )}
          </div>

          <button
            onClick={() => navigate("/purchase/minutes")}
            className="mt-6 w-full py-2 rounded-lg bg-gradient-to-r from-amber-400 to-orange-500 text-white font-semibold shadow hover:from-amber-500 hover:to-orange-400 focus-visible:ring-2 focus-visible:ring-amber-400 transition"
          >
            {viewer.isGuest ? "Create Account" : "Buy More Minutes"}
          </button>
        </motion.div>

        {/* Profile */}
        <motion.div
          className="rounded-2xl border border-zinc-700 bg-zinc-900 shadow-lg p-6 flex flex-col justify-between"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <div className="flex items-center gap-4 mb-3">
            <div className="p-4 rounded-full bg-gradient-to-br from-teal-500 to-blue-600 text-white shadow-lg">
              <User className="w-6 h-6" />
            </div>
            <div>
              <p className="text-lg font-semibold text-white">
                {viewer.isGuest ? "Guest User" : viewer.name}
              </p>
              <p className="text-sm text-zinc-400">{viewer.isGuest ? "—" : viewer.email}</p>
            </div>
          </div>
          <button
            onClick={() => navigate("/account")}
            className="w-full mt-2 py-2 rounded-lg bg-gradient-to-r from-zinc-700 to-zinc-800 text-white font-medium shadow hover:from-zinc-800 hover:to-zinc-900 focus-visible:ring-2 focus-visible:ring-zinc-400 transition"
          >
            Account Settings
          </button>
        </motion.div>

        {/* Plan Card */}
        <motion.div
          className="rounded-2xl border border-teal-700 bg-gradient-to-br from-teal-900 to-blue-900 shadow-xl p-6 flex flex-col items-start"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-center gap-3 mb-3">
            <ShieldCheck className="w-7 h-7 text-teal-300" />
            <span className="text-xl font-bold text-teal-200">{planLabel}</span>
          </div>
          <p className="text-zinc-200 mb-2">
            Unlock advanced features, faster transcription, and premium support.
          </p>
          <button
            onClick={() => navigate("/purchase")}
            className="mt-2 w-full py-2 rounded-lg bg-gradient-to-r from-teal-500 to-blue-600 text-white font-semibold shadow hover:from-teal-400 hover:to-blue-400 focus-visible:ring-2 focus-visible:ring-teal-400 transition"
          >
            {viewer.planKey === "premium" ? "Manage Plan" : "Upgrade Plan"}
          </button>
        </motion.div>
      </div>

      {/* Footer */}
      <div className="mt-12 pt-6 border-t border-zinc-800 text-sm text-zinc-400 flex flex-col sm:flex-row items-start sm:items-center gap-3 justify-between">
        <span>© {new Date().getFullYear()} EchoScript.AI</span>
        <div className="flex items-center gap-4">
          <a href="/privacy" target="_blank" rel="noopener noreferrer" className="text-teal-300 hover:text-teal-2 00 underline underline-offset-4">
            Privacy Policy
          </a>
          <a href="/terms" target="_blank" rel="noopener noreferrer" className="text-teal-300 hover:text-teal-200 underline underline-offset-4">
            Terms of Service
          </a>
        </div>
      </div>
    </motion.div>
  );
}

function DashboardActionCard({ icon, label, desc, color, onClick }) {
  return (
    <motion.button
      whileHover={{ scale: 1.045 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`flex flex-col justify-between items-start w-full h-40 md:h-44 p-5 rounded-2xl shadow-lg bg-gradient-to-br ${color} text-white transition-all group border-2 border-transparent hover:border-teal-300/60`}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex items-center gap-4 mb-2">
        <span className="p-3 bg-white/20 rounded-full shadow">
          {React.cloneElement(icon, { className: "w-6 h-6" })}
        </span>
        <span className="text-lg font-bold">{label}</span>
      </div>
      <p className="text-zinc-200 text-[15px] mb-2 flex-1">{desc}</p>
      <span className="text-xs text-white/80 mt-auto group-hover:translate-x-1 transition-transform">
        Go &rarr;
      </span>
    </motion.button>
  );
}

import React, { useState } from "react";
import { motion } from "framer-motion";
import Textarea from "../components/ui/Textarea";
import Button from "../components/ui/Button";
import { Sparkles, Loader2 } from "lucide-react";
import { useTranslation } from "react-i18next";

const tones = [
  { id: "default", label: "Smart" },
  { id: "friendly", label: "Friendly" },
  { id: "formal", label: "Formal" },
  { id: "bullet", label: "Bulleted" },
  { id: "action", label: "Action-Oriented" },
];

const lengths = ["short", "medium", "long"];

export default function SummaryPage() {
  const { t } = useTranslation();
  const [transcript, setTranscript] = useState("");
  const [tone, setTone] = useState("default");
  const [length, setLength] = useState("short");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [cached, setCached] = useState(false);

  const generateSummary = async () => {
    if (!transcript.trim()) return;
    setLoading(true);
    setSummary("");
    setCached(false);

    try {
      const res = await fetch("/summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript, tone, length }),
      });
      const data = await res.json();
      setSummary(data.summary);
      setCached(data.cached);
    } catch (err) {
      setSummary(t("Something went wrong. Please try again."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      className="min-h-screen flex flex-col items-center justify-center px-2 sm:px-6 py-8 sm:py-12 bg-gradient-to-br from-zinc-950 to-zinc-900"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ duration: 0.4 }}
    >
      <div className="w-full max-w-2xl bg-zinc-900/95 border border-zinc-800 rounded-3xl shadow-2xl px-3 xs:px-7 py-7 xs:py-10 space-y-7">
        <h1 className="text-2xl xs:text-4xl font-extrabold text-center bg-gradient-to-br from-teal-400 to-blue-500 bg-clip-text text-transparent tracking-tight">
          🧠 AI-Powered Summarizer
        </h1>

        <p className="text-center text-zinc-400 text-base mb-2">
          {t("Paste your transcript below and generate a clear, structured summary with advanced GPT AI.")}
        </p>

        <Textarea
          rows={8}
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          placeholder={t("Paste your transcript here...")}
          className="w-full mb-0 resize-y text-base bg-zinc-800 text-white border border-zinc-700 rounded-xl p-3 focus:ring-2 focus:ring-teal-500 transition"
          disabled={loading}
        />

        <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-2">
          <div className="flex flex-wrap gap-2 flex-1 justify-center sm:justify-start">
            {tones.map((tOption) => (
              <button
                key={tOption.id}
                onClick={() => setTone(tOption.id)}
                className={`px-4 py-1.5 rounded-full text-sm font-semibold transition 
                  ${tone === tOption.id
                    ? "bg-teal-600 text-white shadow-md"
                    : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"}
                  focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400`}
                aria-pressed={tone === tOption.id}
                disabled={loading}
              >
                {tOption.label}
              </button>
            ))}
          </div>
          <div className="flex gap-2 flex-1 justify-center sm:justify-end">
            {lengths.map((l) => (
              <button
                key={l}
                onClick={() => setLength(l)}
                className={`px-4 py-1.5 rounded-full text-sm font-semibold transition 
                  ${length === l
                    ? "bg-blue-600 text-white shadow-md"
                    : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"}
                  focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400`}
                aria-pressed={length === l}
                disabled={loading}
              >
                {t(l)}
              </button>
            ))}
          </div>
        </div>

        <div className="text-center">
          <Button
            onClick={generateSummary}
            disabled={loading || !transcript.trim()}
            icon={loading ? <Loader2 className="animate-spin" /> : <Sparkles />}
            className="w-full max-w-xs mx-auto py-3 text-base font-bold rounded-xl"
          >
            {loading ? t("Summarizing...") : t("Generate Summary")}
          </Button>
        </div>

        {summary && (
          <motion.div
            className="mt-7 p-5 bg-zinc-950 border border-zinc-800 rounded-xl shadow-lg whitespace-pre-wrap text-base leading-relaxed font-mono text-zinc-200"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            {cached && (
              <div className="mb-2 text-xs italic text-yellow-400">
                ({t("from cache")})
              </div>
            )}
            {summary}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FileText, Loader2, AlertCircle } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function TranscriptsPage() {
  const { t } = useTranslation();
  const [transcripts, setTranscripts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchTranscripts = async () => {
      try {
        const response = await fetch("/api/transcripts");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
          throw new Error("Expected JSON, got something else.");
        }
        const data = await response.json();
        if (!Array.isArray(data)) throw new Error("Invalid data format");
        setTranscripts(data);
      } catch (err) {
        console.error("Fetch failed:", err);
        setError(
          t("error.fetchTranscripts") || "Unable to load transcripts. Please try again later."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchTranscripts();
  }, [t]);

  return (
    <div className="px-4 py-8 max-w-4xl mx-auto">
      <motion.h1
        className="text-3xl font-bold text-zinc-800 dark:text-zinc-100 mb-6"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        {t("transcripts.title", "Your Transcripts")}
      </motion.h1>

      {loading ? (
        <div className="flex items-center gap-2 text-zinc-600 dark:text-zinc-300">
          <Loader2 className="animate-spin w-5 h-5" />
          <span>{t("loading", "Loading...")}</span>
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 text-red-500">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      ) : transcripts.length === 0 ? (
        <p className="text-zinc-500">
          {t("transcripts.none", "No transcripts found.")}
        </p>
      ) : (
        <ul className="space-y-4">
          {transcripts.map((t) => (
            <li
              key={t.id}
              className="p-4 rounded-xl border dark:border-zinc-700 shadow-sm hover:bg-zinc-50 dark:hover:bg-zinc-800 transition"
            >
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-teal-500" />
                <span className="font-medium text-zinc-900 dark:text-white">
                  {t.title || "Untitled Transcript"}
                </span>
              </div>
              <p className="text-sm text-zinc-500 mt-1">
                {t.created_at
                  ? new Date(t.created_at).toLocaleString()
                  : "Unknown date"}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}


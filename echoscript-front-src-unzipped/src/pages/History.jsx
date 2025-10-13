// src/pages/HistoryPage.jsx — Enhanced History with Search, Pagination, and Toasts
import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Download, Trash2, RotateCcw } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/toast/ToastProvider";

const HISTORY_KEY = "transcriptHistory";
const ITEMS_PER_PAGE = 8;

const loadHistory = () => {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
};

const saveHistory = (history) => {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
};

export default function HistoryPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const toast = useToast();

  const [history, setHistory] = useState([]);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    setHistory(loadHistory());
  }, []);

  const updateHistory = (newHistory) => {
    setHistory(newHistory);
    saveHistory(newHistory);
  };

  const filtered = history.filter((item) =>
    item.label.toLowerCase().includes(search.toLowerCase()) ||
    item.preview.toLowerCase().includes(search.toLowerCase())
  );

  const pageCount = Math.ceil(filtered.length / ITEMS_PER_PAGE) || 1;
  const currentItems = filtered.slice(
    (page - 1) * ITEMS_PER_PAGE,
    page * ITEMS_PER_PAGE
  );

  const handleDelete = (id) => {
    updateHistory(history.filter((h) => h.id !== id));
    toast({ message: t("Entry deleted"), type: "info" });
  };

  const handleDownload = (text, label) => {
    const blob = new Blob([text], { type: "text/plain" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${label}.txt`;
    link.click();
  };

  const handleClearAll = () => {
    if (window.confirm(t("Clear all history? This cannot be undone."))) {
      updateHistory([]);
      toast({ message: t("All history cleared"), type: "success" });
    }
  };

  return (
    <motion.div
      className="max-w-5xl mx-auto px-4 py-10 text-white"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
        <h1 className="text-3xl font-bold">{t("Your History")}</h1>
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder={t("Search history...")}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm focus:outline-none focus:border-teal-500"
          />
          <button
            onClick={handleClearAll}
            className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm transition"
          >
            {t("Clear All")}
          </button>
        </div>
      </div>

      {history.length === 0 ? (
        <p className="text-zinc-400 text-sm">{t("No past sessions found.")}</p>
      ) : (
        <div className="space-y-6">
          {currentItems.map((h) => (
            <div
              key={h.id}
              className="bg-zinc-900 border border-zinc-700 rounded-xl p-5 shadow-md"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div
                    className="cursor-pointer"
                    onClick={() =>
                      setExpandedId(expandedId === h.id ? null : h.id)
                    }
                  >
                    <h2 className="text-lg font-semibold mb-1">{h.label}</h2>
                    <p className="text-sm text-zinc-400 mb-2">{h.date}</p>
                  </div>
                  <p
                    className={`text-sm text-zinc-300 whitespace-pre-wrap transition-max-h overflow-hidden ${
                      expandedId === h.id ? "max-h-screen" : "max-h-20"
                    }`}
                  >
                    {h.preview}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-2 ml-4">
                  <button
                    onClick={() => handleDownload(h.preview, h.label)}
                    className="flex items-center gap-1 px-3 py-1 bg-teal-600 hover:bg-teal-700 text-white text-xs rounded transition"
                  >
                    <Download className="w-4 h-4" />
                    {t("Download")}
                  </button>
                  <button
                    onClick={() => handleDelete(h.id)}
                    className="flex items-center gap-1 px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition"
                  >
                    <Trash2 className="w-4 h-4" />
                    {t("Delete")}
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* Pagination controls */}
          <div className="flex justify-center items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-400 rounded transition disabled:opacity-50"
            >
              {t("Previous")}
            </button>
            <span className="text-sm">
              {page} / {pageCount}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
              disabled={page === pageCount}
              className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-400 rounded transition disabled:opacity-50"
            >
              {t("Next")}
            </button>
          </div>
        </div>
      )}

      <div className="mt-8 flex justify-center">
        <button
          onClick={() => navigate("/recover")}
          className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 border border-blue-500 text-blue-300 hover:text-white rounded-lg text-sm transition"
        >
          <RotateCcw className="w-4 h-4" />
          {t("Recover Deleted Files")}
        </button>
      </div>
    </motion.div>
  );
}


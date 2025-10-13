import React, { useState } from "react";
import { motion } from "framer-motion";
import { Download, RotateCcw, ArrowLeft } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

export default function RecoverDeletedPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [deletedItems, setDeletedItems] = useState([
    { id: 1, label: "Meeting Notes", date: "2025-06-20", content: "These are meeting notes." },
    { id: 2, label: "Podcast Summary", date: "2025-06-18", content: "Podcast summary transcript." }
  ]);

  const handleRecover = (id) => {
    setDeletedItems((prev) => prev.filter((item) => item.id !== id));
    // Add recovery logic here
  };

  const handleDownload = (text, filename) => {
    const blob = new Blob([text], { type: "text/plain" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
  };

  return (
    <motion.div
      className="max-w-4xl mx-auto px-4 py-10 text-white"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h1 className="text-3xl font-bold mb-6">{t("Recover Deleted Files")}</h1>

      {deletedItems.length === 0 ? (
        <p className="text-zinc-400 text-sm">{t("No deleted items to recover.")}</p>
      ) : (
        <div className="grid gap-6">
          {deletedItems.map((item) => (
            <div
              key={item.id}
              className="bg-zinc-900 border border-zinc-700 rounded-xl p-5 shadow-md"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-lg font-semibold mb-1">{item.label}</h2>
                  <p className="text-sm text-zinc-400 mb-2">{item.date}</p>
                  <p className="text-sm text-zinc-300 max-h-24 overflow-hidden whitespace-pre-wrap">
                    {item.content}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-2 ml-4">
                  <button
                    onClick={() => handleRecover(item.id)}
                    className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded flex items-center gap-1"
                  >
                    <RotateCcw className="w-4 h-4" />
                    {t("Recover")}
                  </button>
                  <button
                    onClick={() => handleDownload(item.content, `${item.label}.txt`)}
                    className="text-xs bg-teal-600 hover:bg-teal-700 text-white px-3 py-1 rounded flex items-center gap-1"
                  >
                    <Download className="w-4 h-4" />
                    {t("Download")}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-10 flex justify-center">
        <button
          onClick={() => navigate("/history")}
          className="text-sm bg-zinc-700 hover:bg-zinc-600 text-white px-4 py-2 rounded-lg flex items-center gap-1"
        >
          <ArrowLeft className="w-4 h-4" /> {t("Back to History")}
        </button>
      </div>
    </motion.div>
  );
}

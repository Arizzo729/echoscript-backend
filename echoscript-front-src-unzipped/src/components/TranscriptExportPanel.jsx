// src/components/TranscriptExportPanel.jsx
import React, { useState } from "react";
import { FileDown, ChevronDown, ChevronUp } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function TranscriptExportPanel({ transcriptText, segments }) {
  const [open, setOpen] = useState(false);

  const handleDownload = (type) => {
    let blob, filename;

    const plainText = transcriptText || "No transcript available.";
    const baseFilename = `EchoScript_Transcript_${Date.now()}`;

    switch (type) {
      case "txt":
        blob = new Blob([plainText], { type: "text/plain;charset=utf-8" });
        filename = `${baseFilename}.txt`;
        break;

      case "json":
        blob = new Blob(
          [JSON.stringify({ transcript: plainText, segments }, null, 2)],
          { type: "application/json" }
        );
        filename = `${baseFilename}.json`;
        break;

      case "html": {
        const safe = escapeHtml(plainText);
        const html = `<!doctype html><html><head><meta charset="utf-8"><title>Transcript</title>
          <style>body{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell;
          background:#0b0b0e;color:#e5e7eb;padding:24px} pre{white-space:pre-wrap}</style></head>
          <body><h1>Transcript</h1><pre>${safe}</pre></body></html>`;
        blob = new Blob([html], { type: "text/html;charset=utf-8" });
        filename = `${baseFilename}.html`;
        break;
      }

      case "srt": {
        if (!segments || segments.length === 0) {
          alert("No segments to export as SRT.");
          return;
        }
        const srt = segments
          .map((seg, i) => {
            const start = formatSrtTime(seg.start);
            const end = formatSrtTime(seg.end);
            const text = (seg.text || "").trim();
            return `${i + 1}\n${start} --> ${end}\n${text}\n`;
          })
          .join("\n");
        blob = new Blob([srt], { type: "text/plain;charset=utf-8" });
        filename = `${baseFilename}.srt`;
        break;
      }

      case "docx": {
        // Minimal placeholder DOCX (won't render complex formatting)
        const xml =
          `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
           <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
             <w:body><w:p><w:r><w:t>${escapeXml(plainText)}</w:t></w:r></w:p></w:body>
           </w:document>`;
        blob = new Blob([xml], {
          type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        });
        filename = `${baseFilename}.docx`;
        break;
      }

      default:
        return;
    }

    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
  };

  // Proper SRT time: HH:MM:SS,mmm
  const formatSrtTime = (secondsFloat) => {
    const totalMs = Math.max(0, Math.round(Number(secondsFloat || 0) * 1000));
    const hours = Math.floor(totalMs / 3600000);
    const minutes = Math.floor((totalMs % 3600000) / 60000);
    const seconds = Math.floor((totalMs % 60000) / 1000);
    const millis = totalMs % 1000;
    const pad = (n, len = 2) => String(n).padStart(len, "0");
    return `${pad(hours)}:${pad(minutes)}:${pad(seconds)},${pad(millis, 3)}`;
  };

  const escapeHtml = (str) =>
    String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

  const escapeXml = (str) =>
    String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

  return (
    <div className="relative inline-block text-left">
      <button
        onClick={() => setOpen((o) => !o)}
        className="px-5 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-semibold flex items-center gap-2 shadow transition-all"
      >
        <FileDown size={18} />
        Export
        {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.ul
            className="absolute right-0 mt-2 w-48 bg-zinc-900 border border-zinc-700 rounded-lg shadow-lg z-50 overflow-hidden"
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
          >
            {[
              { key: "txt", label: ".TXT" },
              { key: "html", label: ".HTML" },
              { key: "docx", label: ".DOCX" },
              { key: "srt", label: ".SRT (subtitles)" },
              { key: "json", label: ".JSON (raw)" },
            ].map(({ key, label }) => (
              <li
                key={key}
                onClick={() => handleDownload(key)}
                className="px-4 py-2 hover:bg-teal-600 text-zinc-200 hover:text-white cursor-pointer text-sm transition"
              >
                {label}
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}

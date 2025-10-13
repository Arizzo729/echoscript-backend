// src/pages/VideoUpload.jsx
import React, { useState } from "react";
import { motion } from "framer-motion";
import { Upload, FileVideo, FileText, Subtitles, Download, Info, Languages } from "lucide-react";
import { useTranslation } from "react-i18next";

const ACCEPTED_FORMATS = ["mp4", "mkv", "avi", "mov", "webm"];
const MAX_FILE_SIZE_MB = 300;
const SUPPORTED_SUB_LANGS = [
  { code: "en", label: "English" }, { code: "es", label: "Spanish" }, { code: "fr", label: "French" },
  { code: "zh", label: "Chinese" }, { code: "hi", label: "Hindi" }, { code: "de", label: "German" },
  { code: "ar", label: "Arabic" }
];

const API_BASE = (import.meta.env.VITE_API_BASE ?? "/api").replace(/\/+$/, "");
const VIDEO_TASK_URL = `${API_BASE}/video-task`;

export default function VideoUpload() {
  const { t } = useTranslation();
  const [videoFile, setVideoFile] = useState(null);
  const [taskType, setTaskType] = useState("transcription");
  const [translateOutput, setTranslateOutput] = useState(false);
  const [subtitleLang, setSubtitleLang] = useState("en");
  const [status, setStatus] = useState(null);
  const [resultText, setResultText] = useState("");

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const ext = file.name.split(".").pop().toLowerCase();
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) return setStatus("file_too_large"), setVideoFile(null);
    if (!ACCEPTED_FORMATS.includes(ext)) return setStatus("invalid_format"), setVideoFile(null);
    setStatus(null); setVideoFile(file); setResultText("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!videoFile) return;
    setStatus("processing");

    const formData = new FormData();
    formData.append("file", videoFile);
    formData.append("type", taskType);
    formData.append("language", "auto");
    if (taskType === "transcription" && translateOutput) formData.append("translate", "true");
    if (taskType === "subtitles") formData.append("subtitle_target", subtitleLang);

    try {
      const res = await fetch(VIDEO_TASK_URL, { method: "POST", body: formData });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
      setResultText(data?.result || t("Task completed successfully."));
      setStatus("success");
    } catch (err) {
      console.error("video-task failed:", err);
      setStatus("error");
    }
  };

  const handleDownload = () => {
    const blob = new Blob([resultText], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${taskType}_result.txt`;
    a.click();
  };

  return (
    <motion.div className="max-w-4xl mx-auto px-6 py-16 text-white"
      initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
      <div className="space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-extrabold">🎬 Upload & Transcribe Video</h1>
          <p className="text-zinc-400 text-sm">
            Supports MP4, MKV, AVI, MOV and more. Choose transcription or subtitle generation.
          </p>
        </div>

        <form onSubmit={handleSubmit}
          className="grid gap-6 bg-zinc-900 p-6 rounded-xl border border-zinc-800 shadow-lg">
          <label className="flex items-center gap-3 p-4 border border-zinc-700 rounded-lg bg-zinc-800 cursor-pointer hover:bg-zinc-700">
            <FileVideo className="w-5 h-5 text-teal-400" />
            <span>{videoFile ? videoFile.name : t("Choose a video file")}</span>
            <input type="file" accept="video/*" onChange={handleFileChange} className="hidden" />
          </label>

          <div className="flex gap-4">
            <button type="button" onClick={() => setTaskType("transcription")}
              className={`flex-1 px-4 py-2 rounded-lg border ${
                taskType === "transcription" ? "bg-teal-600 border-teal-500" : "bg-zinc-800 border-zinc-700"}`}>
              <FileText className="w-4 h-4 inline-block mr-1" /> {t("Transcription")}
            </button>
            <button type="button" onClick={() => setTaskType("subtitles")}
              className={`flex-1 px-4 py-2 rounded-lg border ${
                taskType === "subtitles" ? "bg-teal-600 border-teal-500" : "bg-zinc-800 border-zinc-700"}`}>
              <Subtitles className="w-4 h-4 inline-block mr-1" /> {t("Subtitles")}
            </button>
          </div>

          {taskType === "transcription" && (
            <label className="flex items-center gap-3 text-sm text-zinc-300 px-2">
              <input type="checkbox" checked={translateOutput}
                onChange={() => setTranslateOutput(!translateOutput)} className="accent-teal-500" />
              {t("Translate output to English")}
            </label>
          )}

          {taskType === "subtitles" && (
            <div className="flex flex-col gap-2">
              <label className="text-sm text-zinc-300">{t("Choose subtitle language")}</label>
              <select value={subtitleLang} onChange={(e) => setSubtitleLang(e.target.value)}
                className="bg-zinc-800 text-white border border-zinc-700 rounded px-3 py-2 text-sm">
                {SUPPORTED_SUB_LANGS.map((lang) => (
                  <option key={lang.code} value={lang.code}>{lang.label}</option>
                ))}
              </select>
            </div>
          )}

          <button type="submit"
            className="bg-teal-600 hover:bg-teal-700 text-white py-2 px-6 rounded-lg flex items-center justify-center gap-2"
            disabled={!videoFile || status === "processing"}>
            <Upload className="w-4 h-4" />
            {status === "processing" ? t("Processing...") : t("Submit")}
          </button>

          {status === "success" && (
            <div className="space-y-3">
              <p className="text-green-400">✅ {t("Video processed successfully.")}</p>
              {resultText && (
                <div className="bg-zinc-800 p-4 rounded border border-zinc-700">
                  <pre className="text-sm text-zinc-200 whitespace-pre-wrap">{resultText}</pre>
                  <button onClick={handleDownload}
                    className="mt-3 text-sm text-teal-400 flex items-center gap-2 hover:underline">
                    <Download className="w-4 h-4" /> {t("Download Result")}
                  </button>
                </div>
              )}
            </div>
          )}

          {status === "error"        && <p className="text-red-400">❌ {t("There was an error. Please try again.")}</p>}
          {status === "file_too_large" && <p className="text-red-400">⚠️ {t("File is too large. Max size is")} {MAX_FILE_SIZE_MB}MB.</p>}
          {status === "invalid_format" && <p className="text-red-400">⚠️ {t("Unsupported file format. Accepted formats:")} {ACCEPTED_FORMATS.join(", ").toUpperCase()}</p>}
        </form>

        <div className="text-sm text-zinc-400 bg-zinc-800 border border-zinc-700 rounded-lg p-4 space-y-2">
          <p><Info className="inline-block w-4 h-4 text-blue-400 mr-1" />
            Transcription and subtitle files will be downloadable after processing.</p>
          <p><Languages className="inline-block w-4 h-4 text-teal-400 mr-1" />
            Language will be auto-detected. Translation and subtitle output is supported.</p>
          <p className="text-xs italic text-zinc-500">🌍 {t("More language support coming soon!")}</p>
        </div>
      </div>
    </motion.div>
  );
}


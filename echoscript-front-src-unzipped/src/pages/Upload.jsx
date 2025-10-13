// src/pages/Upload.jsx
import React, { useState, useCallback, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";

import UploadAndTranscribe from "../components/UploadAndTranscribe";
import PaywallModal from "../components/PaywallModal";
import CountdownSelector from "../components/CountdownSelector";
import LiveWaveform from "../components/LiveWaveform";
import TranscriptEditor from "../components/TranscriptEditor";
import TranscriptExportPanel from "../components/TranscriptExportPanel";

import {
  Mic,
  Timer,
  Download,
  Globe,
  FileText,
  Subtitles,
  Info,
  Upload as UploadIcon,
  StopCircle,
  Play,
} from "lucide-react";

const AUDIO = ["mp3", "wav", "flac", "m4a", "aac", "ogg", "webm"];
const VIDEO = ["mp4", "mkv", "mov"];
const MAX_MB = 500;

// ✅ Centralized API base
const API_BASE = import.meta.env.VITE_API_BASE || "";

/**
 * Simple recorder using MediaRecorder.
 * - start(): asks for mic, starts recording, updates state
 * - stop(): stops, returns a File (webm) we can pass to handleFile
 */
function useSimpleRecorder() {
  const [recording, setRecording] = useState(false);
  const [permissionError, setPermissionError] = useState("");
  const mediaStreamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const start = async () => {
    setPermissionError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      chunksRef.current = [];
      const rec = new MediaRecorder(stream, { mimeType: "audio/webm" });
      rec.ondataavailable = (e) => e.data && chunksRef.current.push(e.data);
      rec.start();
      mediaRecorderRef.current = rec;
      setRecording(true);
    } catch (e) {
      setPermissionError(
        e?.name === "NotAllowedError"
          ? "Microphone permission denied."
          : e?.message || "Unable to access microphone."
      );
    }
  };

  const stop = async () => {
    const rec = mediaRecorderRef.current;
    if (!rec) return null;
    return new Promise((resolve) => {
      rec.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        chunksRef.current = [];
        // stop tracks
        mediaStreamRef.current?.getTracks()?.forEach((t) => t.stop());
        mediaStreamRef.current = null;
        mediaRecorderRef.current = null;
        setRecording(false);
        // Wrap in a File so downstream UI still shows a name/size
        const file = new File([blob], `recording-${Date.now()}.webm`, {
          type: "audio/webm",
        });
        resolve(file);
      };
      rec.stop();
    });
  };

  return { recording, permissionError, start, stop };
}

export default function UploadPage() {
  const { t } = useTranslation();

  // UI state
  const [countdown, setCountdown] = useState(3);
  const [file, setFile] = useState(null);
  const [transcript, setTranscript] = useState("");
  const [translated, setTranslated] = useState("");
  const [translateEnabled, setTranslateEnabled] = useState(false);
  const [paywall, setPaywall] = useState(null);
  const [note, setNote] = useState(null);

  // Recorder hook
  const { recording, permissionError, start, stop } = useSimpleRecorder();

  // Restore draft for a specific file
  useEffect(() => {
    if (!file) return;
    const key = `draft_${file.name}`;
    try {
      const draft = localStorage.getItem(key);
      if (draft) {
        const d = JSON.parse(draft);
        setTranscript(d.transcript || "");
        setTranslated(d.translated || "");
        setNote(t("Loaded previous draft."));
      }
    } catch {
      /* ignore */
    }
  }, [file, t]);

  // Auto-clear notes
  useEffect(() => {
    if (!note) return;
    const id = setTimeout(() => setNote(null), 3000);
    return () => clearTimeout(id);
  }, [note]);

  const handleFile = useCallback(
    (uploaded) => {
      if (!uploaded) return;
      const ext = uploaded.name.split(".").pop()?.toLowerCase() || "";
      const valid = AUDIO.includes(ext) || VIDEO.includes(ext);
      const tooBig = uploaded.size > MAX_MB * 1024 * 1024;

      if (!valid || tooBig) {
        alert(
          `${t("Invalid file or too large")} (max ${MAX_MB}MB). ${t("Accepted formats")}: ${[
            ...AUDIO,
            ...VIDEO,
          ]
            .map((f) => f.toUpperCase())
            .join(", ")}.`
        );
        return;
      }
      setFile(uploaded);
      setTranscript("");
      setTranslated("");
    },
    [t]
  );

  const onInputChange = (e) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  };

  const handleTranscript = useCallback(
    (res) => {
      if (!res) return;
      if (res?.status === 403 && res.detail) {
        setPaywall(res.detail);
        setTranscript("");
        setTranslated("");
        return;
      }
      setPaywall(null);

      if (res?.detail && typeof res.detail === "string") {
        setNote(res.detail);
      }

      const tt = res.transcript ?? res.text ?? "";
      setTranscript(tt);
      setTranslated(translateEnabled && tt ? `🌍 [${t("Translated")}]: ${tt}` : "");
    },
    [translateEnabled, t]
  );

  const downloadText = useCallback((txt, name) => {
    if (!txt) return;
    const blob = new Blob([txt], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
  }, []);

  const saveDraft = () => {
    if (!file) return;
    localStorage.setItem(
      `draft_${file.name}`,
      JSON.stringify({
        transcript,
        translated,
        time: Date.now(),
      })
    );
    setNote(t("Draft saved."));
  };

  // Submit transcript text to your API (unchanged)
  const submit = () => {
    if (!file) return;
    fetch(`${API_BASE}/api/submitTranscript`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        fileName: file.name,
        transcript,
        translated: translateEnabled ? translated : null,
      }),
    })
      .then(async (r) => {
        const ct = r.headers.get("content-type");
        if (!ct || !ct.includes("application/json"))
          throw new Error("Unexpected server response");
        const j = await r.json();
        if (!r.ok) throw new Error(j.detail || "Server error");
        setNote(t("Submitted successfully!"));
      })
      .catch((e) => setNote(`${t("Submission failed.")} ${e.message || ""}`));
  };

  const onDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer?.files?.[0];
    if (f) handleFile(f);
  };

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="min-h-screen px-2 sm:px-5 py-7 sm:py-14 bg-gradient-to-b from-zinc-950 via-zinc-900 to-zinc-950 text-white"
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        <div className="max-w-3xl mx-auto space-y-9">
          <div className="text-center space-y-1">
            <h1 className="text-2xl xs:text-3xl md:text-4xl font-extrabold tracking-tight">
              {t("Upload or Record Audio/Video")}
            </h1>
            <p className="text-zinc-400 text-base">
              {t("Supports")} MP3, WAV, MP4, MKV, MOV, FLAC —{" "}
              {t("click or drag to upload, or record live.")}
            </p>
          </div>

          {note && (
            <div className="text-center text-sm text-teal-300 bg-zinc-800/70 px-4 py-2 rounded-lg">
              {note}
            </div>
          )}
          {permissionError && (
            <div className="text-center text-sm text-red-400 bg-zinc-900/70 px-4 py-2 rounded-lg">
              {permissionError}
            </div>
          )}

          {/* === Primary controls row (Upload + Record + Options) === */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Upload */}
            <label className="flex items-center justify-center gap-3 bg-zinc-800 rounded-xl px-4 py-4 border border-zinc-700 cursor-pointer hover:bg-zinc-700 transition">
              <UploadIcon className="w-5 h-5 text-teal-400" />
              <span className="text-sm">
                {file ? file.name : t("Choose a file")}
              </span>
              <input
                type="file"
                accept={[
                  ...AUDIO.map((x) => "." + x),
                  ...VIDEO.map((x) => "." + x),
                  "audio/*",
                  "video/*",
                ].join(",")}
                onChange={onInputChange}
                className="hidden"
              />
            </label>

            {/* Countdown + Translate */}
            <div className="flex items-center justify-between gap-3 bg-zinc-800 rounded-xl px-4 py-4 border border-zinc-700">
              <div className="flex items-center gap-2">
                <Timer className="w-5 h-5 text-teal-400" />
                <CountdownSelector value={countdown} onChange={setCountdown} />
              </div>
              <div className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-yellow-400" />
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    className="form-checkbox accent-teal-600"
                    checked={translateEnabled}
                    onChange={() => setTranslateEnabled((x) => !x)}
                    aria-label={t("Enable translation")}
                  />
                  {t("Translate")}
                </label>
              </div>
            </div>

            {/* Record */}
            <div className="flex items-center justify-between gap-3 bg-zinc-800 rounded-xl px-4 py-4 border border-zinc-700">
              <div className="flex items-center gap-2">
                <Mic className="w-5 h-5 text-emerald-400" />
                <span className="text-sm text-zinc-300">
                  {recording ? t("Recording…") : t("Ready")}
                </span>
              </div>
              {!recording ? (
                <button
                  onClick={start}
                  className="inline-flex items-center gap-2 px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-semibold transition"
                >
                  <Play className="w-4 h-4" />
                  {t("Start")}
                </button>
              ) : (
                <button
                  onClick={async () => {
                    const f = await stop();
                    if (f) handleFile(f);
                  }}
                  className="inline-flex items-center gap-2 px-3 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-semibold transition"
                >
                  <StopCircle className="w-4 h-4" />
                  {t("Stop & Use")}
                </button>
              )}
            </div>
          </div>

          {/* Live waveform (while recording) */}
          {recording && <LiveWaveform sourceType="mic" />}

          {/* Pipeline: when we have a file selected/recorded */}
          {file && (
            <UploadAndTranscribe
              fileInput={file}
              countdown={countdown}
              translate={translateEnabled}
              onRecordingStart={() => {}}
              onRecordingEnd={() => {}}
              onTranscriptComplete={handleTranscript}
            />
          )}

          {/* Results + tools */}
          {!paywall && transcript && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-7">
                <div className="p-5 bg-zinc-900 rounded-2xl border border-zinc-800 space-y-3 shadow">
                  <h3 className="font-semibold text-lg text-white flex gap-2 items-center">
                    <FileText className="w-5 h-5 text-teal-400" />
                    {t("Transcript")}
                  </h3>
                  <TranscriptEditor value={transcript} onChange={setTranscript} />
                </div>

                {translateEnabled && translated && (
                  <div className="p-5 bg-zinc-900 rounded-2xl border border-zinc-800 space-y-3 shadow">
                    <h3 className="font-semibold text-lg text-white flex gap-2 items-center">
                      <Subtitles className="w-5 h-5 text-yellow-400" />
                      {t("Translated Output")}
                    </h3>
                    <pre className="text-zinc-300 text-sm whitespace-pre-wrap max-h-64 overflow-auto">
                      {translated}
                    </pre>
                    <button
                      onClick={() => downloadText(translated, "translated.txt")}
                      className="text-sm text-yellow-300 flex items-center gap-2 hover:underline"
                    >
                      <Download className="w-4 h-4" /> {t("Download Translation")}
                    </button>
                  </div>
                )}
              </div>

              <div className="mt-7 flex flex-col sm:flex-row justify-center items-center gap-4">
                <TranscriptExportPanel transcriptText={transcript} />
                <button
                  onClick={saveDraft}
                  disabled={!transcript}
                  className="px-6 py-2 bg-blue-600 text-white rounded-xl shadow hover:bg-blue-700 disabled:opacity-50 font-semibold transition"
                >
                  {t("Save Draft")}
                </button>
                <button
                  onClick={submit}
                  disabled={!transcript}
                  className="px-6 py-2 bg-green-600 text-white rounded-xl shadow hover:bg-green-700 disabled:opacity-50 font-semibold transition"
                >
                  {t("Submit for Review")}
                </button>
              </div>
            </>
          )}

          {/* Help box */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 text-base text-zinc-400 space-y-3 mt-7 shadow">
            <p className="flex items-center gap-2">
              <Mic className="w-4 h-4 text-teal-400" />{" "}
              {t(
                "Record or upload your voice or video — EchoScript will auto-clean and transcribe it."
              )}
            </p>
            <p className="flex items-center gap-2">
              <Info className="w-4 h-4 text-zinc-400" /> {t(`Files up to ${MAX_MB}MB are supported.`)}
            </p>
          </div>
        </div>
      </motion.div>

      {paywall && <PaywallModal info={paywall} onClose={() => setPaywall(null)} />}
    </>
  );
}

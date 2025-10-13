// src/components/UploadAndTranscribe.jsx
import React, { useEffect, useRef, useState } from "react";
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";

const API_BASE = (import.meta.env.VITE_API_BASE ?? "/api").replace(/\/+$/, "");
const TRANSCRIBE_URL = `${API_BASE}/transcribe`;

export default function UploadAndTranscribe({
  fileInput,            // File | null
  countdown = 0,        // seconds before auto-start
  translate = false,    // (UI flag only — backend stub ignores for now)
  onRecordingStart,     // () => void
  onRecordingEnd,       // () => void
  onTranscriptComplete, // (json) => void
}) {
  const [step, setStep] = useState("idle"); // idle | waiting | uploading | done | error
  const [error, setError] = useState("");
  const timerRef = useRef(null);
  const abortRef = useRef(null);

  // kick off after countdown whenever file changes
  useEffect(() => {
    clearTimer();
    if (!fileInput) { setStep("idle"); return; }

    setStep(countdown > 0 ? "waiting" : "uploading");
    if (countdown > 0) {
      let remaining = countdown;
      timerRef.current = setInterval(() => {
        remaining -= 1;
        if (remaining <= 0) {
          clearTimer();
          doUpload();
        }
      }, 1000);
    } else {
      doUpload();
    }

    return () => {
      clearTimer();
      if (abortRef.current) abortRef.current.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileInput, countdown]);

  const clearTimer = () => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  };

  async function doUpload() {
    try {
      setError("");
      setStep("uploading");
      onRecordingStart?.();

      const fd = new FormData();
      fd.append("file", fileInput);
      // pass language; you can wire a selector later
      const url = `${TRANSCRIBE_URL}?language=en${translate ? "&translate=true" : ""}`;

      abortRef.current = new AbortController();
      const res = await fetch(url, { method: "POST", body: fd, signal: abortRef.current.signal });
      const ct = res.headers.get("content-type") || "";
      const payload = ct.includes("application/json")
        ? await res.json()
        : { detail: await res.text() };

      if (!res.ok) throw new Error(payload?.detail || `HTTP ${res.status}`);

      // Hand result back to the page
      onTranscriptComplete?.(payload);
      setStep("done");
    } catch (e) {
      if (e?.name === "AbortError") return;
      setError(e?.message || "Upload failed");
      setStep("error");
      onTranscriptComplete?.(null);
    } finally {
      onRecordingEnd?.();
    }
  }

  return (
    <div className="mt-6">
      {step === "waiting" && (
        <div className="text-sm text-zinc-300">Starting in {countdown}s…</div>
      )}
      {step === "uploading" && (
        <div className="flex items-center gap-2 text-zinc-300">
          <Loader2 className="w-4 h-4 animate-spin" />
          Uploading & transcribing…
        </div>
      )}
      {step === "done" && (
        <div className="flex items-center gap-2 text-emerald-400">
          <CheckCircle2 className="w-4 h-4" />
          Done
        </div>
      )}
      {step === "error" && (
        <div className="flex items-center gap-2 text-red-400">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}
    </div>
  );
}



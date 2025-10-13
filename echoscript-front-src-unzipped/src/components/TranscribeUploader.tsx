import React, { useRef, useState } from "react";
import { UploadCloud, CheckCircle, AlertCircle, Clipboard } from "lucide-react";

// Use Netlify proxy by default; allow override via VITE_API_BASE
const API_BASE = (import.meta.env.VITE_API_BASE ?? "/api").replace(/\/+$/, "");
const TRANSCRIBE_URL = `${API_BASE}/transcribe`;
const VIDEO_TASK_URL = `${API_BASE}/video-task`;

export default function TranscribeUploader() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | uploading | done | error
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null);
  const inputRef = useRef(null);

  const onPick = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setResult(null);
    setError("");
    setTaskStatus(null);
  };

  const onDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (!f) return;
    setFile(f);
    setResult(null);
    setError("");
    setTaskStatus(null);
  };

  const onDragOver = (e) => e.preventDefault();

  async function transcribe() {
    if (!file) return;
    setStatus("uploading");
    setError("");
    try {
      const fd = new FormData();
      fd.append("file", file);

      const res = await fetch(`${TRANSCRIBE_URL}?language=en`, {
        method: "POST",
        body: fd,
      });

      const ct = res.headers.get("content-type") || "";
      const data = ct.includes("application/json") ? await res.json() : { detail: await res.text() };

      if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
      setResult(data);
      setStatus("done");
    } catch (e) {
      setError(e?.message || "Transcription failed");
      setStatus("error");
    }
  }

  async function startVideoTask() {
    setTaskStatus("sending");
    try {
      const res = await fetch(VIDEO_TASK_URL, { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
      setTaskStatus(`queued: ${data?.task_id || "ok"}`);
    } catch (e) {
      setTaskStatus(`error: ${e?.message || "failed"}`);
    }
  }

  const copyText = () => {
    const text = result?.text || result?.transcript || "";
    if (!text) return;
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-semibold text-zinc-100 mb-6">Upload or Record Audio/Video</h1>

      <div
        className="border-2 border-dashed border-zinc-600 rounded-xl p-8 text-center text-zinc-300 hover:border-zinc-400 transition-colors cursor-pointer"
        onClick={() => inputRef.current?.click()}
        onDrop={onDrop}
        onDragOver={onDragOver}
      >
        <UploadCloud className="w-10 h-10 mx-auto mb-3 text-teal-400" />
        <p className="mb-2">{file ? <strong>{file.name}</strong> : "Click or drag a file here"}</p>
        <p className="text-xs text-zinc-400">MP3, WAV, MP4, MOV, MKV… up to 500MB</p>
        <input
          ref={inputRef}
          type="file"
          accept="audio/*,video/*"
          className="hidden"
          onChange={onPick}
        />
      </div>

      <div className="mt-4 flex gap-3">
        <button
          onClick={transcribe}
          disabled={!file || status === "uploading"}
          className="px-4 py-2 rounded-lg bg-teal-600 text-white disabled:opacity-50"
        >
          {status === "uploading" ? "Transcribing…" : "Transcribe"}
        </button>

        <button
          onClick={startVideoTask}
          className="px-4 py-2 rounded-lg border border-zinc-600 text-zinc-200 hover:bg-zinc-800"
        >
          Send /api/video-task
        </button>

        {taskStatus && <span className="text-sm text-zinc-400 self-center">{taskStatus}</span>}
      </div>

      {status === "error" && (
        <div className="mt-4 text-sm text-red-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {status === "done" && (
        <div className="mt-6 space-y-2">
          <div className="text-sm text-emerald-300 flex items-center gap-2">
            <CheckCircle className="w-4 h-4" />
            Transcript ready
          </div>
          <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-zinc-400">Transcript</span>
              <button onClick={copyText} className="text-xs text-teal-300 hover:underline">
                <Clipboard className="inline w-3 h-3 mr-1" />
                Copy
              </button>
            </div>
            <pre className="whitespace-pre-wrap text-sm text-zinc-100">
              {result?.text || result?.transcript || "(empty)"}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}



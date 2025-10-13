// src/components/MicCheck.tsx
import { useEffect, useRef, useState } from "react";

export default function MicCheck() {
  const [status, setStatus] = useState<"idle"|"ready"|"recording"|"error">("idle");
  const [error, setError] = useState<string>("");
  const mediaStreamRef = useRef<MediaStream|null>(null);
  const recorderRef = useRef<MediaRecorder|null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);
  const mimeTypeRef = useRef<string>("audio/webm");

  const getMic = async () => {
    try {
      setError("");
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 48000,
        },
        video: false,
      });
      mediaStreamRef.current = stream;
      setStatus("ready");
    } catch (e:any) {
      setError(e?.message || "Microphone permission denied");
      setStatus("error");
    }
  };

  const startRecording = () => {
    if (!mediaStreamRef.current) return;
    const preferredTypes = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/mp4",
    ];
    let mimeType = "";
    for (const t of preferredTypes) {
      if (MediaRecorder.isTypeSupported(t)) { mimeType = t; break; }
    }
    if (!mimeType) mimeType = "audio/webm";
    mimeTypeRef.current = mimeType;

    const rec = new MediaRecorder(mediaStreamRef.current!, { mimeType });
    audioChunksRef.current = [];
    rec.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) audioChunksRef.current.push(e.data);
    };
    rec.onstart = () => setStatus("recording");
    rec.start(1000);
    recorderRef.current = rec;
  };

  const stopRecording = () => {
    recorderRef.current?.stop();
    recorderRef.current = null;
    setStatus("ready");
  };

  const playBack = () => {
    const blob = new Blob(audioChunksRef.current, { type: mimeTypeRef.current });
    const url = URL.createObjectURL(blob);
    const a = new Audio(url);
    a.play();
  };

  useEffect(() => {
    return () => {
      mediaStreamRef.current?.getTracks().forEach(t => t.stop());
    };
  }, []);

  return (
    <div className="p-4 space-y-3">
      <h2 className="text-xl font-semibold">Microphone Check</h2>
      <div className="flex gap-2">
        <button onClick={getMic} className="px-3 py-2 rounded bg-teal-600 text-white">Enable Mic</button>
        <button onClick={startRecording} disabled={status!=="ready"} className="px-3 py-2 rounded bg-blue-600 text-white disabled:opacity-50">Start</button>
        <button onClick={stopRecording} disabled={status!=="recording"} className="px-3 py-2 rounded bg-rose-600 text-white disabled:opacity-50">Stop</button>
        <button onClick={playBack} className="px-3 py-2 rounded bg-gray-800 text-white">Play Back</button>
      </div>
      <div>Status: <span className="font-mono">{status}</span></div>
      {error && <div className="text-rose-600">{error}</div>}
    </div>
  );
}


// src/components/LiveCaptions.tsx
import { useEffect, useRef, useState } from "react";
import { openTranscribeSocket } from "../lib/liveCaptionClient";

type Caption = { id: string; text: string; start: number; end?: number; final?: boolean; };

export default function LiveCaptions() {
  const [captions, setCaptions] = useState<Caption[]>([]);
  const [listening, setListening] = useState(false);
  const wsRef = useRef<WebSocket|null>(null);
  const recRef = useRef<MediaRecorder|null>(null);
  const streamRef = useRef<MediaStream|null>(null);

  const start = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
      video: false
    });
    streamRef.current = stream;

    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : (MediaRecorder.isTypeSupported("audio/mp4") ? "audio/mp4" : "audio/webm");

    const ws = openTranscribeSocket();
    ws.binaryType = "arraybuffer";
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data as string);
      // Expect schema: {type: "partial"|"final", id, text, start, end?}
      setCaptions((prev) => {
        const others = prev.filter(c => c.id !== msg.id);
        const next = { ...msg, final: msg.type === "final" };
        return [...others, next];
      });
    };
    ws.onopen = () => {
      const rec = new MediaRecorder(stream, { mimeType });
      rec.ondataavailable = async (e) => {
        if (!e.data.size) return;
        const arrayBuf = await e.data.arrayBuffer();
        ws.send(arrayBuf);
      };
      rec.start(1000); // 1s chunks
      recRef.current = rec;
      wsRef.current = ws;
      setListening(true);
    };
    ws.onclose = () => stop();
    ws.onerror = () => stop();
  };

  const stop = () => {
    recRef.current?.stop();
    recRef.current = null;
    wsRef.current?.close();
    wsRef.current = null;
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    setListening(false);
  };

  useEffect(() => () => stop(), []);

  return (
    <div className="p-4 space-y-3">
      <h2 className="text-xl font-semibold">Live Captions</h2>
      <div className="flex gap-2">
        <button onClick={start} disabled={listening} className="px-3 py-2 rounded bg-teal-600 text-white disabled:opacity-50">Start</button>
        <button onClick={stop} disabled={!listening} className="px-3 py-2 rounded bg-rose-600 text-white disabled:opacity-50">Stop</button>
      </div>
      <div className="mt-4 bg-black/80 text-white p-3 rounded-lg min-h-16">
        {captions.sort((a,b)=>a.start-b.start).slice(-3).map(c => (
          <div key={c.id} className={c.final ? "opacity-100" : "opacity-60"}>{c.text}</div>
        ))}
      </div>
    </div>
  );
}

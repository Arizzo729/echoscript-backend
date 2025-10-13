// src/components/AudioWaveform.jsx
import React, { useEffect, useRef } from "react";

export default function AudioWaveform({ audioStream }) {
  const canvasRef = useRef(null);
  const rafRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const sourceRef = useRef(null);
  const dataRef = useRef(null);
  const roRef = useRef(null);

  // Size the canvas crisply for the current DPR
  const sizeCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = Math.max(1, window.devicePixelRatio || 1);
    const cssWidth = canvas.clientWidth || 600;
    const cssHeight = 100;
    canvas.width = Math.floor(cssWidth * dpr);
    canvas.height = Math.floor(cssHeight * dpr);
    canvas.style.width = `${cssWidth}px`;
    canvas.style.height = `${cssHeight}px`;
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); // scale drawing space
  };

  useEffect(() => {
    if (!audioStream) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    sizeCanvas();
    roRef.current = new ResizeObserver(sizeCanvas);
    roRef.current.observe(canvas);

    audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    analyserRef.current = audioCtxRef.current.createAnalyser();
    analyserRef.current.fftSize = 2048;

    // Connect stream -> analyser
    sourceRef.current = audioCtxRef.current.createMediaStreamSource(audioStream);
    sourceRef.current.connect(analyserRef.current);

    const bufferLength = analyserRef.current.fftSize;
    dataRef.current = new Uint8Array(bufferLength);

    const draw = () => {
      analyserRef.current.getByteTimeDomainData(dataRef.current);

      // clear
      ctx.fillStyle = "#0f172a"; // zinc-900
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // draw line in CSS pixels (we scaled CTX)
      const cssW = canvas.width / (window.devicePixelRatio || 1);
      const cssH = canvas.height / (window.devicePixelRatio || 1);

      ctx.lineWidth = 2;
      ctx.strokeStyle = "#14b8a6"; // teal-500
      ctx.beginPath();

      const sliceWidth = cssW / bufferLength;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const v = dataRef.current[i] / 128.0;
        const y = (v * cssH) / 2;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        x += sliceWidth;
      }

      ctx.lineTo(cssW, cssH / 2);
      ctx.stroke();

      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      try { sourceRef.current?.disconnect(); } catch {}
      try { analyserRef.current?.disconnect(); } catch {}
      try { audioCtxRef.current?.close(); } catch {}
      roRef.current?.disconnect();
      sourceRef.current = null;
      analyserRef.current = null;
      audioCtxRef.current = null;
    };
  }, [audioStream]);

  return (
    <div className="w-full max-w-3xl mx-auto mt-4">
      <canvas
        ref={canvasRef}
        className="w-full h-[100px] rounded-xl border border-zinc-700 shadow-md"
      />
    </div>
  );
}



// === LiveWaveform.jsx ===
import React, { useEffect, useRef, useState } from "react";

/**
 * LiveWaveform - High-fidelity real-time waveform visualizer.
 * Props:
 *  - sourceType: "mic" | "playback"
 *  - audioBlob: File | Blob (only required for playback)
 */
export default function LiveWaveform({ sourceType = "mic", audioBlob }) {
  const canvasRef = useRef(null);
  const [audioCtx, setAudioCtx] = useState(null);
  const [analyser, setAnalyser] = useState(null);
  const [source, setSource] = useState(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    let audioContext = new (window.AudioContext || window.webkitAudioContext)();
    let analyserNode = audioContext.createAnalyser();
    analyserNode.fftSize = 2048;
    analyserNode.smoothingTimeConstant = 0.88;
    const bufferLength = analyserNode.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    setAudioCtx(audioContext);
    setAnalyser(analyserNode);

    const draw = () => {
      requestAnimationFrame(draw);
      analyserNode.getByteTimeDomainData(dataArray);
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.beginPath();
      const sliceWidth = canvas.width / bufferLength;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * canvas.height) / 2;
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
        x += sliceWidth;
      }

      ctx.strokeStyle = "#14b8a6"; // teal-500
      ctx.lineWidth = 2;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";
      ctx.shadowColor = "#0f766e";
      ctx.shadowBlur = 6;
      ctx.stroke();
    };

    draw();

    if (sourceType === "mic") {
      navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
        const micSource = audioContext.createMediaStreamSource(stream);
        micSource.connect(analyserNode);
        setSource(micSource);
      }).catch(console.error);
    } else if (sourceType === "playback" && audioBlob) {
      const audioEl = new Audio();
      audioEl.src = URL.createObjectURL(audioBlob);
      audioEl.oncanplay = () => {
        const playbackSource = audioContext.createMediaElementSource(audioEl);
        playbackSource.connect(analyserNode);
        analyserNode.connect(audioContext.destination);
        setSource(playbackSource);
        audioEl.play();
      };
    }

    return () => {
      if (source) source.disconnect();
      if (analyserNode) analyserNode.disconnect();
      if (audioContext) audioContext.close();
    };
  }, [sourceType, audioBlob]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-24 rounded-lg bg-zinc-900 ring-1 ring-zinc-700"
    />
  );
}


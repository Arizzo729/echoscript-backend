import React, { useEffect, useRef } from "react";

export default function WaveformVisualizer({ isRecording }) {
  const canvasRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);
  const sourceRef = useRef(null);
  const animationRef = useRef(null);

  useEffect(() => {
    if (!isRecording) {
      cancelAnimationFrame(animationRef.current);
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      return;
    }

    const initAudio = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 2048;

        const source = audioCtx.createMediaStreamSource(stream);
        source.connect(analyser);

        const bufferLength = analyser.fftSize;
        const dataArray = new Uint8Array(bufferLength);

        analyserRef.current = analyser;
        dataArrayRef.current = dataArray;
        audioContextRef.current = audioCtx;
        sourceRef.current = source;

        draw();
      } catch (error) {
        console.error("Microphone access denied or error:", error);
      }
    };

    const draw = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      const ctx = canvas.getContext("2d");
      const analyser = analyserRef.current;
      const dataArray = dataArrayRef.current;
      const width = canvas.width;
      const height = canvas.height;

      const gradient = ctx.createLinearGradient(0, 0, width, 0);
      gradient.addColorStop(0, "#0ea5e9"); // sky blue
      gradient.addColorStop(1, "#14b8a6"); // teal

      const renderFrame = () => {
        animationRef.current = requestAnimationFrame(renderFrame);

        analyser.getByteTimeDomainData(dataArray);

        ctx.clearRect(0, 0, width, height);

        ctx.fillStyle = "#09090b";
        ctx.fillRect(0, 0, width, height);

        ctx.lineWidth = 2;
        ctx.strokeStyle = gradient;
        ctx.beginPath();

        const sliceWidth = width / dataArray.length;
        let x = 0;

        for (let i = 0; i < dataArray.length; i++) {
          const v = dataArray[i] / 128.0;
          const y = (v * height) / 2;

          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
          x += sliceWidth;
        }

        ctx.lineTo(width, height / 2);
        ctx.stroke();

        ctx.shadowColor = "#14b8a6";
        ctx.shadowBlur = 25;
      };

      renderFrame();
    };

    initAudio();

    return () => {
      cancelAnimationFrame(animationRef.current);
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
    };
  }, [isRecording]);

  return (
    <div className="w-full h-28 rounded-lg bg-zinc-900 overflow-hidden border border-zinc-700">
      <canvas
        ref={canvasRef}
        width={window.innerWidth * 0.8}
        height={112}
        className="w-full h-full"
      />
    </div>
  );
}

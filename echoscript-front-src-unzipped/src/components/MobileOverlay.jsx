// src/components/MobileOverlay.jsx
import React, { useRef, useEffect, useState } from "react";
import { X, Play, Pause, ChevronLeft, ChevronRight } from "lucide-react";

export default function MobileOverlay({ onClose }) {
  const overlayRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const dragOffset = useRef({ x: 0, y: 0 });
  const [pos, setPos] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("audio-overlay-pos")) || { x: 16, y: window.innerHeight - 180 };
    } catch {
      return { x: 16, y: window.innerHeight - 180 };
    }
  });
  const [playing, setPlaying] = useState(false);
  const [label, setLabel] = useState("Ambient");

  // sync DOM position when state changes
  useEffect(() => {
    const node = overlayRef.current;
    if (!node) return;
    node.style.left = `${pos.x}px`;
    node.style.top = `${pos.y}px`;
  }, [pos]);

  // touch drag handlers
  useEffect(() => {
    const node = overlayRef.current;
    if (!node) return;

    function onTouchStart(e) {
      setDragging(true);
      const touch = e.touches[0];
      const rect = node.getBoundingClientRect();
      dragOffset.current = { x: touch.clientX - rect.left, y: touch.clientY - rect.top };
      node.style.transition = "none";
    }

    function onTouchMove(e) {
      if (!dragging) return;
      const touch = e.touches[0];
      let x = touch.clientX - dragOffset.current.x;
      let y = touch.clientY - dragOffset.current.y;
      x = Math.max(0, Math.min(window.innerWidth - node.offsetWidth, x));
      y = Math.max(0, Math.min(window.innerHeight - node.offsetHeight - 80, y));
      node.style.left = `${x}px`;
      node.style.top = `${y}px`;
    }

    function onTouchEnd() {
      setDragging(false);
      node.style.transition = "left 0.13s, top 0.13s";
      const rect = node.getBoundingClientRect();
      const next = { x: Math.round(rect.left), y: Math.round(rect.top) };
      setPos(next);
      localStorage.setItem("audio-overlay-pos", JSON.stringify(next));
    }

    node.addEventListener("touchstart", onTouchStart, { passive: false });
    node.addEventListener("touchmove", onTouchMove, { passive: false });
    node.addEventListener("touchend", onTouchEnd, { passive: false });
    return () => {
      node.removeEventListener("touchstart", onTouchStart);
      node.removeEventListener("touchmove", onTouchMove);
      node.removeEventListener("touchend", onTouchEnd);
    };
  }, [dragging]);

  return (
    <div
      ref={overlayRef}
      style={{
        position: "fixed",
        left: `${pos.x}px`,
        top: `${pos.y}px`,
        zIndex: 9999,
        width: 260,
        height: 60,
        background: "rgba(24,24,30,0.95)",
        borderRadius: 16,
        boxShadow: "0 4px 24px 0 rgba(0,0,0,0.13)",
        border: "1.5px solid #14b8a6a6",
        backdropFilter: "blur(7px)",
        display: "flex",
        alignItems: "center",
        gap: 6,
        padding: "0 10px 0 8px",
        touchAction: "none",
        userSelect: "none",
      }}
      aria-label="Ambient audio overlay"
      role="dialog"
      tabIndex={-1}
    >
      <button
        type="button"
        aria-label="Previous"
        onClick={() => setLabel("Ambient ◀")}
        className="w-8 h-8 rounded-full flex items-center justify-center hover:scale-110 transition"
      >
        <ChevronLeft className="w-5 h-5 text-teal-400" />
      </button>

      <button
        type="button"
        aria-label={playing ? "Pause" : "Play"}
        onClick={() => setPlaying((v) => !v)}
        className="w-8 h-8 rounded-full flex items-center justify-center hover:scale-110 transition"
      >
        {playing ? <Pause className="w-5 h-5 text-teal-400" /> : <Play className="w-5 h-5 text-teal-400" />}
      </button>

      <button
        type="button"
        aria-label="Next"
        onClick={() => setLabel("Ambient ▶")}
        className="w-8 h-8 rounded-full flex items-center justify-center hover:scale-110 transition"
      >
        <ChevronRight className="w-5 h-5 text-teal-400" />
      </button>

      <span className="ml-1 mr-1 font-mono text-[0.83rem] text-teal-200 tracking-wider select-none">{label}</span>

      <button
        onClick={onClose}
        className="ml-auto flex items-center justify-center p-0 w-8 h-8 rounded-full hover:scale-110 transition"
        aria-label="Close"
      >
        <X className="w-4 h-4 text-teal-400" />
      </button>
    </div>
  );
}



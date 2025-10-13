import React, { useState, useEffect, useRef } from "react";
import ReactDOM from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import MobileHeader from "./MobileHeader";
import MobileBottomNav from "./MobileBottomNav";
import MobileOverlay from "./MobileOverlay";

function AudioModal({ open, onClose, children }) {
  const dialogRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const prevOverflow = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";

    const onKey = (e) => {
      if (e.key === "Escape") onClose?.();
      if (e.key === "Tab" && dialogRef.current) {
        const focusable = dialogRef.current.querySelectorAll(
          'a,button,input,textarea,select,[tabindex]:not([tabindex="-1"])'
        );
        if (!focusable.length) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener("keydown", onKey);
    // focus inside on open
    setTimeout(() => {
      if (!dialogRef.current) return;
      const el =
        dialogRef.current.querySelector("[autofocus]") ||
        dialogRef.current.querySelector(
          'button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])'
        );
      (el || dialogRef.current).focus();
    }, 0);

    return () => {
      document.documentElement.style.overflow = prevOverflow;
      document.removeEventListener("keydown", onKey);
    };
  }, [open, onClose]);

  if (!open) return null;

  const modal = (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Audio controls"
      className="fixed inset-0 z-[70] flex items-center justify-center"
    >
      <div
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
        aria-hidden="true"
      />
      <motion.div
        ref={dialogRef}
        tabIndex={-1}
        initial={{ opacity: 0, y: 30, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 20, scale: 0.98 }}
        transition={{ type: "spring", stiffness: 260, damping: 22 }}
        className="relative z-[71] w-[95vw] max-w-xl rounded-2xl border border-zinc-700 bg-zinc-900 p-4 shadow-2xl focus:outline-none"
      >
        <button
          onClick={onClose}
          className="absolute top-2 right-2 rounded-md border border-zinc-700/60 bg-zinc-800/60 px-2 py-1 text-sm text-zinc-200 hover:bg-zinc-700/60 focus:outline-none focus:ring-2 focus:ring-teal-400"
          aria-label="Close audio panel"
        >
          ✕
        </button>
        {children}
      </motion.div>
    </div>
  );

  return ReactDOM.createPortal(modal, document.body);
}

const BOTTOM_NAV_HEIGHT = 72;

function MobileLayout({ children }) {
  const [audioOpen, setAudioOpen] = useState(false);
  const [showShadow, setShowShadow] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => setShowShadow(el.scrollTop > 2);
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="relative flex h-dvh w-full flex-col bg-zinc-950 text-white">
      <div
        className={`sticky top-0 z-40 transition-shadow ${
          showShadow ? "shadow-lg shadow-black/20" : ""
        }`}
      >
        <MobileHeader
          onOpenAudio={() => setAudioOpen(true)}
          className="backdrop-blur bg-zinc-950/70 border-b border-zinc-800"
        />
      </div>

      <main
        ref={scrollRef}
        className="flex-1 overflow-y-auto"
        style={{
          paddingBottom: `calc(${BOTTOM_NAV_HEIGHT}px + env(safe-area-inset-bottom) + 16px)`,
        }}
      >
        {children}
      </main>

      <button
        onClick={() => setAudioOpen(true)}
        aria-label="Open audio overlay"
        className="fixed right-4 z-50 inline-flex h-12 w-12 items-center justify-center rounded-full border border-zinc-700 bg-zinc-900/90 backdrop-blur hover:bg-zinc-800 transition-colors"
        style={{
          bottom: `calc(${BOTTOM_NAV_HEIGHT}px + env(safe-area-inset-bottom) + 1rem)`,
        }}
      >
        <span className="inline-block w-5 h-5 rounded-full border border-teal-300" />
      </button>

      <AnimatePresence>
        <AudioModal open={audioOpen} onClose={() => setAudioOpen(false)}>
          <MobileOverlay onClose={() => setAudioOpen(false)} />
        </AudioModal>
      </AnimatePresence>

      <AnimatePresence>
        <motion.div
          initial={{ y: 80 }}
          animate={{ y: 0 }}
          exit={{ y: 80 }}
          transition={{ type: "spring", stiffness: 240, damping: 28 }}
          className="fixed bottom-0 left-0 right-0 z-50 pointer-events-auto"
          style={{
            height: `calc(${BOTTOM_NAV_HEIGHT}px + env(safe-area-inset-bottom))`,
            background: "transparent",
          }}
        >
          <MobileBottomNav />
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

export default MobileLayout;

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function LogoLoader({ duration = 2500, onComplete }) {
  const [visible, setVisible] = useState(true);

  const close = () => {
    setVisible(false);
    setTimeout(() => onComplete?.(), 500); // Allow fade-out to complete
  };

  useEffect(() => {
    const timer = setTimeout(close, duration);
    return () => clearTimeout(timer);
  }, [duration]);

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          key="logo-loader"
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-[9999] flex flex-col items-center justify-center px-6 text-center backdrop-blur-2xl bg-gradient-to-br from-white via-zinc-100 to-zinc-200 dark:from-zinc-950 dark:via-zinc-900 dark:to-zinc-800"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.6 }}
        >
          {/* 🔄 Logo animation */}
          <motion.img
            src="/EchoScriptAI_Animated.svg"
            alt="EchoScript.AI Logo Animation"
            className="w-48 h-48 mb-4 object-contain animate-pulse"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 1, ease: "easeOut" }}
          />

          {/* 🧠 Brand title */}
          <motion.h1
            className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-800 dark:text-white"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
          >
            EchoScript<span className="text-teal-500">.AI</span>
          </motion.h1>

          {/* 🎧 Slogan */}
          <motion.p
            className="text-sm sm:text-base mt-2 text-zinc-500 dark:text-zinc-400 whitespace-pre-line"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.6 }}
          >
            The Best Listener{"\n"}Understanding Everyone
          </motion.p>

          {/* ⏳ Progress bar */}
          <motion.div
            className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-teal-400 to-blue-400"
            initial={{ width: 0 }}
            animate={{ width: "100%" }}
            transition={{ duration: duration / 1000 }}
          />

          {/* 🔘 Skip button */}
          <button
            onClick={close}
            className="absolute bottom-5 right-5 text-sm px-4 py-2 rounded-md bg-white/20 dark:bg-zinc-700/30 text-zinc-800 dark:text-white backdrop-blur hover:bg-white/30 hover:dark:bg-zinc-600/40 transition-all shadow-lg"
          >
            Skip
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}


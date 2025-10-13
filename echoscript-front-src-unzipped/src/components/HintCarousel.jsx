// src/components/HintCarousel.jsx
import React, { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles } from "lucide-react";

const DEFAULT_HINTS = [
  { emoji: "🎙️", message: "Tap the mic to start live recording — we'll transcribe clearly in real time." },
  { emoji: "📂", message: "Upload audio/video files and get clean, timestamped transcripts." },
  { emoji: "✨", message: "Turn long conversations into summaries with one click." },
  { emoji: "🌐", message: "Switch languages easily — English, Spanish, and more." },
];

export default function HintCarousel({ hints }) {
  const items = useMemo(() => {
    const arr = Array.isArray(hints) && hints.length ? hints : DEFAULT_HINTS;
    return arr.filter(Boolean);
  }, [hints]);

  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (items.length <= 1) return;
    const timer = setInterval(() => setIndex((prev) => (prev + 1) % items.length), 7000);
    return () => clearInterval(timer);
  }, [items.length]);

  if (!items.length) return null;

  return (
    <div className="relative w-full max-w-xl mx-auto mt-8 text-center px-6">
      <div className="h-20 sm:h-16 flex items-center justify-center">
        <AnimatePresence mode="wait">
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.98 }}
            transition={{ duration: 0.6, ease: "easeInOut" }}
            className="text-base sm:text-lg text-zinc-300 font-medium leading-relaxed px-4"
          >
            <span className="mr-2">{items[index].emoji}</span>
            <span>{items[index].message}</span>
          </motion.div>
        </AnimatePresence>
      </div>

      {items.length > 1 && (
        <>
          <div className="flex justify-center gap-2 mt-3">
            {items.map((_, i) => (
              <button
                key={i}
                onClick={() => setIndex(i)}
                className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
                  i === index ? "bg-teal-400 shadow-sm scale-110" : "bg-zinc-600 hover:bg-zinc-500"
                }`}
                aria-label={`Hint ${i + 1}`}
              />
            ))}
          </div>
          <div className="absolute top-0 left-4 sm:left-6 animate-pulse text-teal-400">
            <Sparkles className="w-5 h-5" />
          </div>
        </>
      )}
    </div>
  );
}

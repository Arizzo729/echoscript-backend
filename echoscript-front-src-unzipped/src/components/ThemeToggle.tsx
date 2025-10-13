import React from "react";
import { useTheme } from "./useTheme";
import { motion, AnimatePresence } from "framer-motion";

/**
 * ThemeToggle — animated dark/light mode toggle
 * - Smooth SVG transitions
 * - Full accessibility
 * - Minimalist, elegant, mobile-friendly
 */
export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isLight = theme === "light";

  return (
    <button
      aria-label={`Switch to ${isLight ? "dark" : "light"} mode`}
      onClick={toggleTheme}
      className="p-2 rounded-lg bg-transparent hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 focus-visible:ring-offset-2"
      title={`Switch to ${isLight ? "dark" : "light"} mode`}
      type="button"
    >
      <AnimatePresence mode="wait" initial={false}>
        {isLight ? (
          <motion.svg
            key="sun"
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6 text-yellow-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            initial={{ opacity: 0, rotate: -90, scale: 0.8 }}
            animate={{ opacity: 1, rotate: 0, scale: 1 }}
            exit={{ opacity: 0, rotate: 90, scale: 0.8 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 3v1m0 16v1m8.485-9h1M3.515 12h1m12.02 6.364l.707.707M6.343 6.343l.707.707m12.02 0l-.707.707M6.343 17.657l-.707.707M12 7a5 5 0 100 10 5 5 0 000-10z"
            />
          </motion.svg>
        ) : (
          <motion.svg
            key="moon"
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6 text-blue-400"
            fill="currentColor"
            viewBox="0 0 24 24"
            initial={{ opacity: 0, rotate: 90, scale: 0.8 }}
            animate={{ opacity: 1, rotate: 0, scale: 1 }}
            exit={{ opacity: 0, rotate: -90, scale: 0.8 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
          >
            <path d="M21 12.79A9 9 0 1111.21 3a7 7 0 109.79 9.79z" />
          </motion.svg>
        )}
      </AnimatePresence>
    </button>
  );
}


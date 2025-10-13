import React from "react";
import { motion } from "framer-motion";

export default function ProgressBar({ value = 0, showLabel = false }) {
  const safeValue = Math.min(100, Math.max(0, value));

  return (
    <div
      className="relative w-full h-3 rounded-full bg-zinc-800 overflow-hidden"
      role="progressbar"
      aria-valuenow={safeValue}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <motion.div
        className="h-full bg-gradient-to-r from-teal-400 to-blue-500"
        initial={{ width: 0 }}
        animate={{ width: `${safeValue}%` }}
        transition={{ type: "spring", stiffness: 120, damping: 20 }}
      />
      {showLabel && (
        <span className="absolute inset-0 text-xs text-white text-center leading-3 font-medium">
          {safeValue}%
        </span>
      )}
    </div>
  );
}

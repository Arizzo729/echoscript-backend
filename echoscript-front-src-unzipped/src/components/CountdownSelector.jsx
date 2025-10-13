import React from "react";
import { motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { twMerge } from "tailwind-merge";

export default function CountdownSelector({ value, onChange, options = [0, 1, 2, 3, 5, 7, 10] }) {
  const selectId = "countdown-selector";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="w-full max-w-xs"
    >
      <label
        htmlFor={selectId}
        className="block mb-2 text-sm font-medium text-zinc-300"
      >
        ⏱ Countdown Before Recording
      </label>

      <div className="relative">
        <select
          id={selectId}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className={twMerge(
            "w-full appearance-none bg-zinc-900 border border-zinc-700",
            "text-white text-sm rounded-lg px-4 py-2.5 pr-10",
            "hover:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500",
            "transition-all duration-300"
          )}
        >
          {options.map((option) => (
            <option key={option} value={option}>
              {option === 0 ? "No Countdown" : `${option} second${option !== 1 ? "s" : ""}`}
            </option>
          ))}
        </select>

        <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400">
          <ChevronDown className="w-4 h-4" />
        </div>
      </div>

      <p className="mt-1 text-xs text-zinc-500">
        Choose how long you want to prepare before recording starts.
      </p>
    </motion.div>
  );
}


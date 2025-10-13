// 2. LiveGPTBubble.jsx (Advanced)
import React from "react";
import { motion } from "framer-motion";
import { BsStars } from "react-icons/bs";

export default function LiveGPTBubble({ message, onClose }) {
  return (
    <motion.div
      className="absolute top-24 right-6 max-w-sm bg-white text-black p-4 rounded-xl shadow-2xl z-50 border border-zinc-300"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-start gap-2">
        <BsStars className="text-teal-500 mt-1" />
        <div className="text-sm font-medium leading-snug">
          <span className="block">{message}</span>
          <button onClick={onClose} className="text-xs mt-2 text-teal-600 hover:underline">
            Dismiss
          </button>
        </div>
      </div>
    </motion.div>
  );
}

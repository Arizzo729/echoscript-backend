import React from "react";
import { motion } from "framer-motion";
import { Mic, Bot, Loader2 } from "lucide-react";

const moodMap = {
  idle: {
    icon: <Bot className="w-6 h-6 text-zinc-500 dark:text-zinc-400" />,
    label: "Echo is listening...",
  },
  thinking: {
    icon: <Loader2 className="w-6 h-6 animate-spin text-teal-500" />,
    label: "Echo is thinking...",
  },
  speaking: {
    icon: <Mic className="w-6 h-6 animate-pulse text-teal-500" />,
    label: "Echo is responding...",
  },
};

export default function AssistantAvatar({ mood = "idle" }) {
  const current = moodMap[mood] || moodMap.idle;

  return (
    <motion.div
      className="flex items-center gap-3 px-4 py-2 border-b border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900 rounded-t-xl"
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="flex items-center justify-center w-9 h-9 rounded-full bg-zinc-200 dark:bg-zinc-800 shadow-sm">
        {current.icon}
      </div>
      <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
        {current.label}
      </span>
    </motion.div>
  );
}

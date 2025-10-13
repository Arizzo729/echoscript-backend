import React from "react";
import { Mic, MicOff } from "lucide-react";
import { motion } from "framer-motion";
import useVoiceInput from "../hooks/useVoiceInput";

/**
 * VoiceInputButton — toggles microphone for live voice input
 * - Safe fallback if `onTranscript` not provided
 * - Animated feedback + keyboard accessible
 * - Color-coded for recording state
 * - Fully accessible and dark-mode friendly
 */
export default function VoiceInputButton({ onTranscript = () => {} }) {
  const { listening, startListening, stopListening } = useVoiceInput({ onTranscript });

  const handleClick = () => {
    listening ? stopListening() : startListening();
  };

  return (
    <motion.button
      onClick={handleClick}
      whileTap={{ scale: 0.95 }}
      className={`p-3 rounded-full shadow-md border transition-all duration-300 ease-out focus:outline-none focus:ring-2 
        ${listening 
          ? "bg-red-500 text-white border-red-600 hover:bg-red-600 focus:ring-red-400"
          : "bg-zinc-200 dark:bg-zinc-800 text-zinc-900 dark:text-white border-zinc-300 dark:border-zinc-600 hover:bg-zinc-300 dark:hover:bg-zinc-700 focus:ring-blue-400"
        }`}
      aria-label={listening ? "Stop microphone input" : "Start microphone input"}
      title={listening ? "Stop microphone input" : "Start microphone input"}
    >
      {listening ? <MicOff size={20} /> : <Mic size={20} />}
    </motion.button>
  );
}

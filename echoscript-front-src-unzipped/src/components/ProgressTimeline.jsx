// src/components/ProgressTimeline.jsx
import React from "react";
import { motion } from "framer-motion";

export default function ProgressTimeline({
  currentStep = 0,
  steps = ["Mic", "Voice", "AI", "Start"],
}) {
  return (
    <div className="relative flex justify-center items-center gap-6 mt-8 z-10">
      {steps.map((label, index) => {
        const isActive = index <= currentStep;
        const isCurrent = index === currentStep;

        return (
          <div key={index} className="flex flex-col items-center relative">
            {/* Connector Line */}
            {index !== 0 && (
              <motion.div
                className="absolute -left-[calc(50%+0.625rem)] top-2 h-1 w-[36px] rounded-full"
                initial={{ backgroundColor: "#3f3f46" }}
                animate={{ backgroundColor: isActive ? "#14b8a6" : "#3f3f46" }}
                transition={{ duration: 0.4 }}
              />
            )}

            {/* Step Circle */}
            <motion.div
              className={`w-5 h-5 rounded-full border-2 ${
                isActive ? "bg-teal-400 border-teal-500" : "bg-zinc-700 border-zinc-600"
              }`}
              initial={{ scale: 0.8 }}
              animate={{ scale: isCurrent ? 1.3 : 1 }}
              transition={{ type: "spring", stiffness: 120, damping: 15 }}
              aria-current={isCurrent ? "step" : undefined}
              role="presentation"
            ></motion.div>

            {/* Step Label */}
            <span
              className={`text-xs mt-1 ${
                isActive ? "text-teal-400" : "text-zinc-500"
              }`}
            >
              {label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

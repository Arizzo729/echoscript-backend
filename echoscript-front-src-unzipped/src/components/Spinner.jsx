import React from "react";
import { twMerge } from "tailwind-merge";

export default function Spinner({
  size = 6,
  className = "",
  label = "Loading…",
  speed = "slow", // accepts "slow", "normal", or "fast"
}) {
  const sizeClass =
    typeof size === "number"
      ? `h-${size} w-${size}`
      : `h-[${size}] w-[${size}]`;

  const speedClass = {
    slow: "animate-spin-slow",
    normal: "animate-spin",
    fast: "animate-spin-fast",
  }[speed] || "animate-spin-slow";

  return (
    <div
      className={twMerge(
        "inline-flex items-center justify-center",
        sizeClass,
        className
      )}
      role="status"
      aria-label={label}
    >
      <svg
        className={twMerge(speedClass, "text-teal-500")}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="spinner-gradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#14b8a6" />
            <stop offset="50%" stopColor="#0ea5e9" />
            <stop offset="100%" stopColor="#10b981" />
          </linearGradient>
        </defs>
        <circle
          cx="50"
          cy="50"
          r="40"
          stroke="url(#spinner-gradient)"
          strokeWidth="10"
          fill="none"
          strokeDasharray="250"
          strokeDashoffset="210"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}

}


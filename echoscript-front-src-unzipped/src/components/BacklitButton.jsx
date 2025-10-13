// src/components/BacklitButton.jsx
import React from "react";
import clsx from "clsx";

export default function BacklitButton({
  children,
  className = "",
  type = "button",           // avoid accidental form submit
  disabled = false,
  loading = false,
  ...props
}) {
  const isDisabled = disabled || loading;

  return (
    <button
      type={type}
      disabled={isDisabled}
      aria-busy={loading || undefined}
      {...props}
      className={clsx(
        "relative px-6 py-3 rounded-full font-semibold text-white text-lg tracking-tight",
        "bg-gradient-to-r from-purple-500 to-fuchsia-500 shadow-lg",
        "hover:from-fuchsia-500 hover:to-purple-500 transition-all duration-300 ease-out",
        "before:absolute before:inset-0 before:rounded-full before:blur-xl before:opacity-30 before:bg-fuchsia-500",
        isDisabled && "opacity-60 cursor-not-allowed",
        className
      )}
    >
      <span className="relative z-10 flex items-center gap-2">
        {loading && (
          <span className="inline-block h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
        )}
        {children}
      </span>
    </button>
  );
}

// src/components/IconButton.jsx
import React from "react";

/**
 * Minimal, accessible icon button that forwards all events/props.
 */
export default function IconButton({
  icon,
  label,
  tooltip,
  className = "",
  type = "button",
  onClick,
  disabled = false,
  ...rest
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      aria-label={label || tooltip}
      title={tooltip || label}
      className={[
        "inline-flex items-center justify-center",
        "h-9 w-9 rounded-lg",
        "bg-transparent hover:bg-zinc-200 dark:hover:bg-zinc-700",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400",
        disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer",
        className,
      ].join(" ")}
      {...rest}
    >
      {icon}
    </button>
  );
}


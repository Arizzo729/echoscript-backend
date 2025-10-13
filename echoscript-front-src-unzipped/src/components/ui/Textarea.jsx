import React, { useId } from "react";
import { twMerge } from "tailwind-merge";

function Textarea({
  label,
  placeholder = "Enter text...",
  rows = 4,
  className = "",
  description,
  error,
  required = false,
  ...props
}) {
  const generatedId = useId();
  const id = props.id || `textarea-${generatedId}`;

  return (
    <div className="w-full space-y-1.5">
      {label && (
        <label
          htmlFor={id}
          className="block text-sm font-semibold text-zinc-800 dark:text-zinc-200"
        >
          {label} {required && <span className="text-red-500">*</span>}
        </label>
      )}

      <textarea
        id={id}
        rows={rows}
        placeholder={placeholder}
        aria-invalid={!!error}
        aria-describedby={description ? `${id}-desc` : undefined}
        className={twMerge(
          "w-full rounded-lg border px-3 py-2 text-sm shadow-sm transition",
          "focus:outline-none focus:ring-2 focus:ring-teal-500",
          "bg-white dark:bg-zinc-800",
          "border-zinc-300 dark:border-zinc-700",
          "text-zinc-900 dark:text-white",
          "placeholder-zinc-400 dark:placeholder-zinc-500",
          className
        )}
        required={required}
        {...props}
      />

      {description && (
        <p id={`${id}-desc`} className="text-xs text-zinc-500">
          {description}
        </p>
      )}

      {error && (
        <p className="text-xs text-red-500 font-medium">
          {error}
        </p>
      )}
    </div>
  );
}

export default Textarea;


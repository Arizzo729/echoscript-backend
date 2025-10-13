import React, { useId } from "react";
import { ChevronDown } from "lucide-react";
import { twMerge } from "tailwind-merge";

export function SelectDropdown({
  label,
  options = [],
  placeholder = "Select an option",
  value,
  onChange,
  disabled = false,
  required = false,
  description,
  error,
  className = "",
  id,
  ...props
}) {
  const generatedId = useId();
  const selectId = id || `select-${generatedId}`;

  return (
    <div className="w-full space-y-1.5">
      {label && (
        <label
          htmlFor={selectId}
          className="block text-sm font-semibold text-zinc-800 dark:text-zinc-200"
        >
          {label} {required && <span className="text-red-500">*</span>}
        </label>
      )}
      <div className="relative">
        <select
          id={selectId}
          value={value}
          onChange={onChange}
          disabled={disabled}
          required={required}
          aria-invalid={!!error}
          aria-describedby={
            description ? `${selectId}-desc` : error ? `${selectId}-error` : undefined
          }
          className={twMerge(
            "w-full appearance-none rounded-lg border px-3 py-2 text-sm pr-10 shadow-sm transition-all",
            "bg-white dark:bg-zinc-800",
            "border-zinc-300 dark:border-zinc-700",
            "text-zinc-900 dark:text-white",
            "placeholder-zinc-400 dark:placeholder-zinc-500",
            "focus:outline-none focus:ring-2 focus:ring-teal-500",
            className
          )}
          {...props}
        >
          {placeholder && (
            <option value="" disabled hidden>
              {placeholder}
            </option>
          )}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500 dark:text-zinc-400" />
      </div>

      {description && (
        <p id={`${selectId}-desc`} className="text-xs text-zinc-500">
          {description}
        </p>
      )}
      {error && (
        <p id={`${selectId}-error`} className="text-xs text-red-500 font-medium">
          {error}
        </p>
      )}
    </div>
  );
}


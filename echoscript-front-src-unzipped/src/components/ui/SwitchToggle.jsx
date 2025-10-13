// ✅ EchoScript.AI — Final Advanced SwitchToggle with Sound Feedback
import React from "react";
import { Switch } from "@headlessui/react";
import { twMerge } from "tailwind-merge";
import { useSound } from "../../context/SoundContext";

export default function SwitchToggle({ enabled, onChange, label = "", description = "", disableSound = false }) {
  const { playClick, isMuted } = useSound();

  const handleChange = (val) => {
    if (!disableSound && !isMuted) playClick();
    onChange(val);
  };

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 py-3 w-full">
      <div className="flex flex-col">
        {label && (
          <span className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">
            {label}
          </span>
        )}
        {description && (
          <span className="text-xs text-zinc-500 dark:text-zinc-400">
            {description}
          </span>
        )}
      </div>

      <Switch
        checked={enabled}
        onChange={handleChange}
        className={twMerge(
          "relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-teal-400",
          enabled ? "bg-teal-600 dark:bg-teal-400" : "bg-zinc-300 dark:bg-zinc-600"
        )}
      >
        <span
          className={twMerge(
            "inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform duration-300",
            enabled ? "translate-x-6" : "translate-x-1"
          )}
        />
      </Switch>
    </div>
  );
}

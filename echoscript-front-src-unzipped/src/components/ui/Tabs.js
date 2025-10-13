// ✅ EchoScript.AI — Final Polished Smart Tabs (Horizontal + Vertical + Icon Support)
import React from "react";
import { twMerge } from "tailwind-merge";

export default function Tabs({
  tabs = [],
  activeTab,
  onTabChange,
  direction = "horizontal", // "horizontal" or "vertical"
  className = "",
}) {
  return (
    <div
      className={twMerge(
        "flex",
        direction === "vertical" ? "flex-col gap-2" : "flex-row gap-3 sm:gap-4",
        className
      )}
    >
      {tabs.map(({ id, label, icon: Icon }) => {
        const isActive = id === activeTab;
        return (
          <button
            key={id}
            onClick={() => onTabChange(id)}
            className={twMerge(
              "group flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all duration-300",
              isActive
                ? "bg-teal-100 text-teal-700 dark:bg-teal-700/30 dark:text-teal-300 shadow-inner shadow-teal-200/40 dark:shadow-none"
                : "text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-700/40"
            )}
          >
            {Icon && <Icon className="w-4 h-4 opacity-80 group-hover:opacity-100" />}
            <span className="truncate">{label}</span>
          </button>
        );
      })}
    </div>
  );
}


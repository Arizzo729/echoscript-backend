// components/PaywallModal.jsx
import React from "react";
import { X } from "lucide-react";

export default function PaywallModal({ usageInfo, info, onClose }) {
  const src = usageInfo || info;
  if (!src) return null;

  // normalize
  const used = src.used ?? src.usedMinutes ?? 0;
  const limit = src.limit ?? src.limitMinutes ?? 0;
  const upgradeUrl =
    src.upgrade_url || src.upgradeUrl || "/purchase";

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
    >
      <div className="relative w-full max-w-md rounded-lg bg-white dark:bg-gray-900 p-6 shadow-xl">
        <button
          aria-label="Close paywall modal"
          onClick={onClose}
          className="absolute right-4 top-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
        >
          <X size={24} />
        </button>
        <h2 className="mb-4 text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Usage Limit Reached
        </h2>
        <p className="mb-2 text-gray-700 dark:text-gray-300">
          You have used <strong>{used} minutes</strong> of your{" "}
          <strong>{limit} minutes</strong> free transcription quota.
        </p>
        <p className="mb-6 text-gray-600 dark:text-gray-400">
          To continue transcribing, please upgrade your plan.
        </p>
        <a
          href={upgradeUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block w-full rounded-md bg-teal-600 px-5 py-3 text-center font-medium text-white hover:bg-teal-700 transition"
        >
          Upgrade Now
        </a>
      </div>
    </div>
  );
}


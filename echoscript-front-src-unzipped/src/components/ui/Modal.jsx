import React, { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";

export default function Modal({ isOpen, onClose, children, title, showClose = true }) {
  const contentRef = useRef(null);

  // ESC key handler
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "Escape") onClose?.();
    };
    if (isOpen) window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [isOpen, onClose]);

  // Prevent outside click from closing when clicking inside modal
  const handleBackdropClick = (e) => {
    if (contentRef.current && !contentRef.current.contains(e.target)) {
      onClose?.();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 z-[9998] bg-black/40 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleBackdropClick}
          />

          {/* Modal content */}
          <motion.div
            ref={contentRef}
            className="fixed z-[9999] left-1/2 top-1/2 w-full max-w-lg -translate-x-1/2 -translate-y-1/2
              bg-white dark:bg-zinc-900 rounded-xl shadow-2xl p-6 overflow-hidden"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 300, damping: 22 }}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              {title && (
                <h3 className="text-lg font-bold text-zinc-900 dark:text-white">
                  {title}
                </h3>
              )}
              {showClose && (
                <button
                  onClick={onClose}
                  className="ml-4 text-zinc-400 hover:text-red-500 transition"
                  aria-label="Close"
                >
                  <X size={20} />
                </button>
              )}
            </div>

            {/* Body */}
            <div className="text-sm text-zinc-600 dark:text-zinc-300">{children}</div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}


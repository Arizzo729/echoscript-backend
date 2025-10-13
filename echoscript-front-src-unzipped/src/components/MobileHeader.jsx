// src/components/MobileHeader.jsx
import React, { useState, useRef, useEffect } from "react";
import { MagnifyingGlassIcon, BellIcon, EllipsisVerticalIcon } from "@heroicons/react/24/outline";
import { Volume2, VolumeX } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useSound } from "../context/SoundContext"; // <-- fixed
import { motion, AnimatePresence } from "framer-motion";
import Button from "./ui/Button";

export default function MobileHeader({ onSearch, hasNewNotifications = false }) {
  const { t } = useTranslation();
  const { isMuted, toggleMute } = useSound();

  const [showMenu, setShowMenu] = useState(false);
  const [showNotifDropdown, setShowNotifDropdown] = useState(false);
  const menuRef = useRef(null);
  const notifRef = useRef(null);
  const inputRef = useRef(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const close = (e) => {
      if (!menuRef.current?.contains(e.target) && !notifRef.current?.contains(e.target)) {
        setShowMenu(false);
        setShowNotifDropdown(false);
      }
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", (e) => e.key === "Escape" && close(e));
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", (e) => e.key === "Escape" && close(e));
    };
  }, []);

  return (
    <motion.header
      className="fixed top-0 left-0 right-0 z-50 bg-white/95 dark:bg-zinc-900/95 border-b border-zinc-200 dark:border-zinc-800 shadow backdrop-blur-md"
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 220, damping: 18 }}
      style={{ height: 64 }}
      role="banner"
    >
      <div className="flex items-center justify-between gap-2 px-3 py-2" style={{ minHeight: 56 }}>
        <div className="flex-1 relative">
          <input
            ref={inputRef}
            type="search"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              if (onSearch) onSearch(e.target.value);
            }}
            placeholder={t("Search tools, pages, actions.")}
            className="w-full h-11 pl-10 pr-4 rounded-full bg-zinc-100 dark:bg-zinc-800 text-[1rem] text-zinc-900 dark:text-white placeholder-zinc-400 shadow-inner border-0 focus:outline-none focus:ring-2 focus:ring-teal-400 transition"
            aria-label={t("Search")}
            autoCorrect="off"
            spellCheck="false"
            autoComplete="off"
          />
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400 pointer-events-none" aria-hidden="true" />
        </div>

        <motion.div whileTap={{ scale: 0.9 }}>
          <Button
            variant="ghost"
            size="icon"
            className="ml-1"
            aria-label={isMuted ? t("Unmute") : t("Mute")}
            onClick={toggleMute}
            icon={isMuted ? <VolumeX className="w-5 h-5 text-red-500" /> : <Volume2 className="w-5 h-5 text-teal-400" />}
            tabIndex={0}
          />
        </motion.div>

        <motion.div whileTap={{ scale: 0.9 }} className="relative" ref={notifRef}>
          <Button
            variant="ghost"
            size="icon"
            aria-label={t("Notifications")}
            onClick={() => setShowNotifDropdown((v) => !v)}
            icon={
              <span className="relative">
                <BellIcon className="w-5 h-5 text-zinc-900 dark:text-white" />
                {hasNewNotifications && <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-teal-400 rounded-full border-2 border-white dark:border-zinc-900" />}
              </span>
            }
            tabIndex={0}
          />
          <AnimatePresence>
            {showNotifDropdown && (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute right-0 top-full mt-2 w-64 rounded-xl shadow-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 z-50 py-3"
                role="menu"
              >
                <div className="text-sm text-zinc-800 dark:text-zinc-200 p-4">{t("No notifications yet")}</div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        <motion.div whileTap={{ scale: 0.9 }} className="relative" ref={menuRef}>
          <Button
            variant="ghost"
            size="icon"
            aria-label={t("More")}
            onClick={() => setShowMenu((v) => !v)}
            icon={<EllipsisVerticalIcon className="w-6 h-6 text-zinc-900 dark:text-white" />}
            tabIndex={0}
          />
          <AnimatePresence>
            {showMenu && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute right-0 top-full mt-2 w-56 rounded-xl shadow-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 z-50 py-2"
                role="menu"
              >
                <MenuItem label={t("Settings")} onClick={() => { setShowMenu(false); window.location.href = "/settings"; }} />
                <MenuItem label={t("Help & Support")} onClick={() => { setShowMenu(false); window.location.href = "/help"; }} />
                <MenuItem label={t("Feedback")} onClick={() => { setShowMenu(false); window.location.href = "/feedback"; }} />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </motion.header>
  );
}

function MenuItem({ label, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full text-left px-4 py-2 text-[1rem] text-zinc-800 dark:text-zinc-100 hover:bg-teal-50 dark:hover:bg-zinc-800 focus:bg-teal-50 dark:focus:bg-zinc-800 transition rounded-md"
      tabIndex={0}
      role="menuitem"
    >
      {label}
    </button>
  );
}


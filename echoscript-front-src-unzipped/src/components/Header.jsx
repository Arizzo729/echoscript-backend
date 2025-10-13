// src/components/Header.jsx
import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Command, Search, Loader2, Cog, VolumeX, Volume2, User, Home } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import IconButton from "./IconButton";
import { useSound } from "../context/SoundContext";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");

// Local quick actions / destinations used for type-ahead
const LOCAL_INDEX = [
  { label: "Home", path: "/", type: "page", keywords: ["home", "start", "landing"] },
  { label: "Dashboard", path: "/dashboard", type: "page", keywords: ["dashboard", "overview"] },
  { label: "Upload", path: "/upload", type: "page", keywords: ["upload", "transcribe", "audio", "video"] },
  { label: "Live Captions", path: "/live", type: "page", keywords: ["live", "captions", "realtime"] },
  { label: "Transcripts", path: "/transcripts", type: "page", keywords: ["transcripts", "history", "search"] },
  { label: "Purchase", path: "/purchase", type: "page", keywords: ["upgrade", "pro", "pricing", "purchase", "buy"] },
  { label: "Account", path: "/account", type: "page", keywords: ["account", "profile", "settings"] },
  { label: "Settings", path: "/settings", type: "page", keywords: ["settings", "preferences"] },
  { label: "Contact", path: "/contact", type: "page", keywords: ["contact", "support", "help"] },
  { label: "Community", path: "/community", type: "page", keywords: ["community", "forum"] },
  { label: "FAQ", path: "/faq", type: "page", keywords: ["faq", "questions"] },
  { label: "Terms of Service", path: "/terms", type: "page", keywords: ["terms", "tos"] },
  { label: "Privacy Policy", path: "/privacy", type: "page", keywords: ["privacy"] },
  // Actions
  { label: "New Upload", action: "new-upload", type: "action", keywords: ["new", "upload", "start"] },
  { label: "Start Recording", action: "start-recording", type: "action", keywords: ["record", "mic", "start"] },
];

function score(item, q) {
  const s = (str) => str.toLowerCase();
  const query = s(q);
  const label = s(item.label);
  if (label.startsWith(query)) return 100 - (label.length - query.length);
  if (label.includes(query)) return 60 - (label.indexOf(query) || 0);
  if (item.keywords?.some((k) => s(k).startsWith(query))) return 40;
  if (item.keywords?.some((k) => s(k).includes(query))) return 20;
  return 0;
}

export default function Header() {
  const navigate = useNavigate();
  const { isMuted, toggleMute } = useSound();
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(0);
  const [loadingRemote, setLoadingRemote] = useState(false);
  const [remote, setRemote] = useState([]);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  // simple auth check (swap to your real auth hook when ready)
  const isAuthed = !!localStorage.getItem("auth_token");

  // remote suggestions (optional)
  useEffect(() => {
    const t = setTimeout(async () => {
      const query = q.trim();
      if (!query) {
        setRemote([]);
        setLoadingRemote(false);
        return;
      }
      setLoadingRemote(true);
      try {
        const res = await fetch(`${API_BASE}/api/search/suggest?q=${encodeURIComponent(query)}`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          const normalized = (Array.isArray(data) ? data : [])
            .slice(0, 6)
            .map((d) => ({
              label: d.label || d.title || d.name || String(d),
              path: d.path || d.url || d.href || null,
              type: "remote",
            }));
          setRemote(normalized);
        } else {
          setRemote([]);
        }
      } catch {
        setRemote([]);
      } finally {
        setLoadingRemote(false);
      }
    }, 180);
    return () => clearTimeout(t);
  }, [q]);

  const localMatches = useMemo(() => {
    const query = q.trim();
    if (!query) return [];
    return LOCAL_INDEX
      .map((item) => ({ item, s: score(item, query) }))
      .filter((x) => x.s > 0)
      .sort((a, b) => b.s - a.s)
      .slice(0, 6)
      .map((x) => x.item);
  }, [q]);

  const suggestions = useMemo(() => {
    const seen = new Set();
    const merged = [];
    for (const it of localMatches) {
      const key = it.path || it.action || it.label;
      if (!seen.has(key)) { seen.add(key); merged.push(it); }
    }
    for (const it of remote) {
      const key = it.path || it.label;
      if (!seen.has(key)) { seen.add(key); merged.push(it); }
    }
    return merged;
  }, [localMatches, remote]);

  const openMenu = () => setOpen(true);
  const closeMenu = () => { setOpen(false); setActiveIdx(0); };

  const submitSearch = useCallback(
    (override) => {
      const pick = override ?? suggestions[activeIdx];
      if (pick?.type === "action") {
        if (pick.action === "new-upload") { navigate("/upload"); return closeMenu(); }
        if (pick.action === "start-recording") {
          window.dispatchEvent(new CustomEvent("echo:record:start"));
          return closeMenu();
        }
      }
      if (pick?.path) { navigate(pick.path); return closeMenu(); }
      const query = q.trim();
      if (query) navigate(`/search?q=${encodeURIComponent(query)}`);
      closeMenu();
    },
    [activeIdx, suggestions, q, navigate]
  );

  const onKeyDown = (e) => {
    if (!open) return;
    if (e.key === "ArrowDown") { e.preventDefault(); setActiveIdx((i) => Math.min(i + 1, Math.max(0, suggestions.length - 1))); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActiveIdx((i) => Math.max(i - 1, 0)); }
    else if (e.key === "Enter") { e.preventDefault(); submitSearch(); }
    else if (e.key === "Escape") { e.preventDefault(); closeMenu(); }
  };

  useEffect(() => {
    const handler = (e) => {
      if (!open) return;
      if (!listRef.current?.contains(e.target) && e.target !== inputRef.current) closeMenu();
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  return (
    <>
      <header className="w-full bg-white/80 dark:bg-zinc-900/80 backdrop-blur border-b border-zinc-200 dark:border-zinc-800">
        <div className="max-w-screen-2xl mx-auto px-4 py-3 flex items-center gap-3">
          {/* Home icon button (always visible) */}
          <IconButton label="Home" tooltip="Home" icon={<Home className="w-5 h-5" />} onClick={() => navigate("/")} />

          {/* Brand (also clickable) */}
          <Link to="/" className="flex items-center gap-2">
            <Command className="w-5 h-5 text-teal-500" />
            <span className="font-semibold text-zinc-900 dark:text-white">EchoScript.AI</span>
          </Link>

          {/* Search */}
          <div className="relative flex-1 max-w-xl ml-auto">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 pointer-events-none" />
              <input
                ref={inputRef}
                type="search"
                value={q}
                onChange={(e) => { setQ(e.target.value); if (!open) setOpen(true); }}
                onFocus={openMenu}
                onKeyDown={onKeyDown}
                placeholder="Search tools, pages, actions…"
                className="w-full pl-9 pr-28 py-2 rounded-lg bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-white placeholder-zinc-400 border border-zinc-300 dark:border-zinc-700 focus:outline-none focus:ring-2 focus:ring-teal-500"
                role="combobox"
                aria-expanded={open}
                aria-controls="header-search-listbox"
                aria-autocomplete="list"
              />
              {loadingRemote && (
                <Loader2 className="absolute right-24 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-zinc-400" />
              )}
            </div>

            <AnimatePresence>
              {open && (q.trim().length > 0 || suggestions.length > 0) && (
                <motion.ul
                  id="header-search-listbox"
                  ref={listRef}
                  role="listbox"
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 6 }}
                  className="absolute z-50 mt-2 w-full max-h-72 overflow-auto rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 shadow-xl"
                >
                  {suggestions.length === 0 && (
                    <li className="px-3 py-2 text-sm text-zinc-500">No suggestions. Press Enter to search.</li>
                  )}
                  {suggestions.map((sug, i) => {
                    const isActive = i === activeIdx;
                    return (
                      <li
                        key={(sug.path || sug.action || sug.label) + i}
                        role="option"
                        aria-selected={isActive}
                        onMouseEnter={() => setActiveIdx(i)}
                        onMouseDown={(e) => { e.preventDefault(); submitSearch(sug); }}
                        className={`px-3 py-2 cursor-pointer text-sm flex items-center justify-between ${
                          isActive
                            ? "bg-teal-600 text-white"
                            : "text-zinc-800 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                        }`}
                      >
                        <span className="truncate">
                          {sug.label}
                          {sug.type === "action" && <span className="opacity-80"> · action</span>}
                          {sug.type === "remote" && <span className="opacity-80"> · from server</span>}
                        </span>
                        {sug.path && (
                          <span className={`text-xs ${isActive ? "opacity-90" : "text-zinc-400"}`}>{sug.path}</span>
                        )}
                      </li>
                    );
                  })}
                </motion.ul>
              )}
            </AnimatePresence>
          </div>

          {/* Controls: Mute / Settings / Auth */}
          <div className="flex items-center gap-2">
            <IconButton label={isMuted ? "Unmute" : "Mute"} tooltip={isMuted ? "Unmute" : "Mute"} icon={isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />} onClick={toggleMute} />
            <IconButton label="Settings" tooltip="Settings" icon={<Cog className="w-5 h-5" />} onClick={() => navigate("/settings")} />
            <button onClick={() => navigate("/account")} className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-teal-600 text-white font-semibold hover:bg-teal-500 transition">
              <User className="w-4 h-4" />
              Account
            </button>
          </div>
        </div>
      </header>
      {/* Removed: <AudioOverlay /> — mount once at top-level for desktop only */}
    </>
  );
}


// src/components/MobileBottomNav.jsx
import React from "react";
import { NavLink } from "react-router-dom";
import { Home, LayoutDashboard, UploadCloud, ShoppingBag, User } from "lucide-react";
import { motion } from "framer-motion";
import { useSound } from "../context/SoundContext"; // <-- fixed
import "../styles/mobile.css"; // <-- fixed

const links = [
  { to: "/", Icon: Home, label: "Home" },
  { to: "/dashboard", Icon: LayoutDashboard, label: "Dashboard" },
  { to: "/upload", Icon: UploadCloud, label: "Upload" },
  { to: "/purchase", Icon: ShoppingBag, label: "Shop" },
  { to: "/account", Icon: User, label: "Account" },
];

export default function MobileBottomNav() {
  const { playPop } = useSound();

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 h-16 flex justify-around items-center
        bg-zinc-900/80 backdrop-blur-[6px] border-t border-teal-600/40
        safe-area-inset md:hidden select-none"
      role="navigation"
      aria-label="Mobile bottom navigation"
      style={{
        borderTopLeftRadius: "calc(env(safe-area-inset-left,0px) + 10px)",
        borderTopRightRadius: "calc(env(safe-area-inset-right,0px) + 10px)",
        WebkitBackdropFilter: "blur(6px)",
        backdropFilter: "blur(6px)",
        boxShadow: "0 -2px 22px 0 rgba(14, 175, 160, 0.07)",
      }}
    >
      {links.map(({ to, Icon, label }) => (
        <NavLink key={to} to={to} className="flex-1 flex justify-center items-center h-full outline-none" aria-label={label} tabIndex={0}>
          {({ isActive }) => (
            <motion.div
              onTap={playPop}
              whileTap={{ scale: 0.87 }}
              className={`w-full h-full flex flex-col items-center justify-center transition relative ${
                isActive ? "bg-teal-700/10" : "hover:bg-zinc-800/40"
              } focus-within:bg-teal-600/15`}
              style={{ borderRadius: 16, transition: "background 0.18s cubic-bezier(.4,0,.2,1)", minWidth: 48 }}
            >
              <Icon className={`w-7 h-7 mx-auto transition-colors duration-200 ${isActive ? "text-teal-400" : "text-zinc-400"}`} aria-hidden="true" />
              <span
                className={`text-xs mt-1 font-medium tracking-tight ${isActive ? "text-teal-300" : "text-zinc-400"}`}
                style={{ letterSpacing: 0.02, fontSize: 12.3, userSelect: "none", pointerEvents: "none" }}
              >
                {label}
              </span>
              {isActive && <span className="absolute left-1/2 -translate-x-1/2 bottom-1 w-8 h-1 rounded-full bg-teal-400" aria-hidden="true" />}
            </motion.div>
          )}
        </NavLink>
      ))}
    </nav>
  );
}


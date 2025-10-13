// Sidebar.jsx — EchoScript.AI Sidebar Navigation (Polished + Future-Proof)

import React from "react";
import { NavLink } from "react-router-dom";
import {
  Home,
  Upload,
  ShoppingCart,
  LogOut,
  Menu,
  X,
  Video,
  MessageCircle,
  LayoutDashboard,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const navItems = [
  { path: "/", label: "Home", icon: Home },
  { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { path: "/upload", label: "Upload", icon: Upload },
  { path: "/video", label: "Video Tools", icon: Video },
  { path: "/purchase", label: "Shop", icon: ShoppingCart },
  { path: "/contact", label: "Contact Us", icon: MessageCircle },
];

export default function Sidebar({ collapsed, setCollapsed }) {
  return (
    <motion.aside
      initial={{ x: -250 }}
      animate={{ x: 0 }}
      transition={{ type: "spring", stiffness: 80, damping: 20 }}
      className={`fixed top-0 left-0 h-screen z-40 bg-gradient-to-b from-zinc-950 via-zinc-900 to-zinc-950 border-r border-zinc-800 shadow-2xl backdrop-blur-lg transition-all duration-300 hidden md:block ${
        collapsed ? "w-16" : "w-56"
      }`}
      aria-label="Sidebar Navigation"
    >
      {/* Toggle Button */}
      <div className="flex items-center justify-end px-3 pt-4">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 rounded-full bg-zinc-800 hover:bg-teal-600 text-white shadow transition-all"
          title={collapsed ? "Open Menu" : "Close Menu"}
          aria-label={collapsed ? "Open sidebar" : "Close sidebar"}
        >
          {collapsed ? <Menu size={18} /> : <X size={18} />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="mt-6 flex flex-col gap-1 px-2">
        {navItems.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `group relative flex items-center gap-3 px-3 py-2 rounded-xl transition-all text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 ${
                isActive
                  ? "bg-gradient-to-r from-teal-500 to-blue-500 text-white shadow-md"
                  : "text-zinc-400 hover:text-white hover:bg-zinc-800"
              }`
            }
            aria-current={({ isActive }) => (isActive ? "page" : undefined)}
            title={collapsed ? label : undefined}
          >
            <Icon className="w-5 h-5 shrink-0" />
            <AnimatePresence initial={false}>
              {!collapsed && (
                <motion.span
                  initial={{ opacity: 0, x: -5 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -5 }}
                  className="truncate"
                >
                  {label}
                </motion.span>
              )}
            </AnimatePresence>
          </NavLink>
        ))}
      </nav>

      {/* Logout Button */}
      <div className="absolute bottom-6 w-full px-3">
        <button
          className="flex items-center gap-3 px-3 py-2 w-full text-left rounded-xl bg-red-500 text-white hover:bg-red-600 transition-all duration-300 shadow-md"
          aria-label="Log out"
        >
          <LogOut className="w-5 h-5" />
          {!collapsed && <span className="text-sm">Log Out</span>}
        </button>
      </div>
    </motion.aside>
  );
}


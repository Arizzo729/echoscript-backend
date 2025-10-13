import React from "react";
import { Link } from "react-router-dom";

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="w-full px-6 py-6 mt-auto text-sm text-center text-zinc-500 dark:text-zinc-400 border-t border-zinc-200 dark:border-zinc-700 bg-white/80 dark:bg-zinc-900/80 backdrop-blur">
      <div className="max-w-screen-xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* © EchoScript.AI */}
        <div className="text-xs">
          &copy; {year}{" "}
          <span className="text-teal-500 font-semibold">EchoScript.AI</span>. All rights reserved.
        </div>

        {/* Footer Nav Links */}
        <div className="flex flex-wrap items-center gap-4 justify-center text-xs">
          <Link to="/privacy" className="hover:text-teal-500 transition">Privacy Policy</Link>
          <Link to="/terms" className="hover:text-teal-500 transition">Terms of Service</Link>
          <Link to="/contact" className="hover:text-teal-500 transition">Contact</Link>
          <Link to="/faq" className="hover:text-teal-500 transition">FAQ</Link>
        </div>
      </div>
    </footer>
  );
}


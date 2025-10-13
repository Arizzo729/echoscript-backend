import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";

export default function NotFound() {
  const { t } = useTranslation();

  return (
    <motion.div
      className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-zinc-950 to-zinc-900 px-2 sm:px-0"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
    >
      <div className="w-full max-w-md">
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl px-7 py-10 text-center">
          <motion.h1
            className="text-7xl sm:text-8xl font-extrabold bg-gradient-to-r from-teal-400 to-blue-500 text-transparent bg-clip-text mb-2"
            initial={{ scale: 0.92 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.18 }}
          >
            404
          </motion.h1>

          <p className="text-lg sm:text-xl text-zinc-400 mb-6">
            {t("not_found.description")}
          </p>

          <Link
            to="/"
            className="inline-flex items-center justify-center px-7 py-3 rounded-xl bg-teal-600 hover:bg-teal-500 text-lg font-semibold text-white shadow-lg transition duration-300 focus-visible:ring-2 focus-visible:ring-teal-400"
          >
            ⬅ {t("not_found.back_home")}
          </Link>
        </div>
      </div>
    </motion.div>
  );
}

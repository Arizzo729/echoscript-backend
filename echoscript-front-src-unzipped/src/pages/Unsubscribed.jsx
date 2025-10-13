// ✅ src/pages/Unsubscribed.jsx — Confirmation Page
import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { CheckCircle } from "lucide-react";

export default function Unsubscribed() {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center px-4">
      <motion.div
        className="w-full max-w-md bg-muted/30 border border-border rounded-2xl shadow-xl p-6 md:p-8 text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <CheckCircle size={42} className="mx-auto mb-4 text-green-500" />
        <h1 className="text-xl font-bold mb-2">You're unsubscribed</h1>
        <p className="text-muted-foreground mb-6">
          You won’t receive any more emails from us.
        </p>
        <Link
          to="/"
          className="inline-block bg-primary text-white px-5 py-2 rounded-xl transition hover:bg-primary/80"
        >
          Return to Homepage
        </Link>
      </motion.div>
    </div>
  );
}

// ✅ src/pages/Unsubscribe.jsx — On-Theme, Professional
import React from "react";
import NewsletterUnsubscribe from "../components/NewsletterUnsubscribe";
import { motion } from "framer-motion";

export default function Unsubscribe() {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center px-4">
      <motion.div
        className="w-full max-w-lg bg-muted/30 border border-border rounded-2xl shadow-xl p-6 md:p-8"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h1 className="text-2xl font-bold text-center mb-4">Unsubscribe</h1>
        <p className="text-sm text-muted-foreground text-center mb-6">
          Sorry to see you go — enter your email below to stop receiving updates.
        </p>
        <NewsletterUnsubscribe />
      </motion.div>
    </div>
  );
}

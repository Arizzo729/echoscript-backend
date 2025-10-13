import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import en from "./en";
import es from "./es";
import zh from "./zh"; // ✅ Add Chinese

i18n
  .use(LanguageDetector)        // 🌐 Detect browser or localStorage language
  .use(initReactI18next)        // 🔁 Hook into React
  .init({
    resources: {
      en: { translation: en },
      es: { translation: es },
      zh: { translation: zh }   // ✅ Register zh
    },
    fallbackLng: "en",
    debug: false,
    interpolation: {
      escapeValue: false
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage']
    },
    react: {
      useSuspense: false
    }
  });

export default i18n;


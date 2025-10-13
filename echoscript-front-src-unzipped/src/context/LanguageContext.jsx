// src/context/LanguageContext.jsx
import { createContext, useState, useEffect, useMemo, useContext, useCallback } from "react";
import i18n from "../i18n";

export const LanguageContext = createContext();

const supported = ["en", "es", "fr", "de", "zh"];

export const LanguageProvider = ({ children }) => {
  const getInitialLang = () => {
    if (typeof window === "undefined") return "en";
    const stored = localStorage.getItem("lang");
    const browserLang = (navigator.language || "en").slice(0, 2);
    if (supported.includes(stored)) return stored;
    if (supported.includes(browserLang)) return browserLang;
    return "en";
  };

  const [lang, setLang] = useState(getInitialLang);

  // persist selection
  useEffect(() => {
    try {
      localStorage.setItem("lang", lang);
    } catch {}
  }, [lang]);

  // keep i18next synchronized with context language
  useEffect(() => {
    if (i18n.language !== lang) {
      i18n.changeLanguage(lang).catch((e) => console.warn("i18n changeLanguage failed:", e));
    }
  }, [lang]);

  // cycle through supported languages
  const toggleLang = useCallback(() => {
    const idx = supported.indexOf(lang);
    const next = supported[(idx + 1) % supported.length];
    setLang(next);
  }, [lang]);

  const value = useMemo(() => ({ lang, toggleLang, setLang, supported }), [lang, toggleLang]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
};

export const useLanguage = () => useContext(LanguageContext);


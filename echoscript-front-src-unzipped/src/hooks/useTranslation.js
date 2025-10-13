// src/hooks/useTranslation.js
import { useContext, useEffect, useCallback } from "react";
import i18n from "../i18n"; // single source of truth (re-export from i18n.js or i18n/index.js)
import { LanguageContext } from "../context/LanguageContext";

/**
 * useTranslation — unified translation hook
 * - syncs LanguageContext.lang -> i18next language
 * - returns t(key, options) that uses i18next (with fallback)
 */
export default function useTranslation() {
  const { lang } = useContext(LanguageContext);

  // keep i18next in sync with our LanguageContext
  useEffect(() => {
    if (!lang || i18n.language === lang) return;
    i18n.changeLanguage(lang).catch((e) => console.warn("i18n changeLanguage failed:", e));
  }, [lang]);

  // stable t() reference
  const t = useCallback(
    (key, options) => {
      try {
        return i18n.t(key, options);
      } catch {
        // extremely defensive fallback to the key itself
        return key;
      }
    },
    []
  );

  return t;
}

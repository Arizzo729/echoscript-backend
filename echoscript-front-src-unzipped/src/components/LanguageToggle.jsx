import React from "react";
import { useTranslation } from "react-i18next";
import { Globe } from "lucide-react";

const languages = [
  { code: "en", label: "English" },
  { code: "es", label: "Español" },
  { code: "zh", label: "中文 (简体)" }
];

export default function LanguageToggle({ className = "" }) {
  const { i18n } = useTranslation();

  const handleChange = (e) => {
    const selectedLang = e.target.value;
    if (i18n && selectedLang) {
      i18n.changeLanguage(selectedLang);
      localStorage.setItem("i18nextLng", selectedLang);
    }
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Globe className="w-4 h-4 text-white" aria-hidden="true" />
      <select
        value={i18n?.resolvedLanguage || "en"}
        onChange={handleChange}
        className="bg-zinc-800 text-white text-sm rounded-md px-2 py-1 border border-zinc-600 focus:outline-none focus:ring focus:ring-primary/50"
        aria-label="Select language"
      >
        {languages.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.label}
          </option>
        ))}
      </select>
    </div>
  );
}


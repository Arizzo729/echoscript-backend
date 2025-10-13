import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import ToggleButton from "./ToggleButton";
import { Globe } from "lucide-react";

export default function LanguageToggle({ className = "" }) {
  const { i18n } = useTranslation();
  const [toggled, setToggled] = useState(i18n.language === "es");

  useEffect(() => {
    const storedLang = localStorage.getItem("i18nextLng");
    if (storedLang === "es" || storedLang === "en") {
      setToggled(storedLang === "es");
      i18n.changeLanguage(storedLang);
    }
  }, []);

  const handleToggle = (newState) => {
    const lang = newState ? "es" : "en";
    i18n.changeLanguage(lang);
    localStorage.setItem("i18nextLng", lang);
    setToggled(newState);
  };

  return (
    <ToggleButton
      onToggle={handleToggle}
      initial={toggled}
      labelOn="Español"
      labelOff="English"
      iconOn={<Globe className="w-4 h-4" />}
      iconOff={<Globe className="w-4 h-4" />}
      size="sm"
      className={className}
      ariaLabelOn="Cambiar a Español"
      ariaLabelOff="Switch to English"
    />
  );
}


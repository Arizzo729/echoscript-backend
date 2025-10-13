import { createContext, useContext, useState, useEffect } from "react";

const FontSizeContext = createContext(undefined);

const MIN = 0.85;
const MAX = 1.25;
const DEFAULT = 1;
const STORAGE_KEY = "font-size";

export function FontSizeProvider({ children }) {
  const [fontSize, setFontSizeRaw] = useState(DEFAULT);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const stored = parseFloat(localStorage.getItem(STORAGE_KEY));
      if (!isNaN(stored) && stored >= MIN && stored <= MAX) {
        setFontSizeRaw(stored);
      }
    } catch {
      setFontSizeRaw(DEFAULT);
    }
  }, []);

  // Save to localStorage on change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, fontSize.toFixed(2));
  }, [fontSize]);

  // Clamping + setter
  const setFontSize = (size) => {
    const clamped = Math.min(Math.max(size, MIN), MAX);
    setFontSizeRaw(clamped);
  };

  return (
    <FontSizeContext.Provider value={{ fontSize, setFontSize }}>
      <div
        className="transition-all duration-300 ease-in-out motion-reduce:transition-none"
        style={{ fontSize: `${fontSize}em` }}
      >
        {children}
      </div>
    </FontSizeContext.Provider>
  );
}

export function useFontSize() {
  const context = useContext(FontSizeContext);
  if (!context)
    throw new Error("useFontSize must be used within a FontSizeProvider");
  return context;
}

export { FontSizeContext };





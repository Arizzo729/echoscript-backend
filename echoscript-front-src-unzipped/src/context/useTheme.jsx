import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";

const THEME_STORAGE_KEY = "theme-preference";
const ThemeContext = createContext();

/**
 * Determines the user's preferred theme:
 * - Checks localStorage first
 * - Falls back to system preference
 */
function getPreferredTheme() {
  if (typeof window === "undefined") return "light";
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

/**
 * Custom hook to manage and sync theme
 */
function useThemeSync() {
  const [theme, setTheme] = useState(getPreferredTheme);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle("dark", theme === "dark");

    const timeout = setTimeout(() => {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
      window.dispatchEvent(
        new CustomEvent("theme-changed", {
          detail: theme,
        })
      );
    }, 50);

    return () => clearTimeout(timeout);
  }, [theme]);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const listener = (e) => {
      const next = e.matches ? "dark" : "light";
      setTheme(next);
    };
    mediaQuery.addEventListener("change", listener);
    return () => mediaQuery.removeEventListener("change", listener);
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  return { theme, toggleTheme };
}

/**
 * Provider to wrap the app with theme context
 */
export function ThemeProvider({ children }) {
  const value = useThemeSync();
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/**
 * Hook to access theme context
 */
export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}



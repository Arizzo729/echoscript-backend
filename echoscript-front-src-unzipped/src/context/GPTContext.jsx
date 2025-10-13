// ✅ GPTContext.jsx — Persistent memory + identity + context sharing
import React, { createContext, useState, useEffect } from "react";

export const GPTContext = createContext();

export function GPTProvider({ children }) {
  const [user, setUser] = useState(null);
  const [contextMessage, setContextMessage] = useState("");

  // Load user from localStorage on mount
  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      try {
        const parsed = JSON.parse(savedUser);
        if (parsed && typeof parsed === "object") setUser(parsed);
      } catch {
        setUser(null);
      }
    }
  }, []);

  // Save to localStorage on update
  const updateUser = (data) => {
    setUser(data);
    localStorage.setItem("user", JSON.stringify(data));
  };

  return (
    <GPTContext.Provider
      value={{
        user,
        setUser: updateUser,
        contextMessage,
        setContextMessage,
      }}
    >
      {children}
    </GPTContext.Provider>
  );
}

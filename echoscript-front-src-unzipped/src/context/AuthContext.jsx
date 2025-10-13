// src/context/AuthContext.jsx
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import api from "../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  // Load session once on mount
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const me = await api.me();
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setReady(true);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  async function signIn({ email, password, remember }) {
    const res = await api.login({ email, password, remember });
    // immediately refresh me so context has {id,email,...}
    try {
      const me = await api.me();
      setUser(me);
    } catch {
      // fallback: synthesize from payload if /me not present
      setUser({ email: res?.email || email, id: res?.id, mode: "jwt" });
    }
  }

  async function signOut() {
    try { await api.logout(); } finally { setUser(null); }
  }

  async function refresh() {
    const me = await api.me();
    setUser(me);
  }

  const value = useMemo(() => ({
    user,
    ready,
    signIn,
    signOut,
    refresh,
    isAuthenticated: !!user?.email,
  }), [user, ready]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}


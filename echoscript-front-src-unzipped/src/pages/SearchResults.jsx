// src/pages/SearchResults.jsx
import React, { useEffect, useMemo, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";

export default function SearchResults() {
  const [params, setParams] = useSearchParams();
  const q = (params.get("q") || "").trim();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState([]);

  // Keep the input in sync with the URL (?q=...)
  const [input, setInput] = useState(q);
  useEffect(() => setInput(q), [q]);

  useEffect(() => {
    let abort = false;
    async function run() {
      if (!q) { setResults([]); return; }
      setLoading(true); setError(null);
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`, { credentials: "include" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setResults(Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : []);
      } catch (e) {
        if (!abort) setError(e?.message || String(e));
      } finally {
        if (!abort) setLoading(false);
      }
    }
    run();
    return () => { abort = true; };
  }, [q]);

  const onSubmit = (e) => {
    e.preventDefault();
    const next = (input || "").trim();
    setParams(next ? { q: next } : {});
  };

  return (
    <div className="container-prose py-6">
      <form onSubmit={onSubmit} className="flex gap-2 mb-4">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Search transcripts, pages, actions…"
          className="flex-1 px-3 py-2 rounded-xl bg-white/10 border border-white/10 focus:outline-none focus:ring-2 focus:ring-teal-500"
        />
      <button className="btn btn-primary" type="submit">Search</button>
      </form>

      {loading && <p className="muted">Searching…</p>}
      {error && (
        <div className="card">
          <div className="text-red-300 font-medium">Search isn’t ready yet.</div>
          <p className="muted mt-1">The endpoint <code>/api/search</code> returned <code>{String(error)}</code>. You can still use the header’s type-ahead for quick navigation.</p>
        </div>
      )}

      {!loading && !error && q && results.length === 0 && (
        <p className="muted">No results for “{q}”.</p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {results.map((r, i) => (
          <Link
            to={r.path || r.url || "#"}
            key={(r.id || r.path || r.url || i) + ""}
            className="card hover:bg-white/10 transition"
          >
            <div className="text-sm text-zinc-400">{r.type || "Result"}</div>
            <div className="text-lg font-semibold mt-1">{r.title || r.label || r.name || "Untitled"}</div>
            {r.snippet && <p className="muted mt-1">{r.snippet}</p>}
          </Link>
        ))}
      </div>
    </div>
  );
}

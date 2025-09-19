import { useState } from "react";
import { transcribe, JobOut } from "./lib/api";

export default function App() {
  const [resp, setResp] = useState<JobOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState("en");

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setResp(null);

    const input = (e.currentTarget.elements.namedItem("file") as HTMLInputElement);
    const file = input?.files?.[0];
    if (!file) { setError("Pick a file first."); return; }

    try {
      setBusy(true);
      const out = await transcribe(file, language || undefined);
      setResp(out);
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", maxWidth: 760, margin: "2rem auto", padding: "0 1rem" }}>
      <h1>EchoScript – Transcribe</h1>

      <form onSubmit={onSubmit} style={{ border: "1px solid #ddd", borderRadius: 12, padding: 16, display: "grid", gap: 12 }}>
        <input name="file" type="file" accept="audio/*,video/*" />
        <label>
          Language:&nbsp;
          <select value={language} onChange={e => setLanguage(e.target.value)}>
            <option value="en">English (en)</option>
            <option value="">Auto-detect</option>
          </select>
        </label>
        <button disabled={busy} type="submit">{busy ? "Transcribing…" : "Transcribe"}</button>
      </form>

      {error && <p style={{ color: "crimson", marginTop: 16 }}>Error: {error}</p>}

      {resp && (
        <section style={{ marginTop: 24 }}>
          <h3>Result</h3>
          <pre style={{ whiteSpace: "pre-wrap", background: "#f8f8f8", padding: 12, borderRadius: 8 }}>
{JSON.stringify(resp, null, 2)}
          </pre>
          {resp.transcript && (
            <>
              <h3>Transcript</h3>
              <p style={{ lineHeight: 1.6 }}>{resp.transcript}</p>
            </>
          )}
        </section>
      )}
    </main>
  );
}

// src/components/AdaptiveAI.jsx
import React, { useState, useEffect, useCallback, useRef } from "react";
import { AutomationService, PROVIDERS } from "../services/AutomationService";

export default function AdaptiveAI({
  initialProvider = PROVIDERS.BROWSE_AI,
  automationId,
  inputData,
  adaptiveContext = {},
  service = AutomationService,
}) {
  const [provider, setProvider] = useState(initialProvider);
  const [status, setStatus] = useState("idle");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [log, setLog] = useState([]);
  const abortRef = useRef(null);

  const appendLog = (msg) =>
    setLog((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);

  const chooseProviderAdaptive = useCallback(() => {
    // Previously: PROVIDERS.OCTOPARSE (undefined). Use APIFY instead.
    if (typeof inputData === "string" && inputData.length > 1000) return PROVIDERS.APIFY;
    return initialProvider;
  }, [inputData, initialProvider]);

  const runAutomation = useCallback(async () => {
    setStatus("running");
    setError(null);
    setResult(null);
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    appendLog(`🔁 Starting automation with provider: ${provider}`);

    try {
      const res = await service.runAutomation(provider, automationId, inputData, {
        signal: abortRef.current.signal,
        context: adaptiveContext,
      });
      appendLog(`✅ Automation completed successfully.`);
      setResult(res);
      setStatus("success");
    } catch (err) {
      if (err.name === "AbortError") {
        appendLog(`⏹️ Automation aborted.`);
      } else {
        appendLog(`❌ Automation failed: ${err.message}`);
        setError(err.message);
        setStatus("error");
      }
    }
  }, [provider, automationId, inputData, service, adaptiveContext]);

  useEffect(() => {
    const newProvider = chooseProviderAdaptive();
    if (newProvider !== provider) {
      appendLog(`🤖 Adaptive AI switched provider → ${newProvider}`);
      setProvider(newProvider);
    }
  }, [chooseProviderAdaptive, provider]);

  useEffect(() => {
    if (automationId && inputData) runAutomation();
  }, [automationId, inputData, runAutomation]);

  return (
    <div className="adaptive-ai-widget p-6 bg-gradient-to-br from-white via-zinc-50 to-zinc-100 dark:from-zinc-900 dark:via-zinc-950 dark:to-zinc-900 rounded-2xl shadow-xl max-w-3xl mx-auto font-inter space-y-6">
      <header>
        <h2 className="text-2xl font-bold text-teal-600 dark:text-teal-400 mb-1">
          Adaptive AI Automation
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Our system auto-selects the best provider based on your input context.
        </p>
      </header>

      <div>
        <label htmlFor="provider-select" className="block mb-1 font-semibold text-sm">
          Select Provider:
        </label>
        <select
          id="provider-select"
          className="p-2 border rounded-md w-full max-w-xs text-sm dark:bg-zinc-800 dark:border-zinc-700 focus:ring-2 focus:ring-teal-400"
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
          disabled={status === "running"}
        >
          {Object.entries(PROVIDERS).map(([key, val]) => (
            <option key={val} value={val}>
              {key}
            </option>
          ))}
        </select>
      </div>

      <div className="min-h-[64px]">
        {status === "idle" && <p className="text-gray-500 dark:text-gray-400">Awaiting input to run automation...</p>}
        {status === "running" && (
          <p className="text-blue-600 dark:text-blue-400 font-medium flex items-center animate-pulse">
            Running automation... <LoadingSpinner />
          </p>
        )}
        {status === "success" && result && (
          <div className="relative">
            <pre className="bg-gray-100 dark:bg-zinc-800 rounded-lg p-4 overflow-x-auto max-h-64 text-xs sm:text-sm whitespace-pre-wrap leading-snug">
              {JSON.stringify(result, null, 2)}
            </pre>
            <button
              onClick={() => navigator.clipboard.writeText(JSON.stringify(result, null, 2))}
              className="absolute top-2 right-2 px-2 py-1 text-xs bg-zinc-200 hover:bg-zinc-300 dark:bg-zinc-700 dark:hover:bg-zinc-600 rounded"
              aria-label="Copy result to clipboard"
            >
              Copy
            </button>
          </div>
        )}
        {status === "error" && <p className="text-red-600 dark:text-red-400 font-medium">❌ Error: {error}</p>}
      </div>

      <div>
        <button
          onClick={runAutomation}
          className="px-5 py-2.5 bg-teal-600 hover:bg-teal-700 dark:bg-teal-400 dark:hover:bg-teal-300 text-white dark:text-black rounded-lg font-semibold transition disabled:opacity-60 shadow-sm"
          disabled={status === "running"}
        >
          Run Automation
        </button>
      </div>

      <details className="bg-zinc-50 dark:bg-zinc-800 rounded-xl p-4 text-sm">
        <summary className="cursor-pointer font-semibold">View Logs ({log.length})</summary>
        <div className="mt-2 max-h-48 overflow-y-auto font-mono whitespace-pre-wrap text-zinc-700 dark:text-zinc-300">
          {log.map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </div>
      </details>
    </div>
  );
}

const LoadingSpinner = () => (
  <svg className="inline animate-spin h-5 w-5 ml-2 text-blue-600 dark:text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
  </svg>
);

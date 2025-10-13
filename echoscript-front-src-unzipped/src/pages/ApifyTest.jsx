import React, { useEffect, useState } from "react";
import { AutomationService, PROVIDERS } from "../services/AutomationService";

export default function ApifyTest() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  // Provide via .env: VITE_APIFY_TASK_ID=xxxxx
  const taskId = import.meta.env.VITE_APIFY_TASK_ID;

  useEffect(() => {
    const fetchData = async () => {
      try {
        if (!taskId) {
          throw new Error(
            "Missing VITE_APIFY_TASK_ID. Add it to your .env to run this page."
          );
        }
        const result = await AutomationService.runAutomation(PROVIDERS.APIFY, taskId);
        setData(result);
      } catch (err) {
        setError(err.message || String(err));
      }
    };
    fetchData();
  }, [taskId]);

  return (
    <div className="p-6 max-w-3xl mx-auto mt-10 bg-white dark:bg-zinc-800 rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-4">🔍 Apify Task Output</h2>
      {error && <p className="text-red-400 whitespace-pre-wrap">Error: {error}</p>}
      {data ? (
        <pre className="bg-gray-100 dark:bg-gray-900 p-4 rounded text-sm overflow-x-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      ) : !error ? (
        <p className="text-zinc-500 italic">Loading...</p>
      ) : null}
    </div>
  );
}


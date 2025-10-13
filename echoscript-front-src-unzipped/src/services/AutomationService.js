// ✅ EchoScript.AI — Unified Automation Service Engine
const PROVIDERS = {
  BROWSE_AI: "browseAI",
  BARDEEN_AI: "bardeenAI",
  APIFY: "apify",
  BRIGHTDATA: "brightData",
};

const config = {
  browseAI: {
    apiBase: "https://api.browse.ai/v1",
    apiKey: import.meta.env.VITE_BROWSE_AI_API_KEY,
  },
  apify: {
    apiBase: "https://api.apify.com/v2",
    token: import.meta.env.VITE_APIFY_API_TOKEN,
  },
  brightData: {
    username: import.meta.env.VITE_BRIGHTDATA_USERNAME,
    password: import.meta.env.VITE_BRIGHTDATA_PASSWORD,
    proxyEndpoint: "zproxy.lum-superproxy.io:22225",
  },
};

const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1500;

class AutomationService {
  /**
   * Resilient fetch with retries and helpful messages
   */
  static async fetchWithRetries(url, options, retries = MAX_RETRIES) {
    try {
      const res = await fetch(url, options);
      if (!res.ok) {
        const errorText = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status}: ${errorText || "Request failed"}`);
      }
      // prefer JSON, fall back to text
      const ct = res.headers.get("content-type") || "";
      if (ct.includes("application/json")) return await res.json();
      return await res.text();
    } catch (error) {
      if (retries > 0) {
        await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
        return this.fetchWithRetries(url, options, retries - 1);
      }
      throw new Error(`Failed after ${MAX_RETRIES} attempts → ${error.message}`);
    }
  }

  /**
   * Dispatch to provider handlers
   */
  static async runAutomation(provider, automationId, inputData = {}, options = {}) {
    switch (provider) {
      case PROVIDERS.BROWSE_AI:
        return await this._runBrowseAI(automationId, inputData, options);
      case PROVIDERS.APIFY:
        // allow { apifyToken, input } in options
        return await this._runApify(automationId, options.apifyToken, options.input);
      case PROVIDERS.BRIGHTDATA:
        return await this._runBrightData(inputData);
      case PROVIDERS.BARDEEN_AI:
        throw new Error("Bardeen.AI requires manual extension execution.");
      default:
        throw new Error(`❌ Unsupported provider: ${provider}`);
    }
  }

  /**
   * Browse.AI automation runner
   */
  static async _runBrowseAI(automationId, inputData, { webhookUrl, batchId } = {}) {
    const { apiBase, apiKey } = config.browseAI;
    const url = `${apiBase}/automations/${automationId}/run`;
    const body = { inputData, webhookUrl, batchId };

    const options = {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    };

    return await this.fetchWithRetries(url, options);
  }

  /**
   * Apify task runner
   * - GET for simple runs
   * - POST with JSON body when input is provided
   * Returns dataset items (Apify run-sync-get-dataset-items).
   */
  static async _runApify(taskId, token = config.apify.token, input) {
    const base = `${config.apify.apiBase}/actor-tasks/${taskId}/run-sync-get-dataset-items?token=${encodeURIComponent(
      token || ""
    )}`;

    const hasInput = input && Object.keys(input).length > 0;
    const url = base;
    const options = hasInput
      ? {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(input),
        }
      : { method: "GET" };

    return await this.fetchWithRetries(url, options);
  }

  /**
   * BrightData proxy-based example (client-side only as placeholder; real use should be server-side)
   */
  static async _runBrightData(inputData) {
    const { username, password, proxyEndpoint } = config.brightData;
    if (!username || !password) {
      throw new Error("BrightData credentials missing — set VITE_BRIGHTDATA_USERNAME/PASSWORD.");
    }
    // NOTE: Real proxying must be done server-side with an HTTP agent; this is a placeholder.
    const url = "https://target-site.com/api/search";
    const options = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: inputData }),
    };
    return await this.fetchWithRetries(url, options);
  }

  /**
   * Run a batch of automations for a provider
   */
  static async runBatch(provider, automations = []) {
    const results = [];
    for (const { automationId, inputData, options } of automations) {
      try {
        const data = await this.runAutomation(provider, automationId, inputData, options);
        results.push({ automationId, status: "success", data });
      } catch (err) {
        console.error(`Automation failed [${provider} → ${automationId}]`, err);
        results.push({ automationId, status: "error", error: err.message });
      }
    }
    return results;
  }
}

export { AutomationService, PROVIDERS };

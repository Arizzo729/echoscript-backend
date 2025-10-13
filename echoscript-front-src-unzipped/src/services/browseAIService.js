// ✅ EchoScript.AI — Browse.AI convenience wrapper (delegates to AutomationService)
import { AutomationService, PROVIDERS } from "./AutomationService";

/**
 * Run a Browse.AI automation with optional inputData and options.
 * Keeps all retry/config logic centralized in AutomationService.
 *
 * @param {string} automationId
 * @param {object} inputData
 * @param {object} options  e.g. { webhookUrl, batchId }
 * @returns {Promise<any>}
 */
export async function runBrowseAI(automationId, inputData = {}, options = {}) {
  return AutomationService.runAutomation(
    PROVIDERS.BROWSE_AI,
    automationId,
    inputData,
    options
  );
}

// ✅ EchoScript.AI — Local monthly usage tracker (guest/unauthenticated caps)
const STORAGE_KEY = "echoscript_usage";
const MONTHLY_LIMIT_MINUTES = Number(import.meta.env.VITE_MONTHLY_LIMIT_MINUTES || 60);

export function getTranscriptionUsage() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return { minutesUsed: 0, month: currentMonth(), limit: MONTHLY_LIMIT_MINUTES };

  try {
    const data = JSON.parse(raw);
    if (data.month !== currentMonth()) {
      return { minutesUsed: 0, month: currentMonth(), limit: MONTHLY_LIMIT_MINUTES };
    }
    return { ...data, limit: MONTHLY_LIMIT_MINUTES };
  } catch {
    return { minutesUsed: 0, month: currentMonth(), limit: MONTHLY_LIMIT_MINUTES };
  }
}

export function updateTranscriptionUsage(minutesToAdd) {
  const usage = getTranscriptionUsage();
  const newUsage = {
    minutesUsed: Math.max(0, usage.minutesUsed + Number(minutesToAdd || 0)),
    month: currentMonth(),
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(newUsage));
  return { ...newUsage, limit: MONTHLY_LIMIT_MINUTES };
}

export function hasRemainingMinutes(minutesNeeded) {
  const usage = getTranscriptionUsage();
  return usage.minutesUsed + Number(minutesNeeded || 0) <= MONTHLY_LIMIT_MINUTES;
}

export function getRemainingMinutes() {
  const usage = getTranscriptionUsage();
  return Math.max(0, MONTHLY_LIMIT_MINUTES - usage.minutesUsed);
}

function currentMonth() {
  const now = new Date();
  // zero-pad month to keep string sorting sane (e.g., "2025-09")
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${now.getFullYear()}-${month}`;
}


// ✅ cn.js — Advanced className combiner with optional Tailwind merge
export function cn(...args) {
  const classNames = [];

  const walk = (arg) => {
    if (!arg) return;
    if (typeof arg === "string") {
      classNames.push(arg);
    } else if (typeof arg === "object") {
      if (Array.isArray(arg)) {
        arg.forEach(walk);
      } else {
        Object.entries(arg).forEach(([key, value]) => {
          if (value) classNames.push(key);
        });
      }
    }
  };

  args.forEach(walk);

  // Optional: Deduplicate common Tailwind classes (basic example)
  return dedupeTailwind(classNames.join(" "));
}

// Optional basic Tailwind deduplication (extend as needed)
function dedupeTailwind(str) {
  const seen = new Set();
  const tokens = str.trim().split(/\s+/);
  const final = [];

  // Simple override rules: last class wins (esp. for font, bg, text, flex)
  const overridePrefix = ["bg-", "text-", "font-", "flex", "grid", "justify-", "items-", "gap-"];

  tokens.reverse().forEach((token) => {
    const shouldOverride = overridePrefix.some((prefix) => token.startsWith(prefix));
    if (!seen.has(token) || shouldOverride) {
      seen.add(token);
      final.unshift(token);
    }
  });

  return final.join(" ");
}

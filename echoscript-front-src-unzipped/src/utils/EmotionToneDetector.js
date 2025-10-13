// ✅ EchoScript.AI — Emotion/Tone heuristic detector (lightweight client-side)
export default function detectTone(text) {
  if (!text) return "neutral";
  const lower = String(text).toLowerCase();

  // Expanded dictionaries, case-insensitive
  const positiveRegex =
    /\b(amazing|awesome|great|excited|cool|yay|yes|love|fantastic|wonderful|incredible|happy|satisfied|blessed|joyful|thrilled|grateful|excellent|brilliant|nice|good|perfect|stoked|pumped|win|winning)\b/i;

  const negativeRegex =
    /\b(sad|tired|bad|confused|lost|sorry|angry|upset|hate|frustrated|annoyed|depressed|stressed|miserable|lonely|terrible|ugh|nope|awful|horrible|disappointed|worried|anxious|mad|furious|irritated|bummed)\b/i;

  if (positiveRegex.test(lower)) return "positive";
  if (negativeRegex.test(lower)) return "negative";
  return "neutral";
}

// src/hooks/useVoiceInput.js — EchoScript.AI real-time voice input hook
import { useEffect, useRef, useState, useCallback } from "react";

/**
 * @param {Object} opts
 * @param {(text:string)=>void} [opts.onTranscript]   called with finalized chunks
 * @param {(text:string)=>void} [opts.onInterim]      called with interim partials
 * @param {string} [opts.lang="en-US"]                BCP-47 locale (e.g., "en-US", "es-ES")
 * @returns {{listening:boolean, startListening:Function, stopListening:Function, error:string|null}}
 */
export default function useVoiceInput({ onTranscript = () => {}, onInterim, lang = "en-US" } = {}) {
  const [listening, setListening] = useState(false);
  const [error, setError] = useState(null);
  const recognitionRef = useRef(null);

  // initialize once
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError("SpeechRecognition is not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = lang;
    recognitionRef.current = recognition;

    recognition.onresult = (event) => {
      let finalText = "";
      let interimText = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0]?.transcript || "";
        if (event.results[i].isFinal) finalText += t + " ";
        else interimText += t;
      }
      if (interimText && typeof onInterim === "function") onInterim(interimText);
      if (finalText.trim()) onTranscript(finalText.trim());
    };

    recognition.onerror = (evt) => {
      // most common: "not-allowed", "no-speech", "audio-capture"
      setError(evt?.error || "speech_error");
      setListening(false);
    };

    recognition.onend = () => {
      setListening(false);
    };

    return () => {
      try {
        recognition.stop();
      } catch {}
      recognitionRef.current = null;
    };
    // intentionally omit onTranscript/onInterim from deps to avoid reinit
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang]);

  const startListening = useCallback(() => {
    setError(null);
    const rec = recognitionRef.current;
    if (!rec || listening) return;
    try {
      const p = rec.start();
      // Chrome returns undefined, Safari returns a Promise
      if (p?.catch) p.catch((e) => setError(e?.message || "start_failed"));
      setListening(true);
    } catch (e) {
      setError(e?.message || "start_failed");
      setListening(false);
    }
  }, [listening]);

  const stopListening = useCallback(() => {
    const rec = recognitionRef.current;
    if (!rec) return;
    try {
      rec.stop();
    } catch {}
    setListening(false);
  }, []);

  return { listening, startListening, stopListening, error };
}


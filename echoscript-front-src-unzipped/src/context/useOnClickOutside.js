import { useEffect } from "react";

/**
 * useOnClickOutside — detects clicks outside a referenced element
 * @param {React.RefObject} ref - element to monitor
 * @param {Function} handler - callback for outside click
 */
export function useOnClickOutside(ref, handler) {
  useEffect(() => {
    if (!ref?.current || typeof handler !== "function") return;

    const listener = (event) => {
      // If ref is unmounted or click is inside, ignore
      if (!ref.current || ref.current.contains(event.target)) return;
      handler(event);
    };

    document.addEventListener("mousedown", listener, true);
    document.addEventListener("touchstart", listener, true);

    return () => {
      document.removeEventListener("mousedown", listener, true);
      document.removeEventListener("touchstart", listener, true);
    };
  }, [ref, handler]);
}

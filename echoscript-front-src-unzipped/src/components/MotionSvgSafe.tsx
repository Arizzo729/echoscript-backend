// src/components/MotionSvgSafe.tsx
import { motion } from "framer-motion";

export function MotionSvgSafe({ style, ...rest }) {
  // Strip any accidental style.viewBox (from callers or libs)
  const { viewBox, ...styleSafe } = style || {};
  return <motion.svg {...rest} style={styleSafe} />;
}

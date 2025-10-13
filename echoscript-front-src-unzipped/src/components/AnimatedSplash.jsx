/**
 * AnimatedSplash (Stub)
 *␊
 * The original animated splash has been removed. This stub simply calls
 * the provided onComplete callback and renders nothing. It is still imported
 * throughout the app to preserve the onboarding flow.
 */
import { useEffect } from 'react';

export default function AnimatedSplash({ onComplete }) {
  useEffect(() => {
    onComplete?.();
  }, [onComplete]);

  return null;
}





/*
import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
} from "react";
import { motion, AnimatePresence } from "framer-motion";
import { gsap } from "gsap";

export default function AnimatedSplash({
  onComplete,
  skipOnClick = true,
  displayTime = 3000,
}) {
  const [visible, setVisible] = useState(true);
  const [progress, setProgress] = useState(0);
  const logoRef = useRef(null);
  const orbRef = useRef(null);
  const timerRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.to(logoRef.current, {
        backgroundPosition: "200% center",
        duration: 3,
        ease: "power2.inOut",
        repeat: -1,
        yoyo: true,
      });
      gsap.to(orbRef.current, {
        rotate: 360,
        duration: 30,
        ease: "linear",
        repeat: -1,
      });
    });

    timerRef.current = setTimeout(closeSplash, displayTime);

    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        const next = prev + 1 + Math.random();
        return next < 100 ? next : 100;
      });
    }, displayTime / 100);

    return () => {
      clearTimeout(timerRef.current);
      clearInterval(progressInterval);
      ctx.revert();
    };
  }, [displayTime]);

  const closeSplash = useCallback(() => {
    gsap.to(".splash-container", {
      opacity: 0,
      duration: 0.4,
      onComplete: () => {
        setVisible(false);
        onComplete?.();
      },
    });
  }, [onComplete]);

  const onClickHandler = () => skipOnClick && closeSplash();

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className="splash-container fixed inset-0 z-50 flex flex-col items-center justify-center bg-zinc-950 text-white p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, transition: { duration: 0.4 } }}
          onClick={onClickHandler}
        >
          <div
            ref={orbRef}
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-gradient-to-tr from-teal-500 via-blue-500 to-teal-400 opacity-10 blur-4xl pointer-events-none"
          />

          <div
            ref={logoRef}
            className="relative w-48 h-48 mb-4 bg-no-repeat bg-center"
            style={{
              WebkitMaskImage: "url('/Logo.png')",
              maskImage: "url('/Logo.png')",
              WebkitMaskSize: "contain",
              maskSize: "contain",
              WebkitMaskRepeat: "no-repeat",
              maskRepeat: "no-repeat",
              WebkitMaskPosition: "center",
              maskPosition: "center",
              backgroundImage: "linear-gradient(90deg, #14b8a6, #0ea5e9, #14b8a6)",
              backgroundSize: "300% auto",
            }}
          />

          <motion.h1
            className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-6"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.5 }}
          >
            EchoScript<span className="text-teal-400">.AI</span>
          </motion.h1>

          <div className="w-28 h-28 sm:w-32 sm:h-32 mb-4 flex items-center justify-center">
            <div className="animate-spin h-12 w-12 border-4 border-teal-400 border-t-transparent rounded-full" />
          </div>

          <div className="w-40 bg-gray-700 rounded-full overflow-hidden h-2 mb-2">
            <div
              className="h-full bg-teal-400 transition-all duration-200"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="text-sm text-gray-400 mb-4">
            Loading {Math.min(progress, 100).toFixed(0)}%
          </div>

          <button
            onClick={closeSplash}
            className="mt-2 px-4 py-2 bg-teal-500 hover:bg-teal-600 rounded-lg text-white transition"
          >
            Skip Intro
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
*/

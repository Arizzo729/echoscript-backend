// ✅ EchoScript.AI — Enhanced Button (No Prop Interference, Clean Drag, Glow, Sound)
import React from "react";
import { twMerge } from "tailwind-merge";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { useSound } from "../../context/SoundContext";

function Button({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  fullWidth = false,
  disableSound = false,
  glowOnSound = true,
  className = "",
  ...props
}) {
  const { playClick, isMuted } = useSound();

  const handleClick = (e) => {
    if (!disableSound && !isMuted) {
      playClick();
    }
    if (typeof props.onClick === "function") {
      props.onClick(e);
    }
  };

  const base =
    "relative inline-flex items-center justify-center font-medium select-none transition-all duration-300 ease-out group focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 shadow-sm";

  const sizes = {
    xs: "px-3 py-1 text-xs gap-1.5 rounded-full",
    sm: "px-4 py-1.5 text-sm gap-2 rounded-full",
    md: "px-5 py-2 text-sm gap-2.5 rounded-full",
    lg: "px-6 py-2.5 text-base gap-3 rounded-full",
  };

  const variants = {
    primary: `
      bg-teal-600 text-white
      hover:bg-teal-500 hover:shadow-teal-500/30
      shadow-md focus-visible:ring-teal-400
      dark:shadow-teal-400/20
    `,
    secondary: `
      bg-zinc-200 text-zinc-800
      hover:bg-zinc-300
      dark:bg-zinc-700 dark:text-white dark:hover:bg-zinc-600
      focus-visible:ring-zinc-400
    `,
    ghost: `
      bg-transparent text-teal-600 dark:text-teal-400
      hover:bg-teal-100 dark:hover:bg-teal-700/10
      focus-visible:ring-teal-400
    `,
    danger: `
      bg-red-500 text-white hover:bg-red-600
      dark:bg-red-600 dark:hover:bg-red-700
      focus-visible:ring-red-400
    `,
  };

  const glowClass =
    !isMuted && glowOnSound && variant === "primary" ? "sound-toggle-glow" : "";

  return (
    <motion.button
      type="button"
      onClick={handleClick}
      disabled={loading || props.disabled}
      whileTap={{ scale: 0.97 }}
      className={twMerge(
        base,
        sizes[size],
        variants[variant],
        glowClass,
        fullWidth && "w-full",
        loading && "opacity-70 cursor-not-allowed",
        className
      )}
      aria-busy={loading}
      {...props}
    >
      {loading && (
        <span className="absolute inset-0 flex items-center justify-center bg-white/10 dark:bg-black/10 rounded-full animate-pulse z-0">
          <Loader2 className="w-4 h-4 text-white animate-spin" />
        </span>
      )}
      <span className="relative z-10 inline-flex items-center">
        {icon && <span className={children ? "mr-2" : ""}>{icon}</span>}
        {children}
      </span>
    </motion.button>
  );
}

export { Button };
export default Button;



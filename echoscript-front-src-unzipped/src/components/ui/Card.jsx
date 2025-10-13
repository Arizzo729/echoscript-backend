// ✅ Card.jsx — Professional, Secure, Accessible Card Component Suite
import React from "react";
import PropTypes from "prop-types";
import { twMerge } from "tailwind-merge";

// Utility fallback for class merging
function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

// Main Card container
export function Card({ className = "", children, ...props }) {
  return (
    <section
      role="region"
      aria-label="Card container"
      tabIndex={0}
      className={twMerge(
        cn(
          "bg-zinc-900",
          "border border-zinc-700",
          "rounded-2xl",
          "shadow-md",
          "p-4",
          "transition-all duration-300",
          "hover:shadow-lg",
          "focus-within:ring-2",
          "focus-within:ring-teal-500",
          "text-white"
        ),
        className
      )}
      {...props}
    >
      {children}
    </section>
  );
}

Card.propTypes = {
  className: PropTypes.string,
  children: PropTypes.node.isRequired,
};

// Header section
export function CardHeader({ className = "", children }) {
  return (
    <header className={twMerge("mb-2 flex flex-col gap-1", className)}>
      {children}
    </header>
  );
}

CardHeader.propTypes = {
  className: PropTypes.string,
  children: PropTypes.node.isRequired,
};

// Title
export function CardTitle({ className = "", children }) {
  return (
    <h3 className={twMerge("text-lg font-bold tracking-tight", className)}>
      {children}
    </h3>
  );
}

CardTitle.propTypes = {
  className: PropTypes.string,
  children: PropTypes.node.isRequired,
};

// Optional description
export function CardDescription({ className = "", children }) {
  return (
    <p className={twMerge("text-sm text-zinc-400", className)}>
      {children}
    </p>
  );
}

CardDescription.propTypes = {
  className: PropTypes.string,
  children: PropTypes.node.isRequired,
};

// Content area
export function CardContent({ className = "", children }) {
  return (
    <div className={twMerge("text-sm text-zinc-300", className)}>
      {children}
    </div>
  );
}

CardContent.propTypes = {
  className: PropTypes.string,
  children: PropTypes.node.isRequired,
};

// Footer section (usually for actions)
export function CardFooter({ className = "", children }) {
  return (
    <footer className={twMerge("mt-4 flex justify-end gap-2", className)}>
      {children}
    </footer>
  );
}

CardFooter.propTypes = {
  className: PropTypes.string,
  children: PropTypes.node.isRequired,
};


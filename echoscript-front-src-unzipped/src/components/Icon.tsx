// src/components/Icon.jsx
import React from "react";

/** Accepts either a React component or a string URL (png/svg/data:) */
export default function Icon({
  icon,
  className,
  alt = "",
  ...rest
}) {
  if (typeof icon === "string") {
    return <img src={icon} alt={alt} className={className} {...rest} />;
  }
  const C = icon; // React component
  return <C className={className} aria-label={alt || undefined} {...rest} />;
}

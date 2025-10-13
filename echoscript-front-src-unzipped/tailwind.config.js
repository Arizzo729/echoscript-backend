// tailwind.config.js (FINAL)
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    // Keep default breakpoints; add yours via `extend` instead of replacing
    screens: {
      sm: "640px",
      md: "768px",
      lg: "1024px",
      xl: "1280px",
      "2xl": "1536px",
    },
    extend: {
      // put custom tokens here so defaults remain intact
    },
  },
  plugins: [],
};

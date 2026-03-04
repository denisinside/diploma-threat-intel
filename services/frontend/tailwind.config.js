/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Tactical / Palantir palette
        slate: {
          950: "#0F172A", // primary background
        },
        tactical: {
          amber: "#F59E0B", // warnings, critical
          sky: "#38BDF8",   // interactive elements
        },
        severity: {
          critical: "#DC2626",
          high: "#F59E0B",
          medium: "#EAB308",
          low: "#22C55E",
        },
      },
      fontFamily: {
        sans: ["Roboto Condensed", "system-ui", "sans-serif"],
      },
      backdropBlur: {
        xs: "2px",
      },
      backgroundImage: {
        "glass-panel": "linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.7) 100%)",
      },
    },
  },
  plugins: [],
};

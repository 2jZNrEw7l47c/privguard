import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: "#0f1117",
        panel: "#1a1d27",
        border: "#2a2d3a",
        accent: "#6366f1",
        "accent-hover": "#818cf8",
        muted: "#6b7280",
        danger: "#ef4444",
        warning: "#f59e0b",
        success: "#22c55e",
      },
    },
  },
  plugins: [],
};

export default config;

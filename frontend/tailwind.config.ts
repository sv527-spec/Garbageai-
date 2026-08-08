import type { Config } from "tailwindcss";

// Sustainability-inspired palette: deep forest greens for primary actions, warm earth tones for
// accents, clean neutrals for surfaces. Chosen to feel calm/trustworthy rather than "corporate green".
const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#f0f9f1", 100: "#dcf0de", 200: "#bbe1c0", 300: "#8fca98",
          400: "#5cab6b", 500: "#3a8a4a", 600: "#2a6e39", 700: "#22572f",
          800: "#1e4627", 900: "#193a21",
        },
        earth: {
          50: "#faf6f0", 100: "#f0e6d6", 200: "#e0cba8", 300: "#cba874",
          400: "#b3894e", 500: "#966d3a", 600: "#78552e", 700: "#5f4327",
          800: "#4f3823", 900: "#432f20",
        },
        surface: { light: "#ffffff", dark: "#0f1512" },
      },
      borderRadius: { xl: "1rem", "2xl": "1.5rem" },
    },
  },
  plugins: [],
};
export default config;

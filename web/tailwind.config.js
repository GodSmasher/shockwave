/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Light editorial palette — cream + ink
        bg: "#faf8f2",         // warm cream (FT-ish)
        panel: "#ffffff",      // crisp white panels
        panelHi: "#f3efe3",    // subtle hover
        subtle: "#ede8d8",
        hairline: "#d6cfbb",   // soft newspaper rules
        ink: "#1a1a1a",        // near-black
        inkDim: "#4a4845",
        muted: "#8c8880",
        // Semantic colors tuned for cream background
        risk: "#b03026",       // deeper red
        warn: "#b8762a",       // ochre
        ok: "#2f7a60",         // deep green
        info: "#2560a8",       // ink blue
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui"],
        display: ["Instrument Serif", "Georgia", "serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 1px 0 rgba(0,0,0,0.03), 0 2px 8px rgba(60,40,10,0.06)",
      },
    },
  },
  plugins: [],
};

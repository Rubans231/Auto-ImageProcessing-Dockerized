/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        basalt: "#14181B",
        panel: "#1C2226",
        "panel-raised": "#232A2E",
        moss: "#7C9473",
        "moss-dim": "#4E5D48",
        rust: "#C1693B",
        "rust-dim": "#5C3A29",
        parchment: "#E8E3D6",
        "slate-fog": "#8B948E",
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        sans: ["IBM Plex Sans", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // ── Hemas Healthcare Brand Palette ────────────────────────────
        // Primary teal family
        "hemas-teal": "#025567",   // primary brand teal
        "hemas-teal-dark": "#08263e",   // deep teal / headings
        "hemas-cyan": "#00687f",   // lighter teal accent

        // Secondary navy / dark family
        "hemas-navy": "#112023",   // dark background layer
        "hemas-dark": "#081c20",   // deepest background

        // Accent orange
        "hemas-orange": "#e75424",   // CTA / primary accent

        // Neutral grays / surfaces
        "hemas-white": "#ffffff",   // white
        "hemas-white-alpha": "#ffffff4d", // 30 % transparent white
        "hemas-gray": "#b8b8b8",   // mid gray
        "hemas-gray-light": "#c7d0d7",   // light blueish gray
        "hemas-gray-mid": "#cccccc",   // light neutral gray
        "hemas-gray-muted": "#b3b8c8",   // muted blue-gray
        "hemas-gray-warm": "#7f8c8f",   // warm mid-tone gray
        "hemas-gray-dark": "#777777",   // dark neutral gray

        // Other
        "hemas-blue": "#007bff",   // hyperlink / info blue
        "hemas-black": "#000000",   // pure black

        // ── Semantic aliases (maps to above) ──────────────────────────
        primary: "#025567",   // hemas-teal
        "primary-dark": "#08263e", // hemas-teal-dark
        accent: "#e75424",   // hemas-orange
        surface: "#112023",   // hemas-navy
        "surface-deep": "#081c20", // hemas-dark
      },
    },
  },
  plugins: [],
};

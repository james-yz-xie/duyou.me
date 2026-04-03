/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        'dark': '#0A0A0A',
        'gold': '#D4AF37',
        'gold-dark': '#AA8B1F',
      },
      fontFamily: {
        'sans': ['system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

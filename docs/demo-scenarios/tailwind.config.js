/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        pagerduty: {
          green: '#06ac38',
          dark: '#1f2937',
        }
      }
    },
  },
  plugins: [],
}
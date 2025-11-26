/** @type {import('tailwindcss').Config} */

export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          'system-ui',
          'Segoe UI',
          'sans-serif',
        ],
      },
      colors: {
        surface: {
          DEFAULT: 'rgba(255,255,255,0.8)',
        },
      },
      boxShadow: {
        soft: '0 18px 45px rgba(15,23,42,0.12)',
      },
      borderRadius: {
        'xl-apple': '1.4rem',
      },
    },
  },
  plugins: [],
}



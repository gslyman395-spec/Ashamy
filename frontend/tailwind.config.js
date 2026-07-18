/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#0ea5e9',
        success: '#22c55e',
        danger: '#ef4444',
        warning: '#f59e0b',
        dark: '#0f172a',
        card: '#1e293b',
      },
    },
  },
  plugins: [],
};

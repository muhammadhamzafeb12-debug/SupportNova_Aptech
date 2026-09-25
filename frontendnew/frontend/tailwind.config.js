/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        app: {
          bg: '#080B12',
          surface: '#101521',
          surface2: '#151B28',
          border: '#202838',
          accent: '#635BFF',
          text: '#F4F6FA',
          muted: '#98A2B3',
        },
        brand: {
          DEFAULT: '#635BFF',
          primary: '#635BFF',
          hover: '#5249E6',
        }
      }
    },
  },
  plugins: [],
}

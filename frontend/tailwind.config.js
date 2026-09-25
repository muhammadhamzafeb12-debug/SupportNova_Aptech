/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#0a0e14',        // Deepest near-black base background
          surface: '#141a24',   // Primary panel/card surface
          surfaceHover: '#1a2230',
          border: '#232b3a',    // 1px subtle panel border
          borderLight: '#2e384d',
        },
        brand: {
          50: '#f0f6ff',
          100: '#e0edff',
          400: '#60a5fa',
          500: '#3b82f6',       // Electric blue
          600: '#2563eb',
          700: '#1d4ed8',
          violet: '#8b5cf6',    // Electric violet
        },
        status: {
          active: '#10b981',    // Emerald
          draft: '#f59e0b',     // Amber
          superseded: '#64748b',// Muted slate
          expired: '#ef4444',   // Red
        }
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
        'brand-gradient-hover': 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
        'glow-radial': 'radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, rgba(10, 14, 20, 0) 70%)',
      },
      boxShadow: {
        'glow-brand': '0 0 20px -3px rgba(59, 130, 246, 0.4)',
        'glow-active': '0 0 14px 0 rgba(16, 185, 129, 0.45)',
        'glow-draft': '0 0 14px 0 rgba(245, 158, 11, 0.45)',
        'glow-expired': '0 0 14px 0 rgba(239, 68, 68, 0.45)',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: '1', transform: 'scale(1)', boxShadow: '0 0 12px rgba(16, 185, 129, 0.5)' },
          '50%': { opacity: '0.85', transform: 'scale(1.02)', boxShadow: '0 0 20px rgba(16, 185, 129, 0.75)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'fade-slide-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      },
      animation: {
        'pulse-glow': 'pulse-glow 2.5s infinite ease-in-out',
        'shimmer': 'shimmer 1.8s infinite linear',
        'fade-slide-up': 'fade-slide-up 0.3s ease-out forwards',
      }
    },
  },
  plugins: [],
}

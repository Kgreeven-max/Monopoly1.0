/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
    '../../packages/ui-components/src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        board: {
          brown: '#8B4513',
          lightBlue: '#87CEEB',
          pink: '#FF69B4',
          orange: '#FFA500',
          red: '#FF0000',
          yellow: '#FFFF00',
          green: '#008000',
          blue: '#0000FF',
          railroad: '#000000',
          utility: '#808080',
        },
        monopoly: {
          go: '#00FF00',
          jail: '#FFA500',
          freeParking: '#FF0000',
          goToJail: '#0000FF',
        },
      },
      fontFamily: {
        display: ['Oswald', 'sans-serif'],
        body: ['Open Sans', 'sans-serif'],
      },
      animation: {
        'bounce-in': 'bounceIn 0.5s ease-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'pulse-slow': 'pulse 3s infinite',
        'dice-roll': 'diceRoll 0.5s ease-out',
      },
      keyframes: {
        bounceIn: {
          '0%': { transform: 'scale(0)', opacity: '0' },
          '50%': { transform: 'scale(1.1)' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        diceRoll: {
          '0%, 100%': { transform: 'rotate(0deg)' },
          '25%': { transform: 'rotate(90deg)' },
          '50%': { transform: 'rotate(180deg)' },
          '75%': { transform: 'rotate(270deg)' },
        },
      },
    },
  },
  plugins: [],
};

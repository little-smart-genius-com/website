/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './*.html',
    './articles/*.html',
    './blog/*.html',
    './authors/*.html',
  ],
  theme: {
    extend: {
      colors: {
        brand: '#F48C06',
      },
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./products/**/*.py",
    "./static/**/*.js"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'sans-serif'],
      },
      colors: {
        themeBrown: '#5C3214',
      }
    },
  },
  plugins: [],
}

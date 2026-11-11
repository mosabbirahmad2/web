/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./products/**/*.py",
    "./static/**/*.js",
    "./src/**/*.css"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'sans-serif'],
      },
      colors: {
        themeBrown: '#5C3214',
        zatiqPurple: '#541DFF',
      }
    },
  },
  plugins: [],
}

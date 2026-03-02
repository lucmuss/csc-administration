module.exports = {
  content: [
    './templates/**/*.html',
    './src/apps/**/*.py'
  ],
  theme: {
    extend: {
      colors: {
        csc: {
          50: '#f3faf6',
          100: '#def3e5',
          500: '#2f8f51',
          700: '#236a3d',
          900: '#193f28'
        }
      }
    }
  },
  plugins: []
}

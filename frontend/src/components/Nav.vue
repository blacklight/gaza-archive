<template>
  <nav>
    <RouterLink to="/">Home</RouterLink>
    <RouterLink to="/accounts">Accounts</RouterLink>
    <a href="#" @click.prevent="toggleTheme">
      Switch Theme
    </a>
  </nav>
</template>

<script>
export default {
  data() {
    return {
      theme: '',
    }
  },

  methods: {
    getTheme() {
      const storedTheme = window.localStorage.getItem('theme')
      if (storedTheme) {
        return storedTheme
      }

      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark'
      }
      return 'light'
    },

    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark'
    },
  },

  watch: {
    theme(newTheme) {
      document.documentElement.setAttribute('data-theme', newTheme)
      window.localStorage.setItem('theme', newTheme)
    }
  },

  mounted() {
    this.theme = this.getTheme()
    document.documentElement.setAttribute('data-theme', this.theme)
  }
}
</script>

<style scoped lang="scss">
@use "@/styles/variables" as *;

nav {
  height: $nav-height;
  display: flex;
  align-items: center;
  gap: 1.5em;
  padding: 1em;
  background-color: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);

  a {
    color: var(--color-link);
    text-decoration: none;
    font-weight: bold;

    &:hover {
      text-decoration: underline;
    }
  }
}
</style>

<template>
  <nav>
    <section class="left">
      <RouterLink to="/" title="Home" :class="{ active: currentView === '/' }">
        <i class="fas fa-home" />
      </RouterLink>

      <RouterLink to="/accounts" title="Accounts"
        :class="{ active: currentView?.startsWith('/accounts') }">
        <i class="fas fa-users" />
      </RouterLink>

      <RouterLink to="/posts" title="Posts"
        :class="{ active: currentView?.startsWith('/posts') }">
        <i class="fas fa-stream" />
      </RouterLink>

      <RouterLink to="/attachments" title="Media"
        :class="{ active: currentView?.startsWith('/attachments') }">
        <i class="fas fa-photo-video" />
      </RouterLink>

      <a href="/media" title="Static media directory"><i class="fas fa-folder" /></a>
      <a href="/swagger" title="API"><i class="fas fa-code" /></a>
    </section>

    <span class="spacer" style="flex-grow: 1;"></span>

    <section class="right">
      <a href="#" @click.prevent="toggleTheme" :title="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'">
        <i :class="theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon'" />
      </a>
    </section>
  </nav>
</template>

<script>
export default {
  props: {
    currentView: {
      type: String,
      default: null,
    },
  },

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
  padding: 1em;
  background-color: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);

  section {
    display: flex;
    align-items: center;
    gap: 1.5em;
  }

  a {
    color: var(--color-link);
    text-decoration: none;
    font-weight: bold;

    &:hover {
      text-decoration: underline;
    }

    &.active {
      color: var(--color-secondary);
    }
  }
}
</style>

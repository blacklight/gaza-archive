<template>
  <div id="app-view">
    <Nav :currentView="currentView" />
    <main @scroll.passive="onScroll" ref="main">
      <RouterView />
      <Footer />
    </main>
  </div>
</template>

<script>
import Footer from './components/Footer.vue'
import Nav from './components/Nav.vue'
import mitter from 'mitt'

export default {
  components: {
    Footer,
    Nav,
  },

  data() {
    return {
      bus: mitter(),
      currentView: null,
      infiniteScrollCallback: null,
      scrollTimeout: null,
    }
  },

  methods: {
    onRouteChange(to) {
      this.currentView = to.path
    },

    onScroll(e) {
      const percent = this.$refs.main.scrollTop / (this.$refs.main.scrollHeight - this.$refs.main.clientHeight)
      this.bus.emit('scroll', [percent, e])

      if (percent > 0.8) {
        this.onPageBottom(e)
      }
    },

    onPageBottom(e) {
      if (this.scrollTimeout || !this.infiniteScrollCallback) {
        return
      }

      this.scrollTimeout = setTimeout(async () => {
        // Store the current scroll position
        const scrollPosition = e.target.scrollTop

        try {
          await this.infiniteScrollCallback()
          // Restore the scroll position
        } finally {
          e.target.scrollTop = scrollPosition
        }
      }, 250)

      setTimeout(() => {
        clearTimeout(this.scrollTimeout)
        this.scrollTimeout = null
      }, 500)
    },

    registerInfiniteScrollCallback(callback) {
      this.infiniteScrollCallback = callback
    },

    unregisterInfiniteScrollCallback() {
      this.infiniteScrollCallback = null
    },
  },

  mounted() {
    this.currentView = this.$route.path
    this.$router.afterEach(this.onRouteChange)
  },
}
</script>

<style lang="scss">
@use "@/styles/variables" as *;

#app-view {
  display: flex;
  flex-direction: column;
  height: 100vh;

  main {
    max-height: calc(100vh - $nav-height);
    display: flex;
    flex-direction: column;
    overflow: auto;
    flex: 1;
  }
}
</style>

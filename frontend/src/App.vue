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
    }
  },

  methods: {
    onRouteChange(to) {
      this.currentView = to.path
    },

    onScroll() {
      this.bus.emit(
        'scroll',
        this.$refs.main.scrollTop / (this.$refs.main.scrollHeight - this.$refs.main.clientHeight)
      )
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

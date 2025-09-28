<template>
  <div id="app-view">
    <Nav />
    <main>
      <RouterView />
      <Footer />
    </main>
  </div>
</template>

<script>
import Footer from './components/Footer.vue'
import Nav from './components/Nav.vue'

export default {
  components: {
    Footer,
    Nav,
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

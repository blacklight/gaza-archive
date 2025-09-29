<template>
  <div class="post">
    <p class="content" v-html="post.content"></p>
    <p class="date">{{ new Date(post.created_at).toLocaleString() }}</p>
  </div>
</template>

<script>
export default {
  props: {
    post: {
      type: Object,
      required: true,
    },
  },
}
</script>

<style scoped lang="scss">
</style>

<template>
  <div class="posts view">
    <div class="posts-list-container">
      <PostsList />
    </div>
  </div>
</template>

<script>
import PostsApi from '@/mixins/api/Posts.vue'
import PostsList from '@/views/posts/PostsList.vue'

export default {
  mixins: [PostsApi],
  components: {
    PostsList,
  },
}
</script>

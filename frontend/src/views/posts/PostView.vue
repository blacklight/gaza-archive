<template>
  <Loader v-if="loading" />
  <Post v-else-if="post" :post="post" />
  <div v-else class="error">
    <p>Post not found.</p>
  </div>
</template>

<script>
import Loader from "@/elements/Loader.vue"
import Post from "./Post.vue"
import PostsApi from "@/mixins/api/Posts.vue"

export default {
  mixins: [PostsApi],
  components: {
    Loader,
    Post,
  },

  data() {
    return {
      loading: true,
      post: null,
    }
  },

  methods: {
    async refresh() {
      try {
        this.post = await this.getPost(this.$route.params.id)
      } finally {
        this.loading = false
      }
    }
  },

  async mounted() {
    await this.refresh()
  },
}
</script>

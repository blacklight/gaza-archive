<template>
  <Loader v-if="loading" />
  <div class="posts" v-else>
    <div class="filters">
      <input type="checkbox" id="exclude-replies" v-model="excludeReplies" @change="refresh" />
      <label for="exclude-replies">Exclude replies</label>
    </div>
    <PostView v-for="post in posts" :key="post.id" :post="post" />
  </div>
</template>

<script>
import Loader from '@/elements/Loader.vue'
import PostView from '@/views/posts/Post.vue'
import PostsApi from '@/mixins/api/Posts.vue'

export default {
  mixins: [PostsApi],
  components: {
    Loader,
    PostView,
  },

  props: {
    filter: {
      type: Object,
      default: () => ({}),
    },
  },

  computed: {
    computedFilter() {
      return {
        ...this.filter,
        exclude_replies: this.excludeReplies,
      }
    },
  },

  data() {
    return {
      account: null,
      excludeReplies: false,
      loading: true,
      posts: [],
    }
  },

  methods: {
    async refresh() {
      this.posts = await this.getPosts(this.computedFilter)
    }
  },

  async mounted() {
    try {
      await this.refresh()
    } finally {
      this.loading = false
    }
  },
}
</script>

<style scoped lang="scss">
.posts {
  .filters {
    margin: 1em 0;
    font-size: 0.9em;
    color: var(--color-text-muted);

    input {
      margin-right: 0.5em;
    }
  }
}
</style>

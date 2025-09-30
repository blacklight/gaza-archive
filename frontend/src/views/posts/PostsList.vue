<template>
  <div class="posts">
    <Loader v-if="loading" />
    <div class="filters">
      <input type="checkbox" id="exclude-replies" v-model="excludeReplies" />
      <label for="exclude-replies">Exclude replies</label>
    </div>

    <RouterLink class="post-link"
                v-for="post in posts"
                :to="`/posts/${post.id}`"
                :key="post.id">
      <Post :key="post.id" :post="post" />
    </RouterLink>
  </div>
</template>

<script>
import Loader from '@/elements/Loader.vue'
import Post from '@/views/posts/Post.vue'
import PostsApi from '@/mixins/api/Posts.vue'

export default {
  mixins: [PostsApi],
  components: {
    Loader,
    Post,
  },

  props: {
    filter: {
      type: Object,
      default: () => ({}),
    },
  },

  data() {
    return {
      account: null,
      excludeReplies: false,
      loading: true,
      hasMore: true,
      maxId: null,
      minId: null,
      posts: [],
    }
  },

  computed: {
    computedFilter() {
      return {
        ...this.filter,
        exclude_replies: this.excludeReplies,
      }
    },
  },

  methods: {
    async onBottomScroll() {
      if (this.hasMore && !this.loading) {
        this.loading = true
        try {
          const newPosts = await this.getPosts({
            ...this.computedFilter,
            max_id: this.minId,
          })

          if (newPosts.length > 0) {
            this.posts = [...this.posts, ...newPosts]
            this.minId = newPosts[newPosts.length - 1].id
          } else {
            this.hasMore = false
          }
        } finally {
          this.loading = false
          clearTimeout(this.scrollTimeout)
        }
      }
    },

    async refresh() {
      this.posts = await this.getPosts(this.computedFilter)
    }
  },

  watch: {
    excludeReplies(newVal) {
      this.maxId = null
      this.minId = null
      this.hasMore = true
      this.$router.replace({
        query: {
          ...this.$route.query,
          exclude_replies: newVal ? '1' : '0'
        }
      })

      this.refresh()
    },
  },

  async mounted() {
    this.excludeReplies = this.$route.query.exclude_replies === '1'
    this.$root.registerInfiniteScrollCallback(this.onBottomScroll)

    try {
      await this.refresh()
    } finally {
      this.loading = false
    }
  },

  unmounted() {
    this.$root.unregisterInfiniteScrollCallback()
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

  .post-link {
    text-decoration: none;
    color: inherit;
  }
}
</style>

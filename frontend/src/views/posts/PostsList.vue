<template>
  <div class="posts">
    <Loader v-if="loading" />
    <div class="filters">
      <input type="text" v-model="textFilter" placeholder="Filter posts" />
      <div class="exclude-replies">
        <input type="checkbox" id="exclude-replies" v-model="excludeReplies" />
        <label for="exclude-replies">Exclude replies</label>
      </div>
    </div>

    <RouterLink class="post-link"
                v-for="post in filteredPosts"
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
      textFilter: '',
    }
  },

  computed: {
    computedFilter() {
      return {
        ...this.filter,
        exclude_replies: this.excludeReplies,
      }
    },

    filteredPosts() {
      const filter = this.textFilter?.length ? this.textFilter.toLowerCase().trim() : null
      if (!filter) {
        return this.posts
      }

      return this.posts.filter((post, index) =>
        this.indexedContent[index]?.includes(filter) ||
        post.author?.display_name?.toLowerCase()?.includes(filter) ||
        post.author?.fqn?.includes(filter)
      )
    },

    indexedContent() {
      return this.posts.map(post => {
        const p = document.createElement('p')
        p.innerHTML = post.content || ''
        return p.textContent?.toLowerCase() || ''
      })
    },

    postsById() {
      return this.posts.reduce((map, post) => {
        map[post.id] = post
        return map
      }, {})
    },
  },

  methods: {
    async onBottomScroll() {
      if (this.hasMore && !this.loading) {
        this.loading = true
        try {
          const newPosts = (
            await this.getPosts({
              ...this.computedFilter,
              max_id: this.minId,
            })
          ).filter(post => !this.postsById[post.id])

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
      this.minId = this.posts.length > 0 ? this.posts[this.posts.length - 1].id : null
      this.maxId = this.posts.length > 0 ? this.posts[0].id : null
      this.hasMore = true
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
    if (!this.excludeReplies && this.$route.query.exclude_replies === '0') {
      const query = { ...this.$route.query }
      delete query.exclude_replies
      this.$router.replace({ query })
    }

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
@use '@/styles/index' as *;

.posts {
  margin: 0 auto;

  @include from($tablet) {
    max-width: $tablet;
  }

  @include until($tablet) {
    max-width: 90%;
  }

  .filters {
    width: 100%;
    display: flex;
    align-items: center;
    margin: 1em 0;
    font-size: 0.9em;
    color: var(--color-text-muted);

    .exclude-replies {
      display: flex;
      align-items: center;
    }

    input {
      margin-right: 0.5em;
    }

    input[type="text"] {
      width: 100%;
      flex: 1;
    }
  }

  .post-link {
    text-decoration: none;
    color: inherit;
  }
}
</style>

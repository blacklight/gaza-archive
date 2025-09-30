<template>
  <div class="attachments">
    <Loader v-if="loading" />
    <div class="no-attachments" v-if="!loading && attachments.length === 0">
      No attachments found.
    </div>

    <div class="list" v-else-if="attachments.length > 0">
      <RouterLink class="attachment-link"
                  v-for="attachment in attachments"
                  :to="attachment.path"
                  :key="attachment.url">
        <Attachment preview :key="attachment.url" :attachment="attachment" />
      </RouterLink>
    </div>
  </div>
</template>

<script>
import Loader from '@/elements/Loader.vue'
import Attachment from '@/views/attachments/Attachment.vue'
import AttachmentsApi from '@/mixins/api/Attachments.vue'

export default {
  mixins: [AttachmentsApi],
  components: {
    Loader,
    Attachment,
  },

  props: {
    filter: {
      type: Object,
      default: () => ({}),
    },
  },

  data() {
    return {
      loading: true,
      hasMore: true,
      maxId: null,
      minId: null,
      attachments: [],
      scrollTimeout: null,
    }
  },

  computed: {
    computedFilter() {
      return {
        ...this.filter,
      }
    },
  },

  methods: {
    async onScroll(percentage) {
      if (this.scrollTimeout) {
        return
      }

      setTimeout(async () => {
        if (percentage > 0.8 && this.hasMore && !this.loading) {
          this.loading = true
          try {
            const newAttachments = await this.getAttachments({
              ...this.computedFilter,
              max_id: this.minId,
            })

            if (newAttachments.length > 0) {
              this.attachments = [...this.attachments, ...newAttachments]
              this.minId = newAttachments[newAttachments.length - 1].id
            } else {
              this.hasMore = false
            }
          } finally {
            this.loading = false
            clearTimeout(this.scrollTimeout)
          }
        }
      }, 100)
    },

    async refresh() {
      this.attachments = await this.getAttachments(this.computedFilter)
    }
  },

  watch: {
    excludeReplies() {
      this.maxId = null
      this.minId = null
      this.hasMore = true
      this.refresh()
    },
  },

  async mounted() {
    this.$root.bus.on('scroll', this.onScroll)
    try {
      await this.refresh()
    } finally {
      this.loading = false
    }
  },
}
</script>

<style scoped lang="scss">
.attachments {
  .filters {
    margin: 1em 0;
    font-size: 0.9em;
    color: var(--color-text-muted);

    input {
      margin-right: 0.5em;
    }
  }

  .list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 1em;
  }

  .attachment-link {
    text-decoration: none;
    color: inherit;
  }
}
</style>

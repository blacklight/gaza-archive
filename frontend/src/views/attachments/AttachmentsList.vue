<template>
  <div class="attachments">
    <Loader v-if="loading" />
    <div class="no-attachments" v-if="!loading && attachments.length === 0">
      No attachments found.
    </div>

    <div class="list" ref="list" v-else-if="attachments.length > 0">
      <RouterLink class="attachment-link"
                  v-for="attachment in attachments"
                  :to="attachment.path"
                  :key="attachment.url">
        <Attachment preview
                    @update:mediaDescriptionId="mediaDescriptionId = $event"
                    :key="attachment.url"
                    :show-author="showAuthors"
                    :attachment="attachment" />
      </RouterLink>
    </div>
  </div>

  <Modal v-if="mediaDescriptionId"
         :show="!!mediaDescriptionId"
         title="Media Description"
         @close="mediaDescriptionId = null">
    <div class="media-description" v-if="mediaDescriptionId">
      <p>{{ attachmentsById[mediaDescriptionId]?.description }}</p>
    </div>
  </Modal>
</template>

<script>
import Attachment from '@/views/attachments/Attachment.vue'
import AttachmentsApi from '@/mixins/api/Attachments.vue'
import Loader from '@/elements/Loader.vue'
import Modal from '@/elements/Modal.vue'

export default {
  mixins: [AttachmentsApi],
  components: {
    Attachment,
    Loader,
    Modal,
  },

  props: {
    filter: {
      type: Object,
      default: () => ({}),
    },

    showAuthors: {
      type: Boolean,
      default: false,
    },
  },

  data() {
    return {
      loading: true,
      hasMore: true,
      maxId: null,
      minId: null,
      attachments: [],
      mediaDescriptionId: null,
    }
  },

  computed: {
    attachmentsById() {
      return this.attachments.reduce((map, attachment) => {
        map[attachment.id] = attachment
        return map
      }, {})
    },

    computedFilter() {
      return {
        ...this.filter,
      }
    },
  },

  methods: {
    async onBottomScroll() {
      if (this.hasMore && !this.loading) {
        this.loading = true

        try {
          const newAttachments = (
            await this.getAttachments({
              ...this.computedFilter,
              max_id: this.minId,
            })
          ).filter(
            (attachment) => !this.attachmentsById[attachment.id]
          )

          if (newAttachments.length > 0) {
            this.attachments = [...this.attachments, ...newAttachments]
            this.minId = newAttachments[newAttachments.length - 1].id
          } else {
            this.hasMore = false
          }
        } finally {
          this.loading = false
        }
      }
    },

    async refresh() {
      this.attachments = await this.getAttachments(this.computedFilter)
      this.minId = this.attachments.length > 0 ? this.attachments[this.attachments.length - 1].id : null
      this.maxId = this.attachments.length > 0 ? this.attachments[0].id : null
      this.hasMore = true
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
    grid-template-columns: repeat(auto-fill, minmax(175px, 2fr));
    gap: 1em;
  }

  .attachment-link {
    height: 100%;
    text-decoration: none;
    color: inherit;
  }

  .media-description {
    p {
      white-space: pre-wrap;
    }
  }
}
</style>

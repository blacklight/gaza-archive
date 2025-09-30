<template>
  <div class="attachment" :class="{ preview }">
    <div class="actions" @click.stop v-if="postUrl">
      <RouterLink :to="postUrl">
        <i class="fas fa-link" title="View Post" aria-hidden="true" />
      </RouterLink>
      <a :href="attachment.path" target="_blank" rel="noopener noreferrer">
        <i class="fas fa-download" title="Download" aria-hidden="true" />
      </a>
      <button @click.prevent.stop="$emit('update:mediaDescriptionId', attachment.id)"
              title="View Description"
              v-if="attachment.description?.length">
        <i class="fas fa-info-circle" title="View Description" aria-hidden="true" />
      </button>
    </div>

    <div class="author" v-if="showAuthor && attachment.post?.author">
      <a :href="`/accounts/${attachment.post.author.fqn}`"
         @click.stop
         class="author-link"
         target="_blank"
         rel="noopener noreferrer">
        <img class="avatar"
             :src="attachment.post.author.avatar_path || attachment.post.author.avatar_url"
             :alt="attachment.post.author.display_name || attachment.post.author.username"
             :title="attachment.post.author.display_name || attachment.post.author.username" />
      </a>
    </div>

    <a :href="mediaTarget"
       class="media-link"
       target="_blank"
       rel="noopener noreferrer"
       ref="link"
       @click.stop>
      <img :src="mediaTarget"
           :alt="attachment.description"
           :title="attachment.description || 'Attachment'"
           @load="onMediaLoad"
           @error="onMediaError"
           v-if="attachment.type === 'image' && !errorMessage?.length" />
      <video controls
             :key="videoKey"
             v-else-if="attachment.type === 'video' && !errorMessage?.length">
        <source :src="mediaTarget"
                @load="onMediaLoad"
                @error="onMediaError"
                :type="`video/${extension}`" />
        Your browser does not support the video tag.
      </video>
      <span class="error" ref="error" v-else>
        {{ errorMessage?.length ? errorMessage : 'Unsupported attachment type' }}
      </span>
    </a>

    <div class="footer" v-if="attachment.post">
      <i class="fas fa-clock" aria-hidden="true" />
      <span>{{ formatDateTime(attachment.post.created_at) }}</span>
    </div>
  </div>
</template>

<script>
import Dates from '@/mixins/Dates.vue'

export default {
  mixins: [Dates],
  emits: ['update:mediaDescriptionId'],
  props: {
    attachment: {
      type: Object,
      required: true,
    },

    preview: {
      type: Boolean,
      default: false,
    },

    showAuthor: {
      type: Boolean,
      default: false,
    },
  },

  data() {
    return {
      errorMessage: '',
      mediaTarget: this.attachment.path?.replace("@", "%40") || this.attachment.url,
      videoKey: 0,
    };
  },

  computed: {
    extension() {
      return this.mediaTarget?.split('.')?.pop()?.toLowerCase();
    },

    postUrl() {
      // Don't show link if already on a post page
      if (this.$route.path.indexOf('/posts/') >= 0) {
        return null;
      }

      if (!this.attachment.post?.id) {
        return null;
      }

      return `/posts/${this.attachment.post.id}`;
    },
  },

  methods: {
    onMediaLoad() {
      this.errorMessage = '';
    },

    onMediaError(event) {
      // Fallback to URL
      if (event.target.src !== this.attachment.url) {
        this.mediaTarget = this.attachment.url;

        // For video elements, we need to force a re-render
        if (this.attachment.type === 'video') {
          this.videoKey++; // Increment key to force re-render
        }
      } else {
        this.errorMessage = 'Failed to load media';
      }
    },
  },
}
</script>

<style scoped lang="scss">
@use '@/styles/animations' as *;

$actions-height: 2em;

.attachment {
  background: var(--color-media-bg);
  margin: 0.5em 0;
  text-align: center;
  position: relative;

  img, video {
    max-width: 100%;
    border-radius: 8px;
  }

  &.preview {
    height: 100%;
    display: flex;
    flex-direction: column;
    border-radius: 1em;

    &:hover {
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      @extend .lighten;
    }

    img, video {
      object-fit: fill;
      max-height: 350px;
    }

    .actions {
      height: $actions-height;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.8em;
      padding: 1em;
      gap: 3em;

      button, a, .router-link {
        background: none;
        border: none;
        color: var(--color-text-secondary);
        cursor: pointer;
        text-decoration: none;
        transition: color 0.3s;

        &:hover {
          color: var(--color-accent);
        }

        i {
          font-size: 1.2em;
        }
      }
    }

    .author {
      position: absolute;
      top: $actions-height + 0.5em;

      img.avatar {
        width: 2em;
        height: 2em;
        border-radius: 50%;
        object-fit: cover;
      }
    }

    .media-link {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .footer {
      font-size: 0.8em;
      color: var(--color-text-muted);
      margin-top: auto;
      padding: 0.5em;
      border-top: 1px solid var(--color-border);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5em;
    }
  }
}
</style>

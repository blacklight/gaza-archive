<template>
  <div class="attachment" :class="{ preview }">
    <div class="actions" @click.stop v-if="postUrl">
      <RouterLink :to="postUrl">
        <i class="fas fa-file-alt" title="View Post" aria-hidden="true" />
      </RouterLink>
      <a :href="attachment.path" target="_blank" rel="noopener noreferrer">
        <i class="fas fa-download" title="Download" aria-hidden="true" />
      </a>
    </div>

    <a :href="mediaTarget"
       target="_blank"
       rel="noopener noreferrer"
       ref="link"
       @click.stop>
      <img :src="mediaTarget"
           :alt="attachment.description"
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
  props: {
    attachment: {
      type: Object,
      required: true,
    },

    preview: {
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

.attachment {
  background: var(--color-media-bg);
  margin: 0.5em 0;
  text-align: center;

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
      object-fit: contain;
      max-height: 350px;
    }

    .actions {
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.8em;
      padding: 1em;
      gap: 3em;
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

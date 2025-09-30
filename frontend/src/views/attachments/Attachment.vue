<template>
  <div class="attachment" :class="{ preview }">
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
  </div>
</template>

<script>
export default {
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
.attachment {
  margin: 0.5em 0;
  text-align: center;

  img, video {
    max-width: 100%;
    border-radius: 8px;
  }

  &.preview {
    img, video {
      object-fit: contain;
      max-height: 350px;
    }
  }
}
</style>

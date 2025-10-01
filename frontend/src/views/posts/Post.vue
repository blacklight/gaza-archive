<template>
  <div class="post">
    <div class="icons" @click.stop>
      <i class="fas fa-reply-all reply-icon"
         v-if="post.in_reply_to_id"
         title="This post is a reply" />

      <a :href="post.url" target="_blank" rel="noopener" title="View this post on its original site">
        <i class="fas fa-external-link-alt external-link-icon" />
      </a>
    </div>

    <RouterLink :to="`/accounts/${post.author.fqn}`" class="author">
      <div class="avatar">
        <img :src="post.author.avatar_path"
             :alt="post.author.display_name || post.author.username"
             ref="avatar"
             @error="$refs.avatar.src = post.author.avatar_url" />
      </div>
      <div class="name">
        <strong>{{ post.author.display_name || post.author.username }}</strong>
        <span class="username">{{ post.author.fqn }}</span>
      </div>
    </RouterLink>
    <p class="content" @click.stop="onContentClick" v-html="post.content"></p>
    <p class="date">{{ formatDateTime(post.created_at) }}</p>

    <div class="attachments" v-if="post.attachments?.length">
      <Attachment v-for="attachment in post.attachments"
                  :key="attachment.url"
                  preview
                  :attachment="attachment" />
    </div>
  </div>
</template>

<script>
import Attachment from '@/views/attachments/Attachment.vue'
import Dates from '@/mixins/Dates.vue'

export default {
  mixins: [Dates],
  components: { Attachment },
  props: {
    post: {
      type: Object,
      required: true,
    },
  },

  methods: {
    onContentClick(event) {
      const target = event.target
      if (target.tagName === 'A' && target.href) {
        window.open(target.href, '_blank', 'noopener')
        event.preventDefault()
      }
    },
  },
}
</script>

<style scoped lang="scss">
.post {
  max-width: 800px;
  border: 1px solid var(--color-border);
  padding: 1em;
  margin: 0.5em auto;
  border-radius: 8px;
  background-color: var(--color-bg-secondary);

  .icons {
    display: flex;
    align-items: center;
    color: var(--color-text-secondary);
    margin: 0.25em;
    font-size: 0.9em;
    vertical-align: middle;
    float: right;
    gap: 0.5em;
  }

  .author {
    display: flex;
    align-items: center;
    margin-bottom: 0.5em;

    .avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      overflow: hidden;
      margin-right: 0.5em;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }

    .name {
      font-size: 1em;
      display: flex;
      flex-direction: column;
      justify-content: center;
      margin-left: 0.3em;

      .username {
        color: var(--color-text-secondary);
        font-size: 0.9em;
      }
    }
  }

  a.author {
    color: var(--color-text-primary);
  }

  .content {
    font-size: 1em;
    margin-bottom: 0.5em;
    overflow-wrap: break-word;
  }

  .date {
    font-size: 0.8em;
    color: var(--color-text-secondary);
  }

  .attachments {
    display: flex;
    flex-wrap: wrap;
    gap: 1em;
    margin-top: 0.5em;
  }
}
</style>

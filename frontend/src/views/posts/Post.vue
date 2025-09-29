<template>
  <div class="post">
    <a :href="`/accounts/${post.author.fqn}`" class="author">
      <div class="avatar">
        <img :src="post.author.avatar_url" :alt="post.author.display_name || post.author.username" />
      </div>
      <div class="name">
        <strong>{{ post.author.display_name || post.author.username }}</strong>
        <span class="username">{{ post.author.fqn }}</span>
      </div>
    </a>
    <p class="content" v-html="post.content"></p>
    <p class="date">{{ new Date(post.created_at).toLocaleString() }}</p>
  </div>
</template>

<script>
export default {
  props: {
    post: {
      type: Object,
      required: true,
    },
  },
}
</script>

<style scoped lang="scss">
.post {
  border: 1px solid #ccc;
  padding: 1em;
  margin-bottom: 1em;
  border-radius: 8px;
  background-color: var(--color-bg-secondary);

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
    color: #333;
  }

  .date {
    font-size: 0.8em;
    color: var(--color-text-secondary);
    text-align: right;
  }
}
</style>

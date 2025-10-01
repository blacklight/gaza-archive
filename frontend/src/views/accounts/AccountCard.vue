<template>
  <RouterLink :to="`/accounts/${account.fqn}`" class="account">
    <div class="avatar">
      <img :src="account.avatar_path"
           :alt="account.name"
           ref="avatar"
           @error="$refs.avatar.src = account.avatar_url"
           width="100%" height="100%" />
    </div>
    <div class="details">
      <h3>{{ account.display_name }}</h3>
      <p class="fqn">{{ account.fqn }}</p>
    </div>
  </RouterLink>
</template>

<script>
export default {
  props: {
    account: {
      type: Object,
      required: true
    },
  },
}
</script>

<style scoped lang="scss">
.account {
  width: 100%;
  display: flex;
  align-items: center;
  flex-direction: column;
  color: var(--color-text-secondary);
  margin: 0.5em 0;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background-color: var(--color-bg-secondary);

  .avatar {
    width: 100%;
    background: black;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }

  .details {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0.5em 1em 1em 1em;

    h3 {
      margin: 0;
      font-size: 1.2em;
      color: var(--color-text-primary);
    }

    .fqn {
      margin: 0;
      font-size: 0.9em;
      font-weight: 200;
      color: var(--color-text-secondary);
      word-break: break-all;
    }
  }
}
</style>

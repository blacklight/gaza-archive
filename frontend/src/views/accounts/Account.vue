<template>
  <div class="account">
    <li>
      {{ account.fqn }}
    </li>
  </div>
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
  margin: 0.5em 0;

  li {
    list-style: none;
    padding: 0.5em;
    border: 1px solid var(--color-border);
    border-radius: 4px;
    background-color: var(--color-bg-secondary);
  }
}
</style>

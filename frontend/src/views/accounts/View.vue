<template>
  <div class="accounts-view">
    <h2>Accounts</h2>
    <ul>
      <Account v-for="account in shuffledAccounts" :key="account.fqn" :account="account" />
    </ul>
  </div>
</template>

<script>
import Account from './Account.vue'

export default {
  components: {
    Account,
  },

  props: {
    accounts: {
      type: Array,
      required: true
    },
  },

  computed: {
    shuffledAccounts() {
      return this.accounts.sort(() => Math.random() - 0.5)
    },
  },
}
</script>

<style scoped lang="scss">
</style>

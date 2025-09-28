<template>
  <div class="accounts view">
    <h2>
      <b>{{ accounts.length }}</b>&nbsp;
      <a href="https://gaza-verified.org" target="_blank" rel="noopener">verified accounts</a>
    </h2>
    <Loader v-if="loading" />
    <div class="accounts-list" v-else>
      <AccountCard v-for="account in accounts" :key="account.fqn" :account="account" />
    </div>
  </div>
</template>

<script>
import AccountCard from './AccountCard.vue'
import AccountsApi from '@/mixins/api/Accounts.vue'
import Loader from '@/elements/Loader.vue'

export default {
  mixins: [AccountsApi],
  components: {
    AccountCard,
    Loader,
  },

  data() {
    return {
      accounts: [],
      loading: true,
    }
  },

  methods: {
    async refresh() {
      const accounts = await this.getAccounts()
      // Shuffle accounts
      this.accounts = accounts.sort(() => Math.random() - 0.5)
    }
  },

  async mounted() {
    try {
      await this.refresh()
    } finally {
      this.loading = false
    }
  },
}
</script>

<style scoped lang="scss">
.accounts.view {
  padding: 0 1em;

  h2 {
    font-weight: normal;
    text-align: center;
    margin-bottom: 0.5em;
  }

  .accounts-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1em;
  }
}
</style>

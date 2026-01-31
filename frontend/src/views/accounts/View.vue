<template>
  <div class="accounts view">
    <Loader v-if="loading" />
    <div class="accounts-list-container" v-else>
      <h2>
        <b v-if="filter?.trim()?.length">{{ filteredAccounts.length }} / </b>
        <b>{{ accounts.length }}</b>&nbsp;
        <a href="https://gaza-verified.org" target="_blank" rel="noopener">verified accounts</a>
      </h2>

      <div class="filter">
        <input id="filter-input" type="text" v-model="filter" placeholder="Type to filter accounts..." />
      </div>

      <div class="accounts-list">
        <AccountCard v-for="account in filteredAccounts" :key="account.fqn" :account="account" />
      </div>
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
      filter: '',
      loading: true,
    }
  },

  computed: {
    filteredAccounts() {
      const filter = this.filter?.toLowerCase()?.trim()
      if (!filter?.length) {
        return this.accounts
      }

      return this.accounts.filter(account =>
        (account.display_name || '').toLowerCase().includes(filter) ||
        account.fqn.toLowerCase().includes(filter) ||
        account.url.toLowerCase().includes(filter)
      )
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

  .filter {
    text-align: center;
    margin-bottom: 1em;
  }

  .accounts-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1em;
  }
}
</style>

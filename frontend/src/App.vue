<template>
  <div class="main">
    <AccountsView :accounts="accounts" />
    <Loader v-if="loading" />
  </div>
</template>

<script>
import AccountsApi from './mixins/api/Accounts.vue'
import AccountsView from './views/accounts/View.vue'
import Loader from './elements/Loader.vue'

export default {
  mixins: [AccountsApi],
  components: {
    AccountsView,
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
      this.accounts = await this.getAccounts()
    }
  },

  async mounted() {
    try {
      await this.refresh()
    } finally {
      this.loading = false
    }
  }
}
</script>

<style scoped lang="scss">
.main {
  font-family: var(--font-family);
}
</style>

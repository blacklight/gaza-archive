<template>
  <div class="accounts view">
    <Loader v-if="loading" />
    <div class="accounts-list-container" v-else>
      <h2>
        <b v-if="filter?.trim()?.length">{{ filteredAccounts.length }} / </b>
        <b>{{ totalCount }}</b>&nbsp;
        <a href="https://gaza-verified.org/people" target="_blank" rel="noopener">verified accounts</a>
      </h2>

      <h3 v-if="inactiveCount !== null" class="inactive-count">{{ inactiveCount }} inactive</h3>

      <div class="filter">
        <input id="filter-input" type="text" v-model="filter" placeholder="Type to filter accounts..." />
      </div>

      <div class="hide-inactive">
        <label>
          <input type="checkbox" :checked="hideInactive" @change="onHideInactiveChange" />
          Hide inactive
        </label>
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

const HIDE_INACTIVE_KEY = 'gaza-archive:accounts:hide-inactive'

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
      hideInactive: true,
      totalCount: 0,
      inactiveCount: 0,
    }
  },

  computed: {
    filteredAccounts() {
      let accounts = this.accounts

      if (this.hideInactive) {
        accounts = accounts.filter(account => !['DELETED', 'SUSPENDED'].includes(account?.state))
      }

      const filter = this.filter?.toLowerCase()?.trim()
      if (!filter?.length) {
        return accounts
      }

      return accounts.filter(account =>
        (account?.display_name || '').toLowerCase().includes(filter) ||
        (account?.fqn || '').toLowerCase().includes(filter) ||
        (account?.url || '').toLowerCase().includes(filter)
      )
    }
  },

  methods: {
    async refresh() {
      const params = { hide_inactive: this.hideInactive }
      let accounts, total = null, inactive = null

      try {
        const result = await this.getAccounts(params)
        accounts = result.accounts
        total = result.total
        inactive = result.inactive
      } catch (e) {
        console.error('Failed to fetch accounts:', e)
        return
      }

      // Fallback if headers were stripped
      if (total === null || inactive === null) {
        try {
          const stats = await this.getAccountsStats()
          if (stats.total !== undefined) {
            total = stats.total
          }
          if (stats.inactive !== undefined) {
            inactive = stats.inactive
          }
        } catch (e) {
          console.warn('Failed to fetch account stats:', e)
        }
      }

      // Last-resort client-side count: fetch an unfiltered list so hidden
      // inactive accounts can still be counted.
      if (inactive === null || total === null) {
        let countAccounts = accounts
        if (this.hideInactive) {
          try {
            countAccounts = (await this.getAccounts({ hide_inactive: false })).accounts
          } catch (e) {
            console.warn('Failed to fetch unfiltered accounts for counts:', e)
          }
        }
        if (inactive === null) {
          inactive = countAccounts.filter(account => ['DELETED', 'SUSPENDED'].includes(account?.state)).length
        }
        if (total === null) {
          total = countAccounts.length
        }
      }

      this.totalCount = total
      this.inactiveCount = inactive
      // Shuffle accounts
      this.accounts = accounts.sort(() => Math.random() - 0.5)
    },

    persistAndRefresh() {
      localStorage.setItem(HIDE_INACTIVE_KEY, this.hideInactive ? 'true' : 'false')
      this.refresh()
    },

    onHideInactiveChange(event) {
      this.hideInactive = event.target.checked
      this.persistAndRefresh()
    }
  },

  async mounted() {
    const saved = localStorage.getItem(HIDE_INACTIVE_KEY)
    if (saved !== null) {
      this.hideInactive = saved === 'true'
    }
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

  h2, h3 {
    font-weight: normal;
    text-align: center;
    margin-bottom: 0.5em;
  }

  .inactive-count {
    margin-top: -0.5em;
    opacity: 0.5;
  }

  .filter {
    text-align: center;
    margin-bottom: 1em;
  }

  .hide-inactive {
    text-align: center;
    margin-bottom: 1em;

    label {
      cursor: pointer;
      user-select: none;

      input {
        margin-right: 0.5em;
      }
    }
  }

  .accounts-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1em;
  }
}
</style>

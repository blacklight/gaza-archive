<template>
  <div class="accounts-list">
    <div class="header">
      <div class="filter-container">
        <input
          type="text"
          v-model="filterAccountsText"
          placeholder="Filter accounts..."
          class="filter-input"
        />

        <div class="sort-container">
          <button @click="sortModalVisible = true" title="Sort Accounts" class="sort-button">
            <i class="fas fa-sort" aria-hidden="true"></i>
            Sort
          </button>
        </div>
      </div>

      <div class="filter-container" v-if="!hideDonors">
        <input
          type="text"
          v-model="filterDonorsText"
          placeholder="Filter by donors..."
          class="filter-input"
        />
      </div>
    </div>

    <div class="account" v-for="data in filteredAccounts" :key="data.account.fqn">
      <RouterLink :to="`/campaigns/accounts/${data.account.fqn}?${accountsQueryString}`"
                  class="account-link">
        <div class="account-avatar">
          <img :src="data.account.avatar_path" :alt="`${data.account.display_name}'s avatar`" />
        </div>
        <div class="account-info">
          <div class="account-display-name">{{ data.account.display_name }}</div>
          <div class="account-username">{{ data.account.fqn }}</div>
        </div>
        <div class="amount">
          {{ data.amount.string }}
        </div>
      </RouterLink>
    </div>

    <div class="sort-modal-container" v-if="sortModalVisible">
      <Modal :show="sortModalVisible"
             title="Sort Accounts"
             @close="sortModalVisible = false">
        <Sorter :sort="accountsQuery.sort || []"
                :fields="sortFields"
                @update:sort="onSortChange" />
      </Modal>
    </div>
  </div>
</template>

<script>
import CampaignsApi from '@/mixins/api/Campaigns.vue'
import Modal from '@/elements/Modal.vue'
import Sorter from './Sorter.vue'

export default {
  mixins: [
    CampaignsApi,
  ],

  emits: ['update:query', 'update:query:donors'],

  components: {
    Modal,
    Sorter,
  },

  props: {
    accounts: {
      type: Array,
      required: true,
    },

    fields: {
      type: Object,
      required: false,
      default: () => ({}),
    },

    query: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      accountsQuery: {},
      sortFields: {
        'account.created_at': 'datetime',
        'account.display_name': 'varchar',
        'account.fqn': 'varchar',
        'account.url': 'varchar',
        'amount': 'float',
        'first_donation_time': 'datetime',
        'last_donation_time': 'datetime',
      },
      filterAccountsText: '',
      filterDonorsText: '',
      filterDonorsTimeout: null,
      hideDonors: this.$root.config.hide_donors,
      sortModalVisible: false,
    }
  },

  computed: {
    accountsQueryString() {
      const query = { ...this.accountsQuery }
      delete query.limit
      delete query.offset
      delete query.sort
      return new URLSearchParams(query).toString()
    },

    filteredAccounts() {
      const filter = this.filterAccountsText.toLowerCase().trim()
      if (!filter) {
        return this.accounts
      }

      return this.accounts.filter(data => {
        const displayName = data.account.display_name.toLowerCase()
        const fqn = data.account.fqn.toLowerCase()
        const url = data.account.url.toLowerCase()
        return displayName.includes(filter) || fqn.includes(filter) || url.includes(filter)
      })
    },
  },

  methods: {
    onSortChange(event) {
      this.accountsQuery.sort = event
      this.$emit('update:query', this.accountsQuery)
    },
  },

  mounted() {
    this.accountsQuery = { ...this.deserializeQueryFromRoute() }
    if (this.accountsQuery.donors?.length) {
      this.filterDonorsText = this.accountsQuery.donors[0].replace(/\*/g, '')
    }
  },

  watch: {
    $route() {
      this.accountsQuery = { ...this.query, ...this.deserializeQueryFromRoute() }
    },

    filterDonorsText(newVal) {
      if (this.filterDonorsTimeout) {
        clearTimeout(this.filterDonorsTimeout)
      }

      this.filterDonorsTimeout = setTimeout(() => {
        const accountsQuery = { ...this.accountsQuery }
        if (newVal && newVal.trim() !== '') {
          accountsQuery.donors = '*' + newVal.trim() + '*'
        } else {
          accountsQuery.donors = ''
        }
        this.accountsQuery = accountsQuery
        this.$emit('update:query:donors', this.accountsQuery)
      }, 300)
    },
  },
}
</script>

<style scoped lang="scss">
$account-avatar-size: 3rem;
$amount-width: 8.5rem;
$sort-btn-size: 5rem;

.accounts-list {
  display: flex;
  flex-direction: column;

  .account {
    padding: 1rem 0.75rem;
    transition: background-color 0.2s;
    border-bottom: 1px solid var(--color-border);

    &:hover {
      background-color: var(--color-hover-bg);
    }

    .account-link {
      display: flex;
      align-items: center;
      text-decoration: none;
      color: inherit;

      .account-avatar {
        width: $account-avatar-size;
        height: $account-avatar-size;
        border-radius: 50%;
        overflow: hidden;
        margin-right: 1rem;

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }

      .account-info {
        width: calc(100% - #{$account-avatar-size} - #{$amount-width} - 2rem);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;

        .account-display-name {
          font-weight: bold;
          font-size: 1.1rem;
        }

        .account-username {
          color: var(--color-text-secondary);
          font-size: 0.85rem;
        }
      }

      .amount {
        width: $amount-width;
        margin-left: auto;
        text-align: right;
        font-weight: bold;
        font-size: 1.1rem;
        color: var(--color-primary);
      }
    }
  }

  .filter-container {
    display: flex;
    align-items: center;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--color-border);
    background-color: var(--color-bg);

    input[type="text"] {
      max-width: calc(100% - #{$sort-btn-size} - 1rem);
      width: 100%;
      padding: 0.5rem;
      border: 1px solid var(--color-border);
      border-radius: 0.25rem;
      font-size: 1rem;
    }

    .sort-container {
      margin-left: auto;

      .sort-button {
        width: $sort-btn-size;
        background: none;
        border: none;
        font-size: 1.05em;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;

        i {
          margin-right: 0.2em;
        }
      }
    }
  }
}
</style>

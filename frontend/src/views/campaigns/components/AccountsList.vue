<template>
  <div class="accounts-list">
    <div class="filter-container">
      <input
        type="text"
        v-model="filterText"
        placeholder="Filter accounts..."
        class="filter-input"
      />
    </div>

    <div class="account" v-for="data in filteredAccounts" :key="data.account.fqn">
      <RouterLink :to="`/campaigns/accounts/${data.account.fqn}`" class="account-link">
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
  </div>
</template>

<script>
export default {
  props: {
    accounts: {
      type: Array,
      required: true,
    },
  },

  data() {
    return {
      filterText: '',
    }
  },

  computed: {
    filteredAccounts() {
      const filter = this.filterText.toLowerCase().trim()
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
}
</script>

<style scoped lang="scss">
$account-avatar-size: 3rem;
$amount-width: 6rem;

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
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--color-border);
    background-color: var(--color-bg);

    input[type="text"] {
      max-width: 100%;
      padding: 0.5rem;
      border: 1px solid var(--color-border);
      border-radius: 0.25rem;
      font-size: 1rem;
    }
  }
}
</style>

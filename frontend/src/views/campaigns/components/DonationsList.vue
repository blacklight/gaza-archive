<template>
  <div class="donations-list">
    <div class="filter-container">
      <input
        type="text"
        v-model="filterText"
        placeholder="Filter donors..."
        class="filter-input"
        @input="$emit('update:filter:donors', filterText)"
      />
    </div>

    <div class="donation" v-for="donation in donations" :key="donation.id">
      <RouterLink :to="`/campaigns/donors/${donation.donor}`" class="donor-link">
        <div class="donor-avatar">
          <i class="fas fa-hand-holding-usd" aria-hidden="true"></i>
        </div>
        <div class="donation-info">
          <div class="donor-name">{{ donation.donor || "[Anonymous]" }}</div>
          <div class="donation-time">{{ formatDateTime(donation.created_at) }}</div>
        </div>
        <div class="amount">
          {{ donation.amount.string }}
        </div>
      </RouterLink>
    </div>
  </div>
</template>

<script>
import Dates from '@/mixins/Dates.vue'

export default {
  mixins: [
    Dates,
  ],

  emits: ['update:filter:donors'],

  props: {
    donations: {
      type: Array,
      required: true,
    },

    filter: {
      type: String,
      default: '',
    },
  },

  data() {
    return {
      filterText: '',
    }
  },

  mounted() {
    this.filterText = this.filter
  },
}
</script>

<style scoped lang="scss">
$account-avatar-size: 3rem;
$amount-width: 6rem;

.donations-list {
  width: 100%;
  display: flex;
  flex-direction: column;

  .donation {
    display: flex;
    align-items: center;
    padding: 1rem 0.75rem;
    transition: background-color 0.2s;
    border-bottom: 1px solid var(--color-border);

    &:hover {
      background-color: var(--color-hover-bg);
    }

    .donor-link {
      width: 100%;
      display: flex;
      align-items: center;
      text-decoration: none;
      color: inherit;

      .donor-avatar {
        width: $account-avatar-size;
        height: $account-avatar-size;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: var(--color-border);
        color: var(--color-text-secondary);
        opacity: 0.8;
        border-radius: 50%;
        overflow: hidden;
        margin-right: 1rem;

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }

      .donation-info {
        width: calc(100% - #{$account-avatar-size} - #{$amount-width} - 2rem);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .donor-name {
        font-weight: bold;
        margin-bottom: 0.2rem;
      }

      .donation-time {
        font-size: 0.9rem;
        color: var(--color-text-secondary);
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

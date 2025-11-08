<template>
  <div class="donations-list">
    <div class="filter-container">
      <input
        type="text"
        v-model="filterText"
        placeholder="Filter donors..."
        class="filter-input"
        @input="$emit('update:filter:donors', filterText)"
        v-if="!hideDonors"
      />

      <div class="sort-container">
        <button @click="sortModalVisible = true" title="Sort Accounts" class="sort-button">
          <i class="fas fa-sort" aria-hidden="true"></i>
          Sort
        </button>
      </div>
    </div>

    <div class="donation" v-for="donation in donations" :key="donation.id">
      <div class="donor-link">
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
      </div>
    </div>

    <div class="sort-modal-container" v-if="sortModalVisible">
      <Modal :show="sortModalVisible"
             title="Sort Accounts"
             @close="sortModalVisible = false">
        <Sorter :sort="query.sort || []"
                :fields="sortFields"
                @update:sort="onSortChange" />
      </Modal>
    </div>
  </div>
</template>

<script>
import Dates from '@/mixins/Dates.vue'
import Modal from '@/elements/Modal.vue'
import Sorter from './Sorter.vue'

export default {
  mixins: [Dates],
  emits: ['update:filter:donors', 'update:query'],
  components: {
    Modal,
    Sorter,
  },

  props: {
    donations: {
      type: Array,
      required: true,
    },

    filter: {
      type: String,
      default: '',
    },

    query: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      filterText: '',
      hideDonors: this.$root.config.hide_donors,
      sortModalVisible: false,
      sortFields: {
        'donation.amount': 'float',
        'donation.created_at': 'datetime',
      },
    }
  },

  methods: {
    onSortChange(event) {
      const query = { ...this.query }
      query.sort = event
      this.$emit('update:query', query)
    },
  },

  mounted() {
    this.filterText = this.filter
  },
}
</script>

<style scoped lang="scss">
$account-avatar-size: 3rem;
$amount-width: 8.5rem;
$sort-btn-size: 5rem;

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
    align-items: center;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--color-border);
    background-color: var(--color-bg);

    input[type="text"] {
      max-width: calc(100% - #{$sort-btn-size} - 1rem);
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

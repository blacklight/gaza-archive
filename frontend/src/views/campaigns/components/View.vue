<template>
  <div class="campaigns view">
    <div class="header container">
      <slot name="header" />
      <div class="total item">
        <span class="label">Total Raised</span>
        <span class="value">{{ data?.amount?.string || 0 }}</span>
      </div>

      <div class="first donation date item">
        <span class="label">From</span>
        <span class="value">
          <button @click="showDateFilter = true"
                  title="Filter by Date"
                  class="date-filter-button">
            {{ data?.first_donation_time ? formatDateTime(data.first_donation_time) : 'N/A' }}
          </button>
        </span>
      </div>

      <div class="last donation date item">
        <span class="label">Until</span>
        <span class="value">
          <button @click="showDateFilter = true"
                  title="Filter by Date"
                  class="date-filter-button">
            {{ data?.last_donation_time ? formatDateTime(data.last_donation_time) : 'N/A' }}
          </button>
        </span>
      </div>
    </div>

    <div class="list container">
      <slot name="list" />
    </div>

    <div class="date-filter-modal-container">
      <Modal
        v-if="showDateFilter"
        :show="showDateFilter"
        title="Filter by Date"
        @close="showDateFilter = false">
        <div class="date-filter-modal">
          <label for="start-date">Start Date:</label>
          <span class="input-wrapper">
            <input type="date" id="start-date" v-model="startDate" />
            <button
              v-if="startDate"
              class="clear-button"
              title="Clear start date"
              @click="startDate = null">
              &times;
            </button>
          </span>

          <label for="end-date">End Date:</label>
          <span class="input-wrapper">
            <input type="date" id="end-date" v-model="endDate" />
            <button
              v-if="endDate"
              class="clear-button"
              title="Clear end date"
              @click="endDate = null">
              &times;
            </button>
          </span>

          <div class="modal-actions">
            <button @click="showDateFilter = false">Close</button>
            <button @click="$emit('update:filter:dates', { start: startDate, end: endDate }); showDateFilter = false;">
              Apply Filter
            </button>
          </div>
        </div>
      </Modal>
    </div>
  </div>
</template>

<script>
import CampaignsApi from '@/mixins/api/Campaigns.vue'
import Dates from '@/mixins/Dates.vue'
import Modal from '@/elements/Modal.vue'

export default {
  mixins: [
    CampaignsApi,
    Dates,
  ],

  emits: [
    'update:filter:dates',
  ],

  components: {
    Modal,
  },

  props: {
    data: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      startDate: null,
      endDate: null,
      showDateFilter: false,
    }
  },

  mounted() {
    const query = this.deserializeQueryFromRoute()
    this.startDate = query.start_time ? query.start_time.split('T')[0] : null
    this.endDate = query.end_time ? query.end_time.split('T')[0] : null
  },
}
</script>

<style scoped lang="scss">
@use '@/styles/index' as *;
@use "@/styles/variables" as *;

$clear-btn-size: 1.5em;

.campaigns {
  .header {
    padding: 1em;
    justify-content: center;
    border-bottom: 1px solid var(--color-border);

    .item {
      display: flex;
      align-items: center;

      .label {
        margin-left: 0.8em;
        font-weight: bold;
      }

      .value {
        margin-left: 0.4em;
      }

      &.donation {
        font-size: 1rem;
      }

      &.total {
        font-size: 1.25em;
        margin-left: -0.3em;

        .value {
          font-size: 1.5em;
          color: var(--color-primary);
        }
      }

      &.date {
        .label {
          width: 2.5em;
        }

        .value {
          button {
            background: none;
            border: none;
            color: var(--color-link);
            text-decoration: underline;
            cursor: pointer;
            font-size: 1em;
            padding: 0;
          }
        }
      }
    }
  }

  .list {
    width: 100%;
    max-width: $desktop;
    margin: 0 auto;
    border: 1px solid var(--color-border);
    box-shadow: 1px 1px 3px 3px var(--color-shadow);
    background: var(--color-bg-secondary);

    @include from($desktop) {
      margin: 1em auto 0 auto;
    }
  }

  :deep(.date-filter-modal-container) {
    .date-filter-modal {
      display: flex;
      flex-direction: column;

      label {
        margin-top: 1em;
        font-weight: bold;
      }

      .input-wrapper {
        width: 100%;
        display: inline-flex;
        align-items: center;

        input[type="date"] {
          width: calc(100% - #{$clear-btn-size} - 0.5em);
          background: var(--color-bg);
          color: var(--color-text);
          margin-top: 0.5em;
          padding: 0.5em;
          border: 1px solid var(--color-border);
          border-radius: 0.25em;
        }

        .clear-button {
          width: $clear-btn-size;
          height: $clear-btn-size;
          background: none;
          border: none;
          color: var(--color-text-secondary);
          font-size: 1.2em;
          cursor: pointer;
        }
      }

      .modal-actions {
        margin-top: 1.5em;
        display: flex;
        justify-content: flex-end;

        button {
          margin-left: 1em;
          padding: 0.5em 1em;
          border: none;
          border-radius: 0.25em;
          cursor: pointer;

          &:first-child {
            background: var(--color-bg-secondary);
            color: var(--color-text);
            border: 1px solid var(--color-border);
          }

          &:last-child {
            background: var(--color-primary);
            color: #fff;
          }
        }
      }
    }
  }
}
</style>

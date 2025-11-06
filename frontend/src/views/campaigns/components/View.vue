<template>
  <div class="campaigns view">
    <div class="header container">
      <slot name="header" />
      <div class="total item">
        <span class="label">Total Raised</span>
        <span class="value">{{ data?.amount?.string || 0 }}</span>
      </div>

      <div class="first donation item">
        <span class="label">From</span>
        <span class="value">
          {{ data?.first_donation_time ? formatDateTime(data.first_donation_time) : 'N/A' }}
        </span>
      </div>

      <div class="last donation item">
        <span class="label">Until</span>
        <span class="value">
          {{ data?.last_donation_time ? formatDateTime(data.last_donation_time) : 'N/A' }}
        </span>
      </div>
    </div>

    <div class="list container">
      <slot name="list" />
    </div>
  </div>
</template>

<script>
import Dates from '@/mixins/Dates.vue'

export default {
  mixins: [
    Dates,
  ],

  props: {
    data: {
      type: Object,
      required: true,
    },
  },
}
</script>

<style scoped lang="scss">
@use '@/styles/index' as *;
@use "@/styles/variables" as *;

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
    }
  }

  .list {
    width: 100%;
    max-width: $desktop;
    margin: 0 auto;

    @include from($desktop) {
      margin: 1em auto 0 auto;
    }
    border: 1px solid var(--color-border);
    border-radius: 0.5em;
    box-shadow: 1px 1px 3px 3px var(--color-border);
    background: var(--color-bg-secondary);
  }
}
</style>

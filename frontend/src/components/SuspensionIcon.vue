<template>
  <span v-if="showIcon" class="suspension-icon" :class="stateClass" :title="tooltip">
    <i :class="iconClass" aria-hidden="true"></i>
  </span>
</template>

<script>
export default {
  props: {
    state: {
      type: String,
      required: false,
      default: null
    },
    context: {
      type: String,
      required: false,
      default: 'account'
    }
  },

  computed: {
    showIcon() {
      return this.state && ['LIMITED', 'SUSPENDED', 'DELETED'].includes(this.state)
    },

    stateClass() {
      return `state-${this.state?.toLowerCase()}`
    },

    iconClass() {
      const iconMap = {
        'LIMITED': 'fas fa-exclamation-triangle',
        'SUSPENDED': 'fas fa-ban',
        'DELETED': 'fas fa-user-slash'
      }
      return iconMap[this.state] || ''
    },

    tooltip() {
      const tooltipMap = {
        'LIMITED': 'Account is limited on home instance',
        'SUSPENDED': 'Account is suspended on home instance',
        'DELETED': 'Account is deleted on home instance'
      }
      if (this.context === 'campaign') {
        tooltipMap.DELETED = 'Campaign is deleted'
      }
      return tooltipMap[this.state] || ''
    }
  }
}
</script>

<style scoped lang="scss">
.suspension-icon {
  margin-right: 0.5em;
  font-size: 0.85em;

  &.state-limited {
    color: #f39c12; // Yellow warning
  }

  &.state-suspended {
    color: #e74c3c; // Red stop
  }

  &.state-deleted {
    color: #95a5a6; // Gray trash
  }
}
</style>

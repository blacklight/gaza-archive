<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-content fade-in">
      <div class="modal-header">
        <h2 v-if="title?.length">{{ title }}</h2>
        <button class="modal-close" @click="close">&times;</button>
      </div>
      <div class="modal-body">
        <slot />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    show: {
      type: Boolean,
      required: true,
    },

    title: {
      type: String,
      default: '',
    },
  },
  emits: ['close'],
  methods: {
    close() {
      this.$emit('close')
    },
  },
}
</script>

<style lang="scss" scoped>
@use '@/styles/index' as *;

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;

  .modal-content {
    width: 90%;
    min-width: 300px;
    background: var(--color-bg-secondary);
    border-radius: 8px;
    position: relative;
    max-height: 90%;
    overflow-y: auto;

    @include from($tablet) {
      max-width: $tablet;
    }

    @include until($tablet) {
      max-width: 90%;
    }
  }

  .modal-header {
    background: var(--color-border);
    height: 3em;
    display: flex;
    justify-content: space-between;
    align-items: center;

    h2 {
      width: 100%;
      margin: 0;
      font-size: 1.15em;
      font-weight: normal;
      text-align: center;
    }

    .modal-close {
      position: absolute;
      right: 0.5em;
      background: none;
      border: none;
      font-size: 1.5em;
      cursor: pointer;
      color: var(--color-text-secondary);
      opacity: 0.7;

      &:hover {
        color: #000;
      }
    }
  }

  .modal-body {
    padding: 1em;
  }
}
</style>

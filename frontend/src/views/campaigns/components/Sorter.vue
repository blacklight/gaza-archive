<template>
  <div class="sorter">
    <div class="current-sort">
      <div class="title">Current Sort</div>
      <span v-if="computedSort.length === 0">None</span>
      <span class="fields" v-else>
        <div class="field-container"
             v-for="field in computedSort"
             :key="field.name">
          <div class="sorter-item" @click="toggleFieldOrder(field.name)">
            <span class="field-name">{{ field.name }}</span>
            <span class="field-order" v-if="field.order === 'asc'">▲</span>
            <span class="field-order" v-else-if="field.order === 'desc'">▼</span>
          </div>

          <button class="field-remove"
                  @click="toggleFieldSort(field.name)"
                  :title="`Remove ${field.name} from sort`">
            ✕
          </button>
        </div>
      </span>
    </div>

    <div class="available-fields">
      <div class="title">Available Fields</div>
      <div v-for="_, fieldName in unselectedFields"
           :key="fieldName"
           class="sorter-item"
           @click="toggleFieldSort(fieldName)">
        <span>{{ fieldName }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  emits: ['update:sort'],

  props: {
    fields: {
      type: Object,
      required: true,
    },

    sort: {
      type: Array,
      required: true,
    },
  },

  computed: {
    computedSort() {
      return (this.sort || []).map(sortField => {
        const tokens = sortField.split(':')
        let field = tokens[0]
        let order = 'asc'
        if (tokens.length > 1) {
          order = tokens[1]
        }

        const type = this.fields[field] || 'varchar'
        return { name: field, order, type }
      })
    },

    sortedFields() {
      return Object.keys(this.fields).sort().map(field => {
        const tokens = field.split(':')
        let order = 'asc'
        if (tokens.length > 1) {
          field = tokens[0]
          order = tokens[1]
        }

        return {
          name: field,
          order,
          type: this.fields[field],
        }
      })
    },

    selectedFields() {
      const selected = {};
      (this.sort || []).forEach(sortField => {
        selected[sortField] = this.fields[sortField]
      })
      return selected
    },

    unselectedFields() {
      return this.sortedFields.reduce((acc, field) => {
        if (!this.selectedFields[field.name]) {
          acc[field.name] = field.type
        }
        return acc
      }, {})
    },
  },

  methods: {
    toggleFieldSort(fieldName) {
      const sort = [...this.sort || []]
      const existingIndex = sort.findIndex(sortField => sortField.startsWith(fieldName))
      if (existingIndex !== -1) {
        // Remove the field from sort
        sort.splice(existingIndex, 1)
      } else {
        // Add the field to sort with ascending order
        sort.push(`${fieldName}:asc`)
      }

      this.$emit('update:sort', sort)
    },

    toggleFieldOrder(fieldName) {
      const sort = [...this.sort || []]
      const existingIndex = sort.findIndex(sortField => sortField.startsWith(fieldName))
      if (existingIndex !== -1) {
        const tokens = sort[existingIndex].split(':')
        let order = 'asc'
        if (tokens.length > 1 && tokens[1] === 'asc') {
          order = 'desc'
        }

        sort[existingIndex] = `${fieldName}:${order}`
        this.$emit('update:sort', sort)
      }
    },
  }
}
</script>

<style lang="scss" scoped>
$remove-btn-size: 1.25rem;

.sorter {
  min-height: 400px;
  max-height: 80%;
  display: flex;
  flex-direction: column;
  padding: 1rem;
  overflow-y: auto;

  .sorter-item {
    display: flex;
    justify-content: space-between;
    margin: 0.5rem 0;
    padding: 0.5rem;
    border: 1px solid var(--color-border);
    border-radius: 4px;
    cursor: pointer;
    user-select: none;

    &:hover {
      background-color: var(--color-hover-bg);
    }
  }

  .field-container {
    display: flex;
    align-items: center;
    justify-content: space-between;

    .sorter-item {
      flex-grow: 1;
    }

    .field-remove {
      width: $remove-btn-size;
      height: $remove-btn-size;
      margin-left: 0.5rem;
      border: none;
      background: none;
      color: var(--color-text-secondary);
      font-size: 1rem;
      cursor: pointer;
      user-select: none;

      &:hover {
        color: var(--color-hover-fg);
      }
    }
  }

  .title {
    color: var(--color-primary);
    font-weight: bold;
    margin-bottom: 0.25rem;
  }

  .current-sort {
    margin-bottom: 1rem;

    .sorter-item {
      font-weight: bold;
    }
  }
}
</style>

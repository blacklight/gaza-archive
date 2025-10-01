<script>
export default {
  methods: {
    formatDate(date) {
      const d = new Date(date + "Z")
      return d.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    },

    formatDateTime(date) {
      const d = new Date(date + "Z")
      return d.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    },
  },
}
</script>

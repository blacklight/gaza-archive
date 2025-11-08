<script>
const baseUrl = '/api/v1/internal'

export default {
  methods: {
    async getConfig() {
      return (await fetch(`${baseUrl}/config`)).json()
    },

    async getCurrencies() {
      return (await fetch(`${baseUrl}/currencies`)).json()
    },

    async getDbFields() {
      return (await fetch(`${baseUrl}/db_fields`)).json()
    },
  },
}
</script>

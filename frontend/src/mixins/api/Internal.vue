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

    async getAccountsBot() {
      return (await fetch(`${baseUrl}/bots/accounts`)).json()
    },

    async getCampaignsBot() {
      return (await fetch(`${baseUrl}/bots/campaigns`)).json()
    },
  },
}
</script>

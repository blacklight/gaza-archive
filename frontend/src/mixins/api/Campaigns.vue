<script>
const baseUrl = '/api/v1/campaigns'

export default {
  methods: {
    async getCampaignsAccountsStats(params) {
      const url = `${baseUrl}/accounts`
      const query = new URLSearchParams(params).toString()
      return (await fetch(`${url}?${query}`)).json()
    },

    async getCampaignAccountStats(fqn, params) {
      const url = `${baseUrl}/accounts/${encodeURIComponent(fqn)}`
      const query = new URLSearchParams(params).toString()
      return (await fetch(`${url}?${query}`)).json()
    },

    async getCampaignsDonations(params) {
      const url = `${baseUrl}/donations`
      const query = new URLSearchParams(params).toString()
      return (await fetch(`${url}?${query}`)).json()
    },

    async getCampaignAccountDonations(fqn, params) {
      const url = `${baseUrl}/accounts/${encodeURIComponent(fqn)}/donations`
      const query = new URLSearchParams(params).toString()
      return (await fetch(`${url}?${query}`)).json()
    },
  },

  async getCampaignsDonorsStats(params) {
    const url = `${baseUrl}/donors`
    const query = new URLSearchParams(params).toString()
    return (await fetch(`${url}?${query}`)).json()
  },

  async getCampaignDonorStats(donor, params) {
    const url = `${baseUrl}/donors/${encodeURIComponent(donor)}`
    const query = new URLSearchParams(params).toString()
    return (await fetch(`${url}?${query}`)).json()
  },
}
</script>

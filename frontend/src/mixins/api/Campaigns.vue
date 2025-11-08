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

    async getCurrencies() {
      return (await fetch('/api/v1/internal/currencies')).json()
    },

    async getDbFields() {
      return (await fetch('/api/v1/internal/db_fields')).json()
    },

    deserializeQueryFromRoute() {
      const params = {}

      if (this.$route.query.currency) {
        params.currency = this.$route.query.currency
      }

      if (this.$route.query.accounts) {
        params.accounts = Array.isArray(this.$route.query.accounts)
          ? this.$route.query.accounts
          : [this.$route.query.accounts]
      }

      if (this.$route.query.donors) {
        params.donors = Array.isArray(this.$route.query.donors)
          ? this.$route.query.donors
          : [this.$route.query.donors]
      }

      if (this.$route.query.start_time) {
        params.start_time = this.$route.query.start_time
      }

      if (this.$route.query.end_time) {
        params.end_time = this.$route.query.end_time
      }

      if (this.$route.query.sort) {
        params.sort = Array.isArray(this.$route.query.sort)
          ? this.$route.query.sort
          : [this.$route.query.sort]
      }

      if (this.$route.query.group_by) {
        params.group_by = Array.isArray(this.$route.query.group_by)
          ? this.$route.query.group_by
          : [this.$route.query.group_by]
      }

      if (this.$route.query.limit) {
        params.limit = parseInt(this.$route.query.limit, 10)
      }

      if (this.$route.query.offset) {
        params.offset = parseInt(this.$route.query.offset, 10)
      }

      return Object.keys(params).length ? params : null
    },

    parseQuery(params) {
      const query = {}

      if (params.currency) {
        query.currency = params.currency
      }

      if (params.accounts === '') {
        query.accounts = null
      } else if (params.accounts) {
        query.accounts = params.accounts
      }

      if (params.donors === '') {
        query.donors = null
      } else if (params.donors) {
        query.donors = params.donors
      }

      if (params.start_time) {
        query.start_time = params.start_time
      } else {
        query.start_time = null
      }

      if (params.end_time) {
        query.end_time = params.end_time
      } else {
        query.end_time = null
      }

      if (params.sort) {
        query.sort = params.sort.length ? params.sort : null
      }

      if (params.group_by) {
        query.group_by = params.group_by.length ? params.group_by : null
      }

      if (params.limit) {
        query.limit = params.limit
      } else {
        query.limit = null
      }

      if (params.offset) {
        query.offset = params.offset
      } else {
        query.offset = null
      }

      return query
    },

    serializedQuery(params) {
      const query = this.parseQuery(params)
      if (!Object.keys(query).length) {
        return ''
      }

      return new URLSearchParams(query).toString()
    },

    serializeQueryToRoute(params, { overwrite = false } = {}) {
      let query = this.parseQuery(params)
      if (!Object.keys(query).length) {
        return
      }

      if (overwrite) {
        this.$router.replace({ query })
      } else {
        this.$router.replace({ query: { ...this.$route.query, ...query } })
      }
    },
  },
}
</script>

<script>
export default {
  methods: {
    async getAccounts(params = {}) {
      const query = new URLSearchParams()
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          query.append(key, value)
        }
      })
      const url = `/api/v1/accounts${query.toString() ? '?' + query.toString() : ''}`
      const response = await fetch(url)
      const total = response.headers.get('X-Total-Count')
      const inactive = response.headers.get('X-Inactive-Count')
      return {
        accounts: await response.json(),
        total: total !== null ? parseInt(total, 10) : null,
        inactive: inactive !== null ? parseInt(inactive, 10) : null,
      }
    },

    async getAccountsStats() {
      return (await fetch('/api/v1/accounts/stats')).json()
    },

    async getAccount(fqn) {
      return (await fetch(`/api/v1/accounts/${fqn}`)).json()
    },

    async getAccountSuspensions(fqn, params = {}) {
      const query = new URLSearchParams()
      
      // Handle arrays properly for multiple values
      Object.entries(params).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          value.forEach(v => query.append(key, v))
        } else if (value !== undefined && value !== null) {
          query.append(key, value)
        }
      })
      
      const url = `/api/v1/accounts/${fqn}/suspensions${query.toString() ? '?' + query.toString() : ''}`
      return (await fetch(url)).json()
    },

    async getAccountSuspensionsAudit(fqn, params = {}) {
      const query = new URLSearchParams()
      
      // Handle arrays properly for multiple values
      Object.entries(params).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          value.forEach(v => query.append(key, v))
        } else if (value !== undefined && value !== null) {
          query.append(key, value)
        }
      })
      
      const url = `/api/v1/accounts/${fqn}/suspensions/audit${query.toString() ? '?' + query.toString() : ''}`
      return (await fetch(url)).json()
    },
  },
}
</script>


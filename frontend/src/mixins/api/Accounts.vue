<script>
export default {
  methods: {
    async getAccounts() {
      return (await fetch('/api/v1/accounts')).json()
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


<script>
export default {
  methods: {
    async getAccounts() {
      return (await fetch('/api/v1/accounts')).json()
    },

    async getAccount(fqn) {
      return (await fetch(`/api/v1/accounts/${fqn}`)).json()
    },
  },
}
</script>


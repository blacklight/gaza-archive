<script>
export default {
  methods: {
    async getAccounts() {
      return (await fetch('/api/v1/accounts')).json()
    }
  },
}
</script>


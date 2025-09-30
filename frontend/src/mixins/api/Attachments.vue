<script>
export default {
  methods: {
    async getAttachments(opts) {
      let url = '/api/v1/media'
      if (opts.account) {
        url = `/api/v1/accounts/${opts.account}/media`
        opts.account = encodeURIComponent(opts.account)
      }

      url += `?limit=${opts.limit || 20}&offset=${opts.offset || 0}`
      if (opts.min_id) {
        url += `&min_id=${opts.min_id}`
      }
      if (opts.max_id) {
        url += `&max_id=${opts.max_id}`
      }

      return (await fetch(url)).json()
    },

    async getAttachment(url) {
      return (await fetch(`/api/v1/media/${encodeURIComponent(url)}`)).json()
    },
  },
}
</script>

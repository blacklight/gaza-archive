<script>
export default {
  methods: {
    async getPosts(opts) {
      let url = '/api/v1/posts'
      if (opts.account) {
        url = `/api/v1/accounts/${opts.account}/posts`
        opts.account = encodeURIComponent(opts.account)
      }

      url += `?limit=${opts.limit || 20}&offset=${opts.offset || 0}`
      if (opts.exclude_replies) {
        url += '&exclude_replies=1'
      }
      if (opts.min_id) {
        url += `&min_id=${opts.min_id}`
      }
      if (opts.max_id) {
        url += `&max_id=${opts.max_id}`
      }

      return (await fetch(url)).json()
    },
  },
}
</script>

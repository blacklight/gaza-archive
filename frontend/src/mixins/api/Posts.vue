<script>
export default {
  methods: {
    async getPosts(opts) {
      if (opts.account) {
        opts.account = encodeURIComponent(opts.account)
        let url =  (
          `/api/v1/accounts/${opts.account}/posts` +
          `?limit=${opts.limit || 20}&offset=${opts.offset || 0}`
        )

        if (opts.min_id) {
          url += `&min_id=${opts.min_id}`
        }
        if (opts.max_id) {
          url += `&max_id=${opts.max_id}`
        }

        return (await fetch(url)).json()
      }
    },
  },
}
</script>

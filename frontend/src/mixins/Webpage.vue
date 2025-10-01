<script>
export default {
  methods: {
    getPageTitle() {
      if (this.$route.path === "/accounts") {
        return "Accounts";
      } else if (this.$route.path.startsWith("/accounts/")) {
        return "Account Details";
      } else if (this.$route.path === "/posts") {
        return "Posts";
      } else if (this.$route.path.startsWith("/posts/")) {
        return "Post Details";
      } else {
        return "Gaza Verified Archive"
      }
    },

    getFeedUrl() {
      const head = document.getElementsByTagName('head')[0]
      return head.querySelector("link[type='application/rss+xml']")?.href || '/api/v1/accounts/rss'
    },

    refreshPageTitle() {
      document.title = this.getPageTitle()
    },

    refreshPageMetadata() {
      const head = document.getElementsByTagName('head')[0]
      const properties = document.querySelectorAll('meta[property^="og:"]')
      properties.forEach((element) => element.remove())
      head.insertAdjacentHTML('beforeend', `
        <meta property="og:title" content="${this.getPageTitle()}" />
        <meta property="og:image" content="/favicon.ico" />
        <meta property="og:site_name" content="Gaza Verified Archive" />
      `)

      let feedUrl = '/api/v1/accounts/rss'
      if (this.$route.path.startsWith("/accounts/")) {
        const accountId = this.$route.path.split("/")[2]
        if (this.$route.query.view === "posts") {
          feedUrl = `/api/v1/accounts/${accountId}/posts/rss`
        } else {
          feedUrl = `/api/v1/accounts/${accountId}/media/rss`
        }
      } else if (this.$route.path === "/posts") {
        feedUrl = '/api/v1/posts/rss'
      } else if (this.$route.path.startsWith("/media")) {
        feedUrl = `/api/v1/media/rss`
      }

      let link = document.querySelector("link[type='application/rss+xml']")
      if (link) {
        link.href = feedUrl
      } else {
        head.insertAdjacentHTML('beforeend', `
          <link rel="alternate" type="application/rss+xml" title="RSS Feed" href="${feedUrl}" />
        `)
      }
    },
  }
};
</script>

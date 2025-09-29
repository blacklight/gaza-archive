<template>
  <div class="index view">
    <div class="title">
      <img src="/favicon.ico">
      <h1>Gaza Verified Archive</h1>
    </div>

    <p>This is a public archive of verified from Gaza who registered to
    <a href="https://jointhefediverse.net/" target="_blank">the Fediverse</a>
    in the second half of 2025, in the aftermath of the devastating war that began on October 7,
    2023.</p>

    <p>These accounts have faced significant censorship on centralized platforms like X, Facebook,
    Instagram and Bluesky, and have resorted to decentralized alternatives to continue sharing their
    voices and stories and ask for funding and support.</p>

    <p>However, administrators of Mastodon instances may also be pressured to suspend these
    accounts, or even delete them entirely, with no chance of appeal or migration and the loss of
    all the data they uploaded.</p>

    <p>Since these accounts are publicly providing us first-hand evidence of an ongoing genocide and
    war crimes, we believe it is crucial to preserve their content and make it accessible to the
    public, even if the original accounts are suspended or deleted.</p>

    <p>This archive fetches the list of verified accounts from the
    <a href="https://gaza-verified.org" target="_blank">Gaza Verified</a> website, an initiative
    mainly driven by <a href="https://mastodon.ar.al/@aral" target="_blank">Aral Balkan</a> and
    <a href="https://mastodon.social/@joynewacc" target="_blank">Farah "Joy"</a> to verify and help
    people on the ground in Gaza.</p>

    <p>The project used to generate this archive and periodically scrape the verified accounts is
    <a href="https://git.platypush.tech/blacklight/gaza-archive" target="_blank">open source</a>,
    released under the GPLv3 license, and it's open to contributions and improvements.</p>

    <p>We also invite as many hosting foundations and enthusiasts as possible to run copies of this
    archive, to ensure its availability and redundancy.</p>

    <p>The Gaza Verified Archive is maintained by
    <a href="https://manganiello.social/users/fabio" rel="me" target="_blank">Fabio Manganiello</a>,
    who also runs the <a href="https://archive.gaza.onl" target="_blank">official copy</a> of the
    archive.</p>

    <p>The information is provided over several interfaces:</p>

    <ul>
      <li>A web interface (this one), which allows browsing for accounts, posts and media.</li>
      <li>A REST API - a Swagger interface is available at
        <a href="/swagger" target="_blank"><code>/swagger</code></a>.</li>
      <li>A <a href="/media" target="_blank">static Web directory interface</a> to browse for the
        uploaded media files, indexed by account.</li>
      <li>You can also download the <a href="/app.db">full SQLite database</a> used to power the
        archive, containing all the accounts, posts and media metadata.</li>
    </ul>
  </div>
</template>

<style scoped lang="scss">
.index {
  max-width: 800px;
  margin: 0 auto;
  padding: 1em;

  .title {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1em;
    gap: 1em;
  }

  h1 {
    margin-bottom: 0.5em;
    display: flex;
    align-items: center;
  }

  p {
    line-height: 1.5em;
    margin-bottom: 1em;
  }

  ul {
    margin-left: 1.5em;
    margin-bottom: 1em;

    li {
      margin-bottom: 0.5em;
    }
  }

  a {
    color: var(--color-link);
    text-decoration: underline;

    &:hover {
      text-decoration: none;
    }
  }
}
</style>

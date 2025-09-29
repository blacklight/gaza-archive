<template>
  <Loader v-if="loading" />
  <div class="error" v-else-if="!account">
    <h2>Account not found</h2>
  </div>
  <div class="account view" v-else>
    <div class="header">
      <div class="title">
        <div class="banner">
          <a :href="account.header_url" target="_blank" rel="noopener" v-if="account.header_url">
            <img :src="account.header_url" :alt="`Banner of ${account.display_name}`" />
          </a>
        </div>
        <div class="avatar">
          <img :src="account.avatar_url" :alt="`Avatar of ${account.display_name}`" />
        </div>
        <div class="details">
          <h2>{{ account.display_name }}</h2>
          <p class="fqn">
            <a :href="account.url" target="_blank" rel="noopener">
              {{ account.fqn }}
            </a>
          </p>
        </div>
      </div>

      <div class="note" v-if="account.profile_note">
        <p v-html="account.profile_note"></p>
      </div>
    </div>
  </div>
</template>

<script>
import AccountsApi from '@/mixins/api/Accounts.vue'
import Loader from '@/elements/Loader.vue'

export default {
  mixins: [AccountsApi],
  components: {
    Loader,
  },

  data() {
    return {
      account: null,
      loading: true,
    }
  },

  methods: {
    async refresh() {
      this.account = await this.getAccount(this.$route.params.fqn)
    }
  },

  async mounted() {
    try {
      await this.refresh()
    } finally {
      this.loading = false
    }
  },
}
</script>

<style scoped lang="scss">
$banner-height: 200px;

.account.view {
  max-width: 800px;
  display: flex;
  flex-direction: column;
  margin: 0 auto;
  padding: 1em;

  .header {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-bottom: 1em;

    .title {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 2em;
    }

    .banner {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: $banner-height;
      overflow: hidden;
      z-index: -1;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transform: scale(1.0);
      }
    }

    h2 {
      text-align: center;
      margin-bottom: 0.25em;
    }

    .avatar {
      width: 150px;
      height: 150px;
      margin-top: calc($banner-height / 4);
      border-radius: 50%;
      overflow: hidden;
      margin-bottom: 0.5em;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }

    .details {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      margin-top: calc($banner-height / 2.5);

      .fqn {
        margin: 0;
        font-size: 1em;
        font-weight: 200;
        color: var(--color-text-secondary);
        word-break: break-all;
      }
    }
  }
}
</style>

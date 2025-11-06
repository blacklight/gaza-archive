<template>
  <Loader v-if="loading" />
  <CampaignsView :data="data" v-else-if="data">
    <template #header>
      <div class="account-header" v-if="account">
        <div class="account-avatar">
          <img :src="account.avatar_path" :alt="`${account.display_name}'s avatar`" />
        </div>
        <div class="account-info">
          <RouterLink :to="`/accounts/${account.fqn}`">
            <div class="account-display-name">{{ account.display_name }}</div>
            <div class="account-username">{{ account.fqn }}</div>
          </RouterLink>
          <div class="campaign-link">
            <a :href="account.campaign_url" target="_blank" rel="noopener noreferrer">
              <i class="fas fa-hand-holding-usd" aria-hidden="true"></i>
              {{ account.campaign_url }}
            </a>
          </div>
        </div>
      </div>
    </template>

    <template #list>
      <DonationsList
          :donations="donations"
          @update:filter:donors="onDonorFilterTextUpdate" />
    </template>
  </CampaignsView>
</template>

<script>
import AccountsApi from '@/mixins/api/Accounts.vue'
import CampaignsApi from '@/mixins/api/Campaigns.vue'
import CampaignsView from '../components/View.vue'
import DonationsList from '../components/DonationsList.vue'
import Loader from "@/elements/Loader.vue"

export default {
  mixins: [
    AccountsApi,
    CampaignsApi,
  ],

  components: {
    CampaignsView,
    DonationsList,
    Loader,
  },

  computed: {
    accountFqn() {
      return this.$route.params.fqn
    },
  },

  data() {
    return {
      loading: false,
      donationsLoading: false,
      account: null,
      data: null,
      donations: [],
      donationsQuery: {
        limit: 50,
        offset: 0,
        sort: ['donation.created_at:desc'],
      },
      donorFilterText: '',
      donorFilterTimeout: null,
    }
  },

  methods: {
    onDonorFilterTextUpdate(text) {
      if (this.donorFilterTimeout) {
        clearTimeout(this.donorFilterTimeout)
      }

      this.donorFilterTimeout = setTimeout(() => {
        this.donorFilterText = text
      }, 500)
    },

    async refresh(loadAll = true) {
      if (loadAll) {
        this.loading = true
      } else {
        this.donationsLoading = true
      }

      this.donationsQuery.offset = 0
      let donorFilter = null
      if (this.donorFilterText?.trim().length) {
        donorFilter = [`*${this.donorFilterText.trim()}*`]
        this.donationsQuery.donors = donorFilter
      } else {
        delete this.donationsQuery.donors
      }

      try {
        [this.data, this.account, this.donations] = await Promise.all(
          [
            await this.getCampaignAccountStats(
              this.accountFqn, donorFilter ? { donors: donorFilter } : {}
            ),
            await this.getAccount(this.accountFqn),
            await this.getCampaignAccountDonations(this.accountFqn, this.donationsQuery),
          ]
        )
      } finally {
        this.loading = false
        this.donationsLoading = false
      }
    },

    async onBottomScroll() {
      if (this.loading || this.donationsLoading || !this.data) {
        return
      }

      this.donationsLoading = true
      this.donationsQuery.offset += this.donationsQuery.limit

      try {
        const newDonations = await this.getCampaignAccountDonations(this.accountFqn, this.donationsQuery)
        this.donations = this.donations.concat(newDonations)
      } finally {
        this.donationsLoading = false
      }
    },
  },

  watch: {
    donorFilterText: async function() {
      await this.refresh(false)
    },
  },

  async mounted() {
    await this.refresh()
    this.$root.registerInfiniteScrollCallback(this.onBottomScroll)
  },

  unmounted() {
    this.$root.unregisterInfiniteScrollCallback(this.onBottomScroll)
  }
}
</script>

<style scoped lang="scss">
@use '@/styles/index' as *;
@use "@/styles/variables" as *;

.account-header {
  display: flex;
  align-items: center;
  padding: 0 0.5em 1em 0.5em;
  margin-bottom: 1em;
  border-bottom: 1px solid var(--color-border);

  .account-avatar {
    width: 64px;
    height: 64px;
    margin-right: 1.2em;
    border-radius: 50%;
    overflow: hidden;
    flex-shrink: 0;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }

  .account-info {
    .account-display-name {
      font-size: 1.5em;
      font-weight: bold;
      margin-bottom: 0.1em;
    }

    .account-username {
      font-size: 1em;
      color: var(--color-text-secondary);
    }
  }

  .campaign-link {
    margin-top: 0.5em;

    a {
      text-decoration: none;
      color: var(--color-primary);
      font-weight: bold;

      i {
        margin-right: 0.4em;
      }
    }
  }
}
</style>

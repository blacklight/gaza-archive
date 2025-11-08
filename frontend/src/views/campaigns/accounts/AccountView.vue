<template>
  <Loader v-if="loading" />
  <CampaignsView :data="data"
                 @update:currency="setCurrency"
                 @update:filter:dates="setDateFilter"
                 v-else-if="data">
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
          :filter="donorFilterText"
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
      fields: {},
    }
  },

  methods: {
    setCurrency(currency) {
      if (this.donationsQuery.currency === currency) {
        return
      }

      this.donationsQuery.currency = currency
      this.serializeQueryToRoute(this.donationsQuery)
      this.refresh()
    },

    onDonorFilterTextUpdate(text) {
      if (this.donorFilterTimeout) {
        clearTimeout(this.donorFilterTimeout)
      }

      this.donorFilterTimeout = setTimeout(() => {
        this.donorFilterText = text
        if (this.donorFilterText?.trim().length) {
          this.donationsQuery.donors = [`*${this.donorFilterText.trim()}*`]
        } else {
          delete this.donationsQuery.donors
        }

        this.serializeQueryToRoute(
          {
            ...this.donationsQuery,
            donors: this.donationsQuery.donors || '',
          },
          { overwrite: true }
        )

        if (this.donorFilterTimeout) {
          clearTimeout(this.donorFilterTimeout)
          this.donorFilterTimeout = null
        }
      }, 500)
    },

    setDateFilter(dates) {
      if (dates?.start) {
        this.donationsQuery.start_time = dates.start + 'T00:00:00'
      } else {
        delete this.donationsQuery.start_time
      }

      if (dates?.end) {
        this.donationsQuery.end_time = dates.end + 'T23:59:59'
      } else {
        delete this.donationsQuery.end_time
      }

      this.serializeQueryToRoute(this.donationsQuery)
      this.refresh()
    },

    async refresh(loadAll = true) {
      if (loadAll) {
        this.loading = true
      } else {
        this.donationsLoading = true
      }

      this.donationsQuery.offset = 0
      this.serializeQueryToRoute(
        {
          ...this.donationsQuery,
          donors: this.donationsQuery.donors || '',
        }
      )

      const campaignAccountStatsArgs = { ...this.donationsQuery }
      delete campaignAccountStatsArgs.limit
      delete campaignAccountStatsArgs.offset
      delete campaignAccountStatsArgs.sort

      try {
        [this.data, this.account, this.donations] = await Promise.all(
          [
            await this.getCampaignAccountStats(this.accountFqn, campaignAccountStatsArgs),
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
      this.donationsQuery.offset += (this.donationsQuery.limit || 0)

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
    this.donationsQuery = {
      ...this.donationsQuery,
      ...(this.deserializeQueryFromRoute() || {}),
    }

    if (this.donationsQuery.donors && this.donationsQuery.donors.length > 0) {
      const donorFilter = this.donationsQuery.donors[0]
      this.donorFilterText = donorFilter.replace(/\*/g, '')
    }

    this.fields = await this.getDbFields()
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

<template>
  <Loader v-if="loading" />
  <CampaignsView :data="data"
                 @update:filter:dates="setDateFilter"
                 @update:currency="setCurrency"
                 v-else-if="data">
    <template #list>
      <AccountsList :accounts="accounts" />
    </template>
  </CampaignsView>
</template>

<script>
import AccountsList from '../components/AccountsList.vue'
import CampaignsApi from '@/mixins/api/Campaigns.vue'
import CampaignsView from '../components/View.vue'
import Dates from '@/mixins/Dates.vue'
import Loader from "@/elements/Loader.vue"

export default {
  mixins: [
    CampaignsApi,
    Dates,
  ],

  components: {
    AccountsList,
    CampaignsView,
    Loader,
  },

  data() {
    const now = new Date()
    return {
      loading: false,
      data: null,
      accounts: [],
      query: {
        sort: ['amount'],
        // Last week
        start_time: new Date(
          now.getFullYear(),
          now.getMonth(),
          now.getDate() - 7,
        ).toISOString().split('T')[0] + 'T00:00:00',
      },
    }
  },

  methods: {
    setCurrency(currency) {
      if (this.query.currency === currency) {
        return
      }

      this.query.currency = currency
      this.serializeQueryToRoute(this.query)
      this.refresh()
    },

    setDateFilter(dates) {
      if (dates?.start) {
        this.query.start_time = dates.start + 'T00:00:00'
      } else {
        delete this.query.start_time
      }

      if (dates?.end) {
        this.query.end_time = dates.end + 'T23:59:59'
      } else {
        delete this.query.end_time
      }

      this.serializeQueryToRoute(this.query)
      this.refresh()
    },

    async refresh() {
      this.serializeQueryToRoute(this.query)
      this.loading = true

      try {
        this.data = await this.getCampaignsAccountsStats(this.query)
        this.accounts = this.data.data || []
      } finally {
        this.loading = false
      }
    },
  },

  async mounted() {
    const query = this.deserializeQueryFromRoute()
    if (query) {
      this.query = {
        ...this.query,
        ...query,
      }
    }

    await this.refresh()
  }
}
</script>

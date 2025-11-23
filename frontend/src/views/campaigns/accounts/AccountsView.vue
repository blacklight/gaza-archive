<template>
  <Loader v-if="loading" />
  <CampaignsView :data="data"
                 @update:filter:dates="setDateFilter"
                 @update:currency="setCurrency"
                 v-if="data">
    <template #list>
      <AccountsList :accounts="accounts"
                    :fields="fields"
                    :query="query"
                    @update:query="onQueryUpdate"
                    @update:query:donors="onQueryUpdate($event, {overwrite: ['donors']})" />
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
      accounts: [],
      data: null,
      fields: {},
      loading: false,
      query: {
        sort: ['amount:asc'],
        // Last week
        start_time: new Date(
          now.getFullYear(),
          now.getMonth(),
          now.getDate() - 6,
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

    onQueryUpdate(newQuery, options = { overwrite: [], }) {
      this.query = Object.fromEntries(
        [
          ...Object.entries(this.query).filter(
            ([key,]) => !options.overwrite.includes(key),
          ),
          ...Object.entries(newQuery),
        ].filter(
          ([, value]) => value != null && value !== '',
        ),
      )

      this.serializeQueryToRoute(this.query, { overwrite: true })
      this.refresh()
    },

    async refresh() {
      this.serializeQueryToRoute(this.query, { overwrite: true })
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

    this.fields = await this.getDbFields()
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

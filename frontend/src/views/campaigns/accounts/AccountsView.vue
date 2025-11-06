<template>
  <Loader v-if="loading" />
  <CampaignsView :data="data" v-else-if="data">
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
    return {
      loading: false,
      data: null,
      accounts: [],
      query: {
        sort: ['amount'],
      },
    }
  },

  methods: {
    async refresh() {
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
    await this.refresh()
  }
}
</script>

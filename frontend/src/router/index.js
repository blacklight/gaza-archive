import { createRouter, createWebHistory } from 'vue-router'

import AccountCampaignView from "@/views/campaigns/accounts/AccountView.vue";
import AccountView from "@/views/account/View.vue";
import AccountsCampaignsView from "@/views/campaigns/accounts/AccountsView.vue";
import AccountsView from "@/views/accounts/View.vue";
import AttachmentsView from "@/views/attachments/View.vue";
import IndexView from "@/views/Index.vue";
import PostView from "@/views/posts/PostView.vue";
import PostsView from "@/views/posts/View.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: IndexView,
    },
    {
      path: '/accounts',
      component: AccountsView,
    },
    {
      path: '/accounts/:fqn',
      component: AccountView,
    },
    {
      path: '/campaigns/accounts',
      component: AccountsCampaignsView,
    },
    {
      path: '/campaigns/accounts/:fqn',
      component: AccountCampaignView,
    },
    {
      path: '/posts',
      component: PostsView,
    },
    {
      path: '/posts/:id',
      component: PostView,
    },
    {
      path: '/attachments',
      component: AttachmentsView,
    },
  ],
})

export default router

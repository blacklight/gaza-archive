import { createRouter, createWebHistory } from 'vue-router'

import AccountView from "@/views/account/View.vue";
import AccountsView from "@/views/accounts/View.vue";
import IndexView from "@/views/Index.vue";

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
  ],
})

export default router

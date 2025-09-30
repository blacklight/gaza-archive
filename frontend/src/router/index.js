import { createRouter, createWebHistory } from 'vue-router'

import AccountView from "@/views/account/View.vue";
import AccountsView from "@/views/accounts/View.vue";
import IndexView from "@/views/Index.vue";
import PostView from "@/views/posts/PostView.vue";

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
      path: '/posts/:id',
      component: PostView,
    },
  ],
})

export default router

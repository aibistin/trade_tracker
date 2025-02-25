/* 
src/router/index.js
This file contains the Vue Router configuration.
*/
import { createRouter, createWebHistory } from "vue-router";
// import AllTrades from "@/views/AllTrades.vue";

const routes = [
  {
    path: "/home",
    name: "Home",
    component: () => import("@/views/TradeHome.vue"),
  },
  {
    /* open/all/closed trades */
    path: "/trades/:scope/:stockSymbol",
    name: "AllTrades",
    /* Import only when needed to reduce initial load time */
    component: () => import("@/views/AllTrades.vue"),
    props: true // Pass route params as props
  },
/* TODO Try the below method */
  // {
  //   path: '/all_trades/:stockSymbol',
  //   name: 'AllTrades',
  //   component: AllTrades,
  //   props: (route) => ({
  //     stockSymbol: route.params.stockSymbol,
  //     scope: 'all' // or 'open' for OpenTrades
  //   })
  // }

  {
    path: "/", // Redirect root to /home
    component: () => import("@/views/TradeHome.vue"),
    redirect: "/home",
  },
  {
    path: "/:pathMatch(.*)*", // Catch-all route
    name: "NotFound",
    component: () => import("../views/NotFound.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;

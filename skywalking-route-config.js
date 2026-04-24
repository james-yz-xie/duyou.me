// Route configuration for SkyWalking monitoring page
// Add this route to your tianji-portal-vue/src/router/index.js

const skywalkingRoute = {
  path: '/monitoring/skywalking',
  name: 'SkyWalking',
  component: () => import('@/views/monitoring/SkyWalking.vue'),
  meta: {
    title: 'SkyWalking APM 监控',
    icon: 'el-icon-monitor',
    requiresAuth: true,
    permission: 'monitoring:skywalking:view'
  }
}

// Example of how to integrate into existing router configuration:
/*
import Vue from 'vue'
import VueRouter from 'vue-router'

Vue.use(VueRouter)

const routes = [
  // ... existing routes ...
  skywalkingRoute,
  // ... other routes ...
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router
*/

export default skywalkingRoute

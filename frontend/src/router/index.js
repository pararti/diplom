import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Orders from '../views/Orders.vue'
import Materials from '../views/Materials.vue'
import Optimization from '../views/Optimization.vue'
import Schedule from '../views/Schedule.vue'
import Analytics from '../views/Analytics.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/orders',
    name: 'Orders',
    component: Orders
  },
  {
    path: '/materials',
    name: 'Materials',
    component: Materials
  },
  {
    path: '/optimization',
    name: 'Optimization',
    component: Optimization
  },
  {
    path: '/schedule',
    name: 'Schedule',
    component: Schedule
  },
  {
    path: '/analytics',
    name: 'Analytics',
    component: Analytics
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 
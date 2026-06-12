import { createRouter, createWebHashHistory } from 'vue-router'

import SingleDetect from '../components/SingleDetect.vue'
import BatchDetect from '../components/BatchDetect.vue'
import CameraDetect from '../components/CameraDetect.vue'
import AIChat from '../components/AIChat.vue'
import ResultCharts from '../components/ResultCharts.vue'
import AdminPanel from '../components/AdminPanel.vue'
import Community from '../components/Community.vue'

const routes = [
  { path: '/', redirect: '/single' },
  { path: '/single', component: SingleDetect, name: 'single' },
  { path: '/batch', component: BatchDetect, name: 'batch' },
  { path: '/camera', component: CameraDetect, name: 'camera' },
  { path: '/chat', component: AIChat, name: 'chat' },
  { path: '/charts', component: ResultCharts, name: 'charts' },
  { path: '/admin', component: AdminPanel, name: 'admin' },
  { path: '/community', component: Community, name: 'community' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router

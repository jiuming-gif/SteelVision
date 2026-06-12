<template>
  <aside id="sidebar" class="fixed left-0 top-0 h-full w-64 bg-white dark:bg-slate-950 border-r border-gray-200 dark:border-slate-800 flex flex-col z-30 transition-all duration-300 shadow-lg">
    <div class="p-5 border-b border-gray-200 dark:border-slate-800">
      <h1 class="text-xl font-bold bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
        <i class="fa-solid fa-microchip mr-2"></i>SteelVision
      </h1>
      <p class="text-xs text-gray-400 mt-1">车辆零部件缺陷检测平台</p>
    </div>
    <nav class="flex-1 py-4 space-y-1 px-3">
      <router-link v-for="item in menuItems" :key="item.path" :to="item.path"
        class="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200"
        :class="$route.path === item.path
          ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 shadow-sm'
          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-800 hover:text-gray-900 dark:hover:text-gray-200'">
        <i :class="item.icon" class="w-5 text-center"></i>
        <span>{{ item.label }}</span>
      </router-link>
    </nav>
    <div class="p-4 border-t border-gray-200 dark:border-slate-800">
      <button @click="store.toggleTheme()" class="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-800 transition-all">
        <i :class="themeIcon" class="w-5 text-center"></i>
        <span>{{ themeLabel }}</span>
      </button>
    </div>
  </aside>

  <main class="ml-64 min-h-screen p-8 transition-all duration-300">
    <router-view></router-view>
  </main>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useAppStore } from './stores'

const store = useAppStore()

const menuItems = [
  { path: '/single', label: '单图检测', icon: 'fa-solid fa-magnifying-glass' },
  { path: '/batch', label: '批量检测', icon: 'fa-solid fa-layer-group' },
  { path: '/camera', label: '摄像头检测', icon: 'fa-solid fa-camera' },
  { path: '/chat', label: 'AI 对话', icon: 'fa-solid fa-robot' },
  { path: '/charts', label: '检测结果', icon: 'fa-solid fa-chart-pie' },
  { path: '/admin', label: '管理面板', icon: 'fa-solid fa-shield-halved' },
  { path: '/community', label: '社区', icon: 'fa-solid fa-users' },
]

const themeIcon = computed(() => store.darkMode ? 'fa-solid fa-sun' : 'fa-solid fa-moon')
const themeLabel = computed(() => store.darkMode ? '浅色模式' : '深色模式')

onMounted(() => {
  store.initTheme()
})
</script>

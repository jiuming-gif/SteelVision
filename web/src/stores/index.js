import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const darkMode = ref(localStorage.getItem('theme') === 'dark' || false)
  const user = ref(null)
  const detectResults = ref([])

  function toggleTheme() {
    darkMode.value = !darkMode.value
    localStorage.setItem('theme', darkMode.value ? 'dark' : 'light')
    document.documentElement.classList.toggle('dark', darkMode.value)
  }

  function initTheme() {
    if (
      darkMode.value ||
      (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)
    ) {
      darkMode.value = true
      document.documentElement.classList.add('dark')
    }
  }

  return { darkMode, user, detectResults, toggleTheme, initTheme }
})

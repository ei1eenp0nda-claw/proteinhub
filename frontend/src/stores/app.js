import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // State
  const sidebarCollapsed = ref(false)
  const isMobile = ref(window.innerWidth < 768)

  // Actions
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const setMobile = (value) => {
    isMobile.value = value
  }

  return {
    sidebarCollapsed,
    isMobile,
    toggleSidebar,
    setMobile,
  }
})
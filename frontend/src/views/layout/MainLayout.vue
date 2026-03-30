<template>
  <div class="main-layout">
    <AppHeader />
    <div class="layout-content">
      <router-view />
    </div>
    <AppFooter v-if="!isMobile" />
    <MobileNav v-if="isMobile" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'
import MobileNav from '@/components/layout/MobileNav.vue'

const appStore = useAppStore()
const isMobile = computed(() => appStore.isMobile)

// 监听窗口大小变化
window.addEventListener('resize', () => {
  appStore.setMobile(window.innerWidth < 768)
})
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.layout-content {
  flex: 1;
  padding-top: 60px;
}

@media (max-width: 768px) {
  .layout-content {
    padding-top: 50px;
    padding-bottom: 60px;
  }
}
</style>
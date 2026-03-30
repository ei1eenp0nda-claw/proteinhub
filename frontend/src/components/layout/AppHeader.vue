<template>
  <header class="app-header" :class="{ 'is-scrolled': isScrolled }">
    <div class="header-container">
      <!-- Logo -->
      <div class="logo" @click="$router.push('/')">
        <img src="/vite.svg" alt="ProteinHub" class="logo-icon" />
        <span class="logo-text">ProteinHub</span>
      </div>

      <!-- 搜索栏 -->
      <div class="search-bar" v-if="!isMobile">
        <el-input
          v-model="searchQuery"
          placeholder="搜索笔记、作者..."
          class="search-input"
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button @click="handleSearch">
              <Search />
            </el-button>
          </template>
        </el-input>
      </div>

      <!-- 导航操作 -->
      <div class="header-actions">
        <!-- 发布按钮 -->
        <el-button
          type="primary"
          class="publish-btn"
          @click="$router.push('/publish')"
        >
          <Plus />
          <span v-if="!isMobile">发布</span>
        </el-button>

        <!-- 用户菜单 -->
        <template v-if="userStore.isAuthenticated">
          <el-dropdown @command="handleCommand">
            <div class="user-info">
              <el-avatar
                :size="32"
                :src="userStore.currentUser?.avatar"
                class="user-avatar"
              >
                {{ userStore.currentUser?.nickname?.charAt(0) || 'U' }}
              </el-avatar>
              <span v-if="!isMobile" class="user-name">
                {{ userStore.currentUser?.nickname }}
              </span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <User /> 个人主页
                </el-dropdown-item>
                <el-dropdown-item command="favorites">
                  <Star /> 我的收藏
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <Setting /> 设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <SwitchButton /> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>

        <template v-else>
          <el-button @click="$router.push('/login')">登录</el-button>
          <el-button type="primary" @click="$router.push('/register')">注册</el-button>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()

const searchQuery = ref('')
const isScrolled = ref(false)

const isMobile = computed(() => appStore.isMobile)

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push(`/search?q=${encodeURIComponent(searchQuery.value)}`)
  }
}

const handleCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'favorites':
      router.push('/favorites')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      userStore.logout()
      router.push('/')
      break
  }
}

const handleScroll = () => {
  isScrolled.value = window.scrollY > 10
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: #fff;
  z-index: 1000;
  transition: box-shadow 0.3s;
}

.app-header.is-scrolled {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.header-container {
  max-width: 1440px;
  height: 100%;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: opacity 0.3s;
}

.logo:hover {
  opacity: 0.8;
}

.logo-icon {
  width: 32px;
  height: 32px;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: #ff2442;
  background: linear-gradient(135deg, #ff2442 0%, #ff6b7a 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.search-bar {
  flex: 1;
  max-width: 400px;
  margin: 0 40px;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 20px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.publish-btn {
  border-radius: 20px;
  padding: 8px 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 20px;
  transition: background 0.3s;
}

.user-info:hover {
  background: #f5f5f5;
}

.user-avatar {
  border: 2px solid #ff2442;
}

.user-name {
  font-size: 14px;
  color: #333;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .app-header {
    height: 50px;
  }

  .logo-text {
    font-size: 16px;
  }

  .header-actions {
    gap: 8px;
  }

  .publish-btn {
    padding: 6px 12px;
  }

  .publish-btn span {
    display: none;
  }
}
</style>
<template>
  <div class="admin-layout">
    <aside class="admin-sidebar">
      <div class="sidebar-header">
        <img src="/vite.svg" alt="logo" class="logo" />
        <span>管理后台</span>
      </div>

      <el-menu
        :default-active="$route.path"
        router
        class="admin-menu"
        background-color="#001529"
        text-color="#fff"
        active-text-color="#ff2442"
      >
        <el-menu-item index="/admin">
          <DataLine />
          <span>数据概览</span>
        </el-menu-item>

        <el-menu-item index="/admin/content">
          <Document />
          <span>内容管理</span>
        </el-menu-item>

        <el-menu-item index="/admin/users">
          <User />
          <span>用户管理</span>
        </el-menu-item>

        <el-menu-item divided @click="goToHome">
          <HomeFilled />
          <span>返回首页</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <div class="admin-main">
      <header class="admin-header">
        <div class="breadcrumb">
          <!-- 面包屑 -->
        </div>

        <div class="header-actions">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :src="userStore.currentUser?.avatar">
                {{ userStore.currentUser?.nickname?.charAt(0) }}
              </el-avatar>
              {{ userStore.currentUser?.nickname }}
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="admin-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { DataLine, Document, User, HomeFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const goToHome = () => {
  router.push('/')
}

const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
}

.admin-sidebar {
  width: 220px;
  background: #001529;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar-header {
  height: 64px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 24px;
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header .logo {
  width: 32px;
  height: 32px;
}

.sidebar-header span {
  font-size: 18px;
  font-weight: 600;
}

.admin-menu {
  border-right: none;
}

.admin-main {
  flex: 1;
  margin-left: 220px;
  background: #f0f2f5;
  min-height: 100vh;
}

.admin-header {
  height: 64px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 99;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
}

.admin-content {
  padding: 24px;
}

@media (max-width: 768px) {
  .admin-sidebar {
    width: 64px;
  }

  .sidebar-header span,
  .admin-menu :deep(.el-menu-item span) {
    display: none;
  }

  .admin-main {
    margin-left: 64px;
  }
}
</style>
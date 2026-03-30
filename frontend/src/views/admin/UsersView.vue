<template>
  <div class="users-view">
    <div class="page-header">
      <h2>用户管理</h2>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索用户..."
          style="width: 240px"
          clearable
        >
          <template #suffix>
            <Search />
          </template>
        </el-input>
      </div>
    </div>

    <div class="filter-bar">
      <el-radio-group v-model="filterStatus">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="active">正常</el-radio-button>
        <el-radio-button label="banned">已封禁</el-radio-button>
      </el-radio-group>
    </div>

    <el-table :data="filteredUsers" style="width: 100%" v-loading="loading">
      <el-table-column type="selection" width="55" />
      
      <el-table-column label="用户信息" min-width="200">
        <template #default="{ row }">
          <div class="user-info">
            <el-avatar :size="40" :src="row.avatar">
              {{ row.nickname?.charAt(0) }}
            </el-avatar>
            <div class="user-details">
              <p class="user-name">{{ row.nickname }}</p>
              <p class="user-email">{{ row.email }}</p>
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="role" label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : ''" size="small">
            {{ row.role === 'admin' ? '管理员' : '普通用户' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
            {{ row.status === 'active' ? '正常' : '已封禁' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="noteCount" label="笔记数" width="80" />
      <el-table-column prop="followerCount" label="粉丝数" width="80" />

      <el-table-column prop="createdAt" label="注册时间" width="150" />

      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="viewUser(row)">查看</el-button>
          
          <el-button
            v-if="row.status === 'active'"
            link
            type="danger"
            @click="banUser(row)"
          >
            封禁
          </el-button>
          
          <el-button
            v-else
            link
            type="success"
            @click="unbanUser(row)"
          >
            解封
          </el-button>
          
          <el-button link type="primary" @click="editUser(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
      />
    </div>

    <!-- 用户详情弹窗 -->
    <el-dialog v-model="userDialogVisible" title="用户信息" width="500px">
      <div v-if="selectedUser" class="user-detail">
        <div class="detail-header">
          <el-avatar :size="80" :src="selectedUser.avatar">
            {{ selectedUser.nickname?.charAt(0) }}
          </el-avatar>
          <div class="header-info">
            <h3>{{ selectedUser.nickname }}</h3>
            <p>{{ selectedUser.email }}</p>
          </div>
        </div>

        <div class="detail-stats">
          <div class="stat">
            <span>{{ selectedUser.noteCount }}</span>
            <label>笔记</label>
          </div>
          <div class="stat">
            <span>{{ selectedUser.followerCount }}</span>
            <label>粉丝</label>
          </div>
          <div class="stat">
            <span>{{ selectedUser.followingCount }}</span>
            <label>关注</label>
          </div>
        </div>

        <div class="detail-info">
          <div class="info-row">
            <label>注册时间：</label>
            <span>{{ selectedUser.createdAt }}</span>
          </div>
          <div class="info-row">
            <label>最后登录：</label>
            <span>{{ selectedUser.lastLoginAt }}</span>
          </div>
          <div class="info-row">
            <label>简介：</label>
            <span>{{ selectedUser.bio || '暂无简介' }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="userDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="viewUserNotes">查看笔记</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { adminApi, userApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

const searchQuery = ref('')
const filterStatus = ref('all')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(100)
const loading = ref(false)
const userDialogVisible = ref(false)
const selectedUser = ref(null)

const users = ref([
  {
    id: 1,
    nickname: '生物研究员小王',
    email: 'wang@example.com',
    avatar: '',
    role: 'user',
    status: 'active',
    noteCount: 42,
    followerCount: 256,
    followingCount: 128,
    createdAt: '2023-06-15 10:30',
    lastLoginAt: '2024-01-15 09:20',
    bio: '专注肿瘤免疫研究',
  },
  {
    id: 2,
    nickname: '实验小能手',
    email: 'lab@example.com',
    avatar: '',
    role: 'user',
    status: 'active',
    noteCount: 28,
    followerCount: 189,
    followingCount: 76,
    createdAt: '2023-07-20 14:15',
    lastLoginAt: '2024-01-14 16:45',
    bio: '分享实验技巧',
  },
  {
    id: 3,
    nickname: '违规用户',
    email: 'spam@example.com',
    avatar: '',
    role: 'user',
    status: 'banned',
    noteCount: 0,
    followerCount: 0,
    followingCount: 0,
    createdAt: '2024-01-10 08:00',
    lastLoginAt: '2024-01-10 08:30',
    bio: '',
  },
])

const filteredUsers = computed(() => {
  return users.value.filter(user => {
    if (filterStatus.value !== 'all' && user.status !== filterStatus.value) {
      return false
    }
    if (searchQuery.value && !user.nickname.includes(searchQuery.value) && !user.email.includes(searchQuery.value)) {
      return false
    }
    return true
  })
})

const viewUser = (user) => {
  selectedUser.value = user
  userDialogVisible.value = true
}

const viewUserNotes = () => {
  router.push(`/user/${selectedUser.value.id}`)
  userDialogVisible.value = false
}

const banUser = async (user) => {
  try {
    await ElMessageBox.confirm(`确定要封禁用户 "${user.nickname}" 吗？`, '提示', {
      type: 'warning',
    })
    await adminApi.updateUserStatus(user.id, 'banned')
    user.status = 'banned'
    ElMessage.success('已封禁')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const unbanUser = async (user) => {
  try {
    await adminApi.updateUserStatus(user.id, 'active')
    user.status = 'active'
    ElMessage.success('已解封')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const editUser = (user) => {
  // 编辑用户
}
</script>

<style scoped>
.users-view {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
}

.filter-bar {
  margin-bottom: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-details {
  flex: 1;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.user-email {
  font-size: 12px;
  color: #999;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.user-detail {
  padding: 20px 0;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.header-info h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
}

.header-info p {
  font-size: 14px;
  color: #666;
}

.detail-stats {
  display: flex;
  gap: 40px;
  padding: 20px 0;
  border-top: 1px solid #eee;
  border-bottom: 1px solid #eee;
  margin-bottom: 20px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat span {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.stat label {
  font-size: 12px;
  color: #999;
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  gap: 12px;
}

.info-row label {
  color: #666;
  min-width: 80px;
}

.info-row span {
  color: #333;
}
</style>
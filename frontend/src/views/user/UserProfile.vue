<template>
  <div class="user-profile">
    <div class="profile-header">
      <div class="cover-image"></div>
      <div class="header-content">
        <div class="user-info">
          <el-avatar :size="100" :src="user.avatar">
            {{ user.nickname?.charAt(0) }}
          </el-avatar>
          <div class="info-text">
            <h2>{{ user.nickname }}</h2>
            <p class="bio">{{ user.bio || '这个人很懒，什么都没写~' }}</p>
            <div class="meta-info">
              <span>{{ user.location || '未知地区' }}</span>
              <span class="divider">|</span>
              <span>{{ formatDate(user.createdAt, 'YYYY-MM') }} 加入</span>
            </div>
          </div>
        </div>
        
        <div class="header-actions">
          <template v-if="isCurrentUser">
            <el-button @click="$router.push('/settings')">编辑资料</el-button>
          </template>
          <template v-else>
            <el-button
              type="primary"
              :class="{ 'is-followed': isFollowing }"
              @click="toggleFollow"
            >
              {{ isFollowing ? '已关注' : '+ 关注' }}
            </el-button>
            <el-button @click="sendMessage">私信</el-button>
          </template>
        </div>
      </div>
    </div>

    <div class="profile-stats">
      <div class="stat-item">
        <span class="stat-value">{{ user.noteCount || 0 }}</span>
        <span class="stat-label">笔记</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ user.followingCount || 0 }}</span>
        <span class="stat-label">关注</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ user.followerCount || 0 }}</span>
        <span class="stat-label">粉丝</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ user.likeCount || 0 }}</span>
        <span class="stat-label">获赞</span>
      </div>
    </div>

    <div class="profile-content">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="笔记" name="notes">
          <WaterfallLayout :items="userNotes" :columnCount="isMobile ? 2 : 4">
            <template #default="{ item }">
              <NoteCard :note="item" />
            </template>
          </WaterfallLayout>
          
          <div v-if="userNotes.length === 0" class="empty-state">
            <img src="/empty-notes.svg" alt="empty" />
            <p>还没有发布笔记</p>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="收藏" name="favorites">
          <WaterfallLayout :items="favoriteNotes" :columnCount="isMobile ? 2 : 4">
            <template #default="{ item }">
              <NoteCard :note="item" />
            </template>
          </WaterfallLayout>
          
          <div v-if="favoriteNotes.length === 0" class="empty-state">
            <img src="/empty-favorites.svg" alt="empty" />
            <p>还没有收藏笔记</p>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="赞过" name="liked">
          <WaterfallLayout :items="likedNotes" :columnCount="isMobile ? 2 : 4">
            <template #default="{ item }">
              <NoteCard :note="item" />
            </template>
          </WaterfallLayout>
          
          <div v-if="likedNotes.length === 0" class="empty-state">
            <img src="/empty-liked.svg" alt="empty" />
            <p>还没有点赞笔记</p>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { formatDate } from '@/utils'
import WaterfallLayout from '@/components/common/WaterfallLayout.vue'
import NoteCard from '@/components/note/NoteCard.vue'
import { userApi, noteApi } from '@/api'

const route = useRoute()
const userStore = useUserStore()
const appStore = useAppStore()

const isMobile = computed(() => appStore.isMobile)
const isCurrentUser = computed(() => userStore.currentUser?.id === route.params.id)

const user = ref({})
const activeTab = ref('notes')
const isFollowing = ref(false)
const userNotes = ref([])
const favoriteNotes = ref([])
const likedNotes = ref([])

// 模拟数据
user.value = {
  id: route.params.id,
  nickname: '生物研究员小王',
  avatar: '',
  bio: '专注肿瘤免疫研究 | 分享科研日常 | 欢迎交流',
  location: '上海',
  createdAt: new Date('2023-06-15'),
  noteCount: 42,
  followingCount: 128,
  followerCount: 256,
  likeCount: 1890,
}

userNotes.value = [
  {
    id: 1,
    title: 'CRISPR-Cas9 基因编辑技术的最新进展',
    summary: '本文综述了CRISPR-Cas9技术在基因治疗领域的最新应用...',
    coverImage: 'https://picsum.photos/300/400?random=1',
    author: user.value,
    tags: ['基因编辑', 'CRISPR'],
    viewCount: 1234,
    likeCount: 89,
    isLiked: false,
  },
  {
    id: 2,
    title: 'Western Blot 实验技巧分享',
    summary: '总结了我三年WB实验的经验...',
    coverImage: 'https://picsum.photos/300/350?random=2',
    author: user.value,
    tags: ['实验方法', 'Western Blot'],
    viewCount: 2345,
    likeCount: 156,
    isLiked: false,
  },
]

favoriteNotes.value = []
likedNotes.value = []

const toggleFollow = async () => {
  try {
    if (isFollowing.value) {
      await userApi.unfollowUser(user.value.id)
      isFollowing.value = false
      user.value.followerCount--
    } else {
      await userApi.followUser(user.value.id)
      isFollowing.value = true
      user.value.followerCount++
    }
  } catch (error) {
    console.error('关注操作失败')
  }
}

const sendMessage = () => {
  // 打开私信对话框
}

onMounted(async () => {
  // 加载用户详情
  // const res = await userApi.getUserById(route.params.id)
  // user.value = res.data
})
</script>

<style scoped>
.user-profile {
  min-height: 100vh;
  background: #f5f5f5;
}

.profile-header {
  position: relative;
  background: #fff;
}

.cover-image {
  height: 200px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px 24px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.user-info {
  display: flex;
  gap: 20px;
  margin-top: -50px;
}

.user-info :deep(.el-avatar) {
  border: 4px solid #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.info-text {
  padding-top: 50px;
}

.info-text h2 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.bio {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.meta-info {
  font-size: 13px;
  color: #999;
  display: flex;
  align-items: center;
  gap: 8px;
}

.divider {
  color: #ddd;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.is-followed {
  background: #f0f0f0;
  border-color: #f0f0f0;
  color: #999;
}

.profile-stats {
  display: flex;
  justify-content: center;
  gap: 60px;
  padding: 24px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.stat-label {
  font-size: 13px;
  color: #999;
}

.profile-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
}

.empty-state img {
  width: 120px;
  height: 120px;
  opacity: 0.5;
  margin-bottom: 16px;
}

.empty-state p {
  color: #999;
  font-size: 14px;
}

@media (max-width: 768px) {
  .cover-image {
    height: 120px;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .user-info {
    margin-top: -30px;
  }

  .user-info :deep(.el-avatar) {
    width: 80px !important;
    height: 80px !important;
  }

  .info-text {
    padding-top: 30px;
  }

  .profile-stats {
    gap: 30px;
    padding: 16px;
  }

  .profile-content {
    padding: 12px;
  }
}
</style>
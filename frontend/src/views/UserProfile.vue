<template>
  <div class="user-profile-container">
    <!-- 顶部导航 -->
    <header class="profile-header">
      <div class="header-left">
        <el-button icon="ArrowLeft" text @click="goBack">返回</el-button>
        <span class="header-username">{{ userInfo.username }}</span>
      </div>
      <div class="header-right">
        <el-button icon="Search" text>搜索</el-button>
        <el-button icon="MoreFilled" text>更多</el-button>
      </div>
    </header>

    <!-- 用户信息区 -->
    <div class="user-info-section">
      <div class="user-info-bg"></div>
      <div class="user-info-content">
        <!-- 头像 -->
        <div class="avatar-wrapper" @click="showAvatarPreview = true">
          <el-avatar 
            :size="80" 
            :src="userInfo.avatar"
            class="user-avatar"
          />
          <div class="avatar-edit-icon" v-if="isCurrentUser">
            <el-icon><Camera /></el-icon>
          </div>
        </div>
        
        <!-- 用户名和简介 -->
        <div class="user-meta">
          <h2 class="username">{{ userInfo.username }}</h2>
          <p class="user-bio">{{ userInfo.bio || '这个人很懒，还没有写简介~' }}</p>
          <div class="user-id">ID: {{ userInfo.id }}</div>
        </div>

        <!-- 统计数据 -->
        <div class="user-stats">
          <div class="stat-item">
            <span class="stat-value">{{ formatNumber(userStats.following) }}</span>
            <span class="stat-label">关注</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ formatNumber(userStats.followers) }}</span>
            <span class="stat-label">粉丝</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ formatNumber(userStats.likes) }}</span>
            <span class="stat-label">获赞</span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="user-actions">
          <template v-if="isCurrentUser">
            <el-button type="default" class="action-btn" @click="editProfile">
              <el-icon><Edit /></el-icon>编辑资料
            </el-button>
            <el-button type="default" class="action-btn" @click="showSettings">
              <el-icon><Setting /></el-icon>设置
            </el-button>
          </template>
          <template v-else>
            <el-button 
              :type="isFollowing ? 'default' : 'primary'" 
              class="action-btn follow-btn"
              @click="toggleFollow"
            >
              {{ isFollowing ? '已关注' : '关注' }}
            </el-button>
            <el-button type="default" class="action-btn" @click="sendMessage">
              <el-icon><ChatDotRound /></el-icon>私信
            </el-button>
          </template>
        </div>
      </div>
    </div>

    <!-- Tab切换栏 -->
    <div class="tab-section">
      <el-tabs v-model="activeTab" class="profile-tabs" @tab-change="handleTabChange">
        <el-tab-pane label="笔记" name="notes">
          <span class="tab-label">
            笔记
            <span class="tab-count">{{ userStats.noteCount }}</span>
          </span>
        </el-tab-pane>
        <el-tab-pane label="收藏" name="favorites">
          <span class="tab-label">
            收藏
            <span class="tab-count">{{ userStats.favoriteCount }}</span>
          </span>
        </el-tab-pane>
        <el-tab-pane label="点赞" name="likes">
          <span class="tab-label">
            点赞
            <span class="tab-count">{{ userStats.likeCount }}</span>
          </span>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 内容区 - 瀑布流 -->
    <div class="content-section">
      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="3" animated />
      </div>
      
      <div v-else-if="notes.length === 0" class="empty-state">
        <el-empty description="还没有内容" :image-size="120">
          <template #description>
            <span class="empty-text">还没有内容</span>
          </template>
        </el-empty>
      </div>
      
      <div v-else class="waterfall-container">
        <div class="waterfall-column" v-for="(column, colIndex) in columns" :key="colIndex">
          <NoteCard
            v-for="note in column"
            :key="note.id"
            :note="note"
            @click="goToDetail(note.id)"
            @like="handleLike"
          />
        </div>
      </div>

      <!-- 加载更多 -->
      <div class="loading-more" v-if="loadingMore">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
      
      <div class="no-more" v-if="!hasMore && notes.length > 0">
        <el-divider>没有更多了</el-divider>
      </div>
    </div>

    <!-- 头像预览对话框 -->
    <el-dialog
      v-model="showAvatarPreview"
      title="头像预览"
      width="400px"
      align-center
      destroy-on-close
      class="avatar-preview-dialog"
    >
      <div class="avatar-preview-content">
        <el-avatar :size="200" :src="userInfo.avatar" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Camera, Edit, Setting, ChatDotRound, Loading } from '@element-plus/icons-vue'
import NoteCard from '../components/NoteCard.vue'

const route = useRoute()
const router = useRouter()

// 当前用户ID（从URL参数获取）
const userId = computed(() => route.params.id)

// 当前登录用户ID（mock）
const currentUserId = ref('1')

// 是否当前用户的主页
const isCurrentUser = computed(() => userId.value === currentUserId.value)

// Tab状态
const activeTab = ref('notes')

// 加载状态
const loading = ref(false)
const loadingMore = ref(false)
const hasMore = ref(true)
const page = ref(1)
const pageSize = 10

// 头像预览
const showAvatarPreview = ref(false)

// 关注状态
const isFollowing = ref(false)

// 瀑布流列数
const columnCount = ref(2)

// 用户信息
const userInfo = ref({
  id: userId.value,
  username: '张博士',
  avatar: 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
  bio: '生物信息学研究员 | 专注于CRISPR和基因编辑领域 | 分享学术笔记，欢迎交流',
  email: 'zhang@example.com'
})

// 用户统计数据
const userStats = ref({
  following: 128,
  followers: 2560,
  likes: 15800,
  noteCount: 45,
  favoriteCount: 128,
  likeCount: 356
})

// 笔记列表
const notes = ref([])

// 将笔记分配到各列（瀑布流布局）
const columns = computed(() => {
  const cols = Array.from({ length: columnCount.value }, () => [])
  notes.value.forEach((note, index) => {
    cols[index % columnCount.value].push(note)
  })
  return cols
})

// Mock用户数据映射
const mockUserData = {
  '1': {
    username: '张博士',
    avatar: 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
    bio: '生物信息学研究员 | 专注于CRISPR和基因编辑领域 | 分享学术笔记，欢迎交流',
    stats: { following: 128, followers: 2560, likes: 15800, noteCount: 45, favoriteCount: 128, likeCount: 356 }
  },
  '2': {
    username: '李研究员',
    avatar: 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png',
    bio: '分子生物学博士 | 蛋白质结构预测 | AlphaFold爱好者',
    stats: { following: 89, followers: 1200, likes: 8900, noteCount: 28, favoriteCount: 67, likeCount: 234 }
  },
  '3': {
    username: '王教授',
    avatar: 'https://cube.elemecdn.com/9/9f/9f5c5f5c5f5c5f5c5f5c5f5c5f5c5f5c.png',
    bio: '清华大学生命科学学院教授 | 主要研究方向：细胞信号转导',
    stats: { following: 56, followers: 8900, likes: 45600, noteCount: 78, favoriteCount: 234, likeCount: 567 }
  }
}

// 生成Mock笔记数据
const generateMockNotes = (pageNum, size, type) => {
  const titles = [
    'CRISPR-Cas9技术在基因编辑中的最新进展',
    'AlphaFold2预测蛋白质结构的突破性研究',
    'mRNA疫苗技术原理与临床应用综述',
    '单细胞测序技术在肿瘤研究中的应用',
    '肠道微生物组与代谢疾病关联性研究',
    'CAR-T细胞疗法治疗血液肿瘤的临床进展',
    '人工智能在药物发现中的应用前景',
    '线粒体功能障碍与神经退行性疾病',
    '表观遗传学调控在癌症发生中的作用',
    '干细胞治疗心脏病的最新临床试验结果'
  ]

  const mockNotes = []
  const baseCount = type === 'notes' ? userStats.value.noteCount : 
                    type === 'favorites' ? userStats.value.favoriteCount : 
                    userStats.value.likeCount
  
  const startIndex = (pageNum - 1) * size
  const endIndex = Math.min(startIndex + size, baseCount)
  
  for (let i = startIndex; i < endIndex; i++) {
    mockNotes.push({
      id: `${userId.value}_${type}_${i + 1}`,
      title: titles[Math.floor(Math.random() * titles.length)],
      author: userInfo.value.username,
      authorAvatar: userInfo.value.avatar,
      authorId: userId.value,
      cover: Math.random() > 0.3 ? `https://picsum.photos/300/${400 + Math.floor(Math.random() * 200)}?random=${userId.value}_${i}` : null,
      likes: Math.floor(Math.random() * 1000) + 10,
      favorites: Math.floor(Math.random() * 500) + 5,
      comments: Math.floor(Math.random() * 100) + 1,
      isLiked: type === 'likes' || Math.random() > 0.7,
      isFavorited: type === 'favorites' || Math.random() > 0.8
    })
  }
  
  return { notes: mockNotes, hasMore: endIndex < baseCount }
}

// 格式化数字
const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

// 获取用户信息
const fetchUserInfo = async () => {
  // Mock：根据用户ID获取用户信息
  const mockData = mockUserData[userId.value] || mockUserData['1']
  userInfo.value = {
    id: userId.value,
    username: mockData.username,
    avatar: mockData.avatar,
    bio: mockData.bio,
    email: `${mockData.username}@example.com`
  }
  userStats.value = mockData.stats
}

// 获取笔记列表
const fetchNotes = async (isLoadMore = false) => {
  if (isLoadMore) {
    loadingMore.value = true
  } else {
    loading.value = true
    page.value = 1
    notes.value = []
  }

  try {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const { notes: newNotes, hasMore: more } = generateMockNotes(page.value, pageSize, activeTab.value)
    
    hasMore.value = more
    
    if (isLoadMore) {
      notes.value.push(...newNotes)
    } else {
      notes.value = newNotes
    }
    
    page.value++
  } catch (error) {
    ElMessage.error('加载失败，请重试')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// Tab切换
const handleTabChange = (tabName) => {
  fetchNotes()
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 跳转到笔记详情
const goToDetail = (noteId) => {
  router.push(`/note/${noteId}`)
}

// 点赞
const handleLike = (noteId) => {
  const note = notes.value.find(n => n.id === noteId)
  if (note) {
    note.isLiked = !note.isLiked
    note.likes += note.isLiked ? 1 : -1
  }
}

// 关注/取消关注
const toggleFollow = () => {
  isFollowing.value = !isFollowing.value
  ElMessage.success(isFollowing.value ? '已关注' : '已取消关注')
}

// 发送私信
const sendMessage = () => {
  ElMessage.info('私信功能开发中...')
}

// 编辑资料
const editProfile = () => {
  ElMessage.info('编辑资料功能开发中...')
}

// 设置
const showSettings = () => {
  ElMessage.info('设置功能开发中...')
}

// 响应式列数
const updateColumnCount = () => {
  const width = window.innerWidth
  if (width < 768) {
    columnCount.value = 1
  } else if (width < 1200) {
    columnCount.value = 2
  } else {
    columnCount.value = 3
  }
}

// 滚动加载
const handleScroll = () => {
  const scrollTop = window.pageYOffset || document.documentElement.scrollTop
  const windowHeight = window.innerHeight
  const documentHeight = document.documentElement.scrollHeight
  
  if (documentHeight - scrollTop - windowHeight < 100 && !loadingMore.value && hasMore.value) {
    fetchNotes(true)
  }
}

// 监听用户ID变化
watch(() => userId.value, () => {
  fetchUserInfo()
  fetchNotes()
}, { immediate: true })

onMounted(() => {
  fetchUserInfo()
  fetchNotes()
  updateColumnCount()
  window.addEventListener('resize', updateColumnCount)
  window.addEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.user-profile-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 40px;
}

/* 顶部导航 */
.profile-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  z-index: 100;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-username {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.header-right {
  display: flex;
  gap: 8px;
}

/* 用户信息区 */
.user-info-section {
  position: relative;
  padding-top: 56px;
}

.user-info-bg {
  position: absolute;
  top: 56px;
  left: 0;
  right: 0;
  height: 180px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  border-radius: 0 0 24px 24px;
}

.user-info-content {
  position: relative;
  padding: 20px;
  padding-top: 80px;
  background: #fff;
  margin: 0 16px;
  margin-top: 80px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

/* 头像 */
.avatar-wrapper {
  position: absolute;
  top: -40px;
  left: 50%;
  transform: translateX(-50%);
  cursor: pointer;
  transition: transform 0.3s ease;
}

.avatar-wrapper:hover {
  transform: translateX(-50%) scale(1.05);
}

.user-avatar {
  border: 4px solid #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.avatar-edit-icon {
  position: absolute;
  bottom: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  background: #ff2442;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  border: 2px solid #fff;
}

/* 用户元信息 */
.user-meta {
  text-align: center;
  margin-bottom: 20px;
}

.username {
  font-size: 22px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 8px;
}

.user-bio {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
  margin-bottom: 8px;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

.user-id {
  font-size: 12px;
  color: #999;
}

/* 统计数据 */
.user-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-bottom: 20px;
  padding: 16px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: opacity 0.2s;
}

.stat-item:hover {
  opacity: 0.7;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.stat-label {
  font-size: 13px;
  color: #999;
  margin-top: 4px;
}

/* 操作按钮 */
.user-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.action-btn {
  min-width: 120px;
  border-radius: 20px;
  font-weight: 500;
}

.action-btn :deep(.el-icon) {
  margin-right: 4px;
}

.follow-btn {
  background: #ff2442;
  border-color: #ff2442;
}

.follow-btn:hover {
  background: #e0203c;
  border-color: #e0203c;
}

/* Tab栏 */
.tab-section {
  margin-top: 16px;
  background: #fff;
  padding: 0 16px;
}

.profile-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}

.profile-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #f0f0f0;
}

.profile-tabs :deep(.el-tabs__active-bar) {
  background-color: #ff2442;
  height: 3px;
}

.profile-tabs :deep(.el-tabs__item) {
  font-size: 15px;
  color: #666;
  padding: 0 24px;
}

.profile-tabs :deep(.el-tabs__item.is-active) {
  color: #1a1a1a;
  font-weight: 600;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tab-count {
  font-size: 12px;
  color: #999;
  background: #f5f5f5;
  padding: 2px 8px;
  border-radius: 10px;
}

/* 内容区 */
.content-section {
  padding: 16px;
}

.waterfall-container {
  display: flex;
  gap: 16px;
  max-width: 1200px;
  margin: 0 auto;
}

.waterfall-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 加载状态 */
.loading-state {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 16px;
}

.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #999;
  font-size: 14px;
}

.loading-icon {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 空状态 */
.empty-state {
  padding: 60px 20px;
}

.empty-text {
  font-size: 14px;
  color: #999;
}

/* 没有更多 */
.no-more {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 16px;
  color: #999;
}

/* 头像预览对话框 */
.avatar-preview-dialog :deep(.el-dialog__body) {
  display: flex;
  justify-content: center;
  padding: 20px;
}

.avatar-preview-content .el-avatar {
  border: 4px solid #f5f5f5;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .user-info-content {
    margin: 0 12px;
    margin-top: 80px;
    padding: 16px;
    padding-top: 60px;
  }
  
  .username {
    font-size: 20px;
  }
  
  .user-bio {
    font-size: 13px;
  }
  
  .user-stats {
    gap: 24px;
  }
  
  .stat-value {
    font-size: 18px;
  }
  
  .action-btn {
    min-width: 100px;
    padding: 8px 16px;
  }
  
  .waterfall-container {
    gap: 12px;
    padding: 0;
  }
  
  .content-section {
    padding: 12px;
  }
}

@media (max-width: 480px) {
  .user-stats {
    gap: 16px;
  }
  
  .user-actions {
    flex-wrap: wrap;
  }
  
  .action-btn {
    flex: 1;
    min-width: unset;
  }
}
</style>

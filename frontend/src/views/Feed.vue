<template>
  <div class="feed-container">
    <!-- 顶部导航 -->
    <header class="feed-header">
      <div class="logo">ProteinHub</div>
      <div class="search-box">
        <el-input
          v-model="searchQuery"
          placeholder="搜索学术笔记..."
          prefix-icon="Search"
          clearable
          @keyup.enter="handleSearch"
        />
      </div>
      <div class="header-actions">
        <el-button type="primary" icon="Plus" @click="createNote">发布笔记</el-button>
        <router-link :to="'/user/' + currentUserId">
          <el-avatar :size="40" :src="userAvatar" />
        </router-link>
      </div>
    </header>

    <!-- 瀑布流内容区 -->
    <main class="feed-content" ref="feedContent" @scroll="handleScroll">
      <div class="waterfall-container">
        <div class="waterfall-column" v-for="(column, colIndex) in columns" :key="colIndex">
          <NoteCard
            v-for="note in column"
            :key="note.id"
            :note="note"
            @click="goToDetail(note.id)"
          />
        </div>
      </div>
      
      <!-- 加载状态 -->
      <div class="loading-state" v-if="loading">
        <el-skeleton :rows="3" animated />
      </div>
      
      <div class="no-more" v-if="!hasMore && notes.length > 0">
        <el-divider>没有更多了</el-divider>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import NoteCard from '../components/NoteCard.vue'

const router = useRouter()

// 当前用户ID
const currentUserId = ref('1')

// 状态
const searchQuery = ref('')
const notes = ref([])
const loading = ref(false)
const hasMore = ref(true)
const page = ref(1)
const pageSize = 10
const userAvatar = ref('https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png')

// 瀑布流列数（响应式）
const columnCount = ref(2)

// 将笔记分配到各列
const columns = computed(() => {
  const cols = Array.from({ length: columnCount.value }, () => [])
  notes.value.forEach((note, index) => {
    cols[index % columnCount.value].push(note)
  })
  return cols
})

// Mock数据生成
const generateMockNotes = (pageNum, size) => {
  const mockNotes = []
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
  
  const authors = ['张博士', '李研究员', '王教授', '陈学者', '刘博士', '赵研究员']
  
  for (let i = 0; i < size; i++) {
    const id = (pageNum - 1) * size + i + 1
    mockNotes.push({
      id: id,
      title: titles[Math.floor(Math.random() * titles.length)],
      author: authors[Math.floor(Math.random() * authors.length)],
      authorId: Math.floor(Math.random() * 3) + 1,
      authorAvatar: `https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png`,
      cover: Math.random() > 0.3 ? `https://picsum.photos/300/${400 + Math.floor(Math.random() * 200)}?random=${id}` : null,
      likes: Math.floor(Math.random() * 1000) + 10,
      favorites: Math.floor(Math.random() * 500) + 5,
      comments: Math.floor(Math.random() * 100) + 1,
      isLiked: false,
      isFavorited: false
    })
  }
  return mockNotes
}

// 从localStorage获取当前用户ID
const getCurrentUserId = () => {
  try {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      const user = JSON.parse(userStr)
      return user.id
    }
  } catch (e) {
    console.error('Failed to parse user from localStorage:', e)
  }
  // 如果没有登录，返回null（后端会返回热度排序）
  return null
}

// API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'

// 获取笔记列表（支持个性化推荐）
const fetchNotes = async () => {
  if (loading.value || !hasMore.value) return
  
  loading.value = true
  try {
    const userId = getCurrentUserId()
    
    // 构建请求URL（如果用户已登录，添加user_id参数）
    let url = `${API_BASE_URL}/notes/feed?page=${page.value}&per_page=${pageSize}`
    if (userId) {
      url += `&user_id=${userId}`
    }
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const result = await response.json()
    
    if (result.success) {
      const newNotes = result.data.items || []
      const pagination = result.data.pagination
      
      // 转换后端数据格式为前端格式
      const formattedNotes = newNotes.map(note => ({
        id: note.id,
        title: note.title,
        preview: note.preview,
        author: note.author?.username || '匿名用户',
        authorId: note.author?.id,
        authorAvatar: note.author?.avatar_url || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
        cover: null, // 笔记封面（如果有）
        likes: note.like_count || 0,
        favorites: note.favorite_count || 0,
        comments: note.comment_count || 0,
        tags: note.tags || [],
        isLiked: note.is_liked || false,
        isFavorited: note.is_favorited || false,
        createdAt: note.created_at
      }))
      
      if (formattedNotes.length < pageSize || !pagination?.has_next) {
        hasMore.value = false
      }
      
      notes.value.push(...formattedNotes)
      page.value++
    } else {
      throw new Error(result.error || '获取数据失败')
    }
  } catch (error) {
    console.error('Fetch error:', error)
    ElMessage.error('加载失败，请重试')
    // 如果API失败，使用Mock数据作为降级方案
    if (notes.value.length === 0) {
      const mockNotes = generateMockNotes(page.value, pageSize)
      notes.value.push(...mockNotes)
      page.value++
    }
  } finally {
    loading.value = false
  }
}

// 滚动加载
const handleScroll = (e) => {
  const { scrollTop, scrollHeight, clientHeight } = e.target
  if (scrollHeight - scrollTop - clientHeight < 100) {
    fetchNotes()
  }
}

// 搜索
const handleSearch = () => {
  ElMessage.info(`搜索: ${searchQuery.value}`)
  // 实际项目中这里会调用搜索API
}

// 创建笔记
const createNote = () => {
  ElMessage.info('发布笔记功能开发中...')
}

// 跳转到详情页
const goToDetail = (id) => {
  router.push(`/note/${id}`)
}

// 跳转到个人主页
const goToProfile = () => {
  router.push('/user/' + currentUserId.value)
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

onMounted(() => {
  fetchNotes()
  updateColumnCount()
  window.addEventListener('resize', updateColumnCount)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateColumnCount)
})
</script>

<style scoped>
.feed-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.feed-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  z-index: 100;
}

.logo {
  font-size: 24px;
  font-weight: bold;
  color: #ff2442;
  cursor: pointer;
}

.search-box {
  flex: 1;
  max-width: 500px;
  margin: 0 24px;
}

.search-box :deep(.el-input__wrapper) {
  border-radius: 20px;
  background: #f5f7fa;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-actions .el-avatar {
  cursor: pointer;
}

.feed-content {
  padding-top: 80px;
  padding-bottom: 40px;
  min-height: 100vh;
  overflow-y: auto;
}

.waterfall-container {
  display: flex;
  gap: 16px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
}

.waterfall-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.loading-state {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 16px;
}

.no-more {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 16px;
  color: #999;
}

@media (max-width: 768px) {
  .feed-header {
    padding: 0 12px;
  }
  
  .search-box {
    margin: 0 12px;
  }
  
  .waterfall-container {
    padding: 0 12px;
    gap: 12px;
  }
}
</style>

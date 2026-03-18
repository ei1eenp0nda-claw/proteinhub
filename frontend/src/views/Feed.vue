<template>
  <div class="feed-container">
    <!-- 顶部导航 -->
    <header class="feed-header">
      <div class="logo" @click="refreshFeed">ProteinHub</div>
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
import { loadNotesData } from '../config/dataSource.js'

defineOptions({
  name: 'Feed'
})

const router = useRouter()

// 状态
const searchQuery = ref('')
const notes = ref([])
const loading = ref(false)
const hasMore = ref(true)
const page = ref(1)
const pageSize = 10
const allNotes = ref([])  // 存储所有高清笔记
const userAvatar = ref('https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png')
const currentUserId = ref('1')
const feedContent = ref(null)

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

// 解析markdown内容，提取标题和预览
const parseNoteContent = (content) => {
  if (!content) return { title: '', preview: '' }
  
  // 提取第一行作为标题（通常是 # 开头）
  const lines = content.split('\n').filter(line => line.trim())
  let title = ''
  let preview = ''
  
  for (const line of lines) {
    const trimmed = line.trim()
    if (trimmed.startsWith('# ')) {
      title = trimmed.replace(/^#\s*/, '')
    } else if (trimmed.startsWith('## ')) {
      continue  // 跳过副标题
    } else if (trimmed.length > 20 && !preview) {
      // 找到第一段有意义的文字作为预览
      preview = trimmed.substring(0, 100) + (trimmed.length > 100 ? '...' : '')
    }
    
    if (title && preview) break
  }
  
  return { title, preview }
}

// 从本地JSON加载高清笔记
const loadHighQualityNotes = async () => {
  // 初始化加载第一页
  page.value = 1
  notes.value = []
  hasMore.value = true
  await loadMoreNotes()
}

// 加载更多笔记（分页）
const loadMoreNotes = async () => {
  if (loading.value || !hasMore.value) return
  
  loading.value = true
  try {
    const { notes: newNotes, hasMore: more } = await loadNotesData(page.value, pageSize)
    
    if (newNotes.length > 0) {
      notes.value.push(...newNotes)
      page.value++
    }
    
    hasMore.value = more
  } catch (error) {
    console.error('加载笔记失败:', error)
  } finally {
    loading.value = false
  }
}

// 刷新Feed
const refreshFeed = () => {
  notes.value = []
  page.value = 1
  hasMore.value = true
  if (feedContent.value) {
    feedContent.value.scrollTop = 0
  }
  loadMoreNotes()
}

// 滚动加载
const handleScroll = (e) => {
  const { scrollTop, scrollHeight, clientHeight } = e.target
  if (scrollHeight - scrollTop - clientHeight < 100 && !loading.value && hasMore.value) {
    loadMoreNotes()
  }
}

// 搜索
const handleSearch = () => {
  if (!searchQuery.value.trim()) return
  
  const query = searchQuery.value.toLowerCase()
  const filtered = allNotes.value.filter(note => 
    note.title.toLowerCase().includes(query) ||
    note.preview.toLowerCase().includes(query) ||
    note.content.toLowerCase().includes(query)
  )
  
  notes.value = filtered.slice(0, 20)
  hasMore.value = false
}

// 创建笔记
const createNote = () => {
  ElMessage.info('发布笔记功能开发中...')
}

// 跳转到详情页
const goToDetail = (id) => {
  router.push(`/note/${id}`)
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
  loadHighQualityNotes()
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
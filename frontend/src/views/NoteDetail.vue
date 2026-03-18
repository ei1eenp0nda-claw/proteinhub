<template>
  <div class="note-detail-container">
    <!-- 顶部导航 -->
    <header class="detail-header">
      <div class="header-left">
        <el-button icon="ArrowLeft" text @click="goBack">返回</el-button>
        <span class="header-title">笔记详情</span>
      </div>
      <div class="header-right">
        <el-button icon="Share" text>分享</el-button>
        <el-button icon="MoreFilled" text>更多</el-button>
      </div>
    </header>

    <div class="detail-content" v-if="noteLoaded">
      <!-- 左侧内容区 -->
      <div class="content-main">
        <!-- 作者信息 -->
        <div class="author-section">
          <div class="author-link">
            <el-avatar :size="48" :src="note.authorAvatar" />
            <div class="author-info">
              <div class="author-name">{{ note.author }}</div>
              <div class="publish-time">{{ note.publishTime }}</div>
            </div>
          </div>
        </div>

        <!-- 笔记标题 -->
        <h1 class="note-title">{{ note.title }}</h1>

        <!-- 笔记正文 -->
        <div class="note-body" v-html="renderedContent"></div>

        <!-- 标签 -->
        <div class="note-tags" v-if="note.tags && note.tags.length">
          <el-tag v-for="tag in note.tags" :key="tag" size="small" effect="plain">
            {{ tag }}
          </el-tag>
        </div>

        <!-- 发布时间 -->
        <div class="note-meta">
          <span>发布于 {{ note.publishTime }}</span>
        </div>

        <!-- 互动按钮 -->
        <InteractionBar 
          :likes="note.likes"
          :favorites="note.favorites"
          :comments="note.comments"
          :is-liked="note.isLiked"
          :is-favorited="note.isFavorited"
          @like="handleLike"
          @favorite="handleFavorite"
          @comment="focusComment"
        />

        <!-- 评论区 -->
        <CommentSection 
          ref="commentSection"
          :comments="comments"
          @submit="handleCommentSubmit"
          @reply="handleReply"
        />
      </div>
    </div>

    <!-- 加载中 -->
    <div v-else-if="loading" class="loading-state">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- 笔记不存在 -->
    <div v-else class="error-state">
      <el-empty description="笔记不存在或已被删除" />
      <el-button @click="goBack">返回首页</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import InteractionBar from '../components/InteractionBar.vue'
import CommentSection from '../components/CommentSection.vue'
import { loadNoteDetail } from '../config/dataSource.js'

const route = useRoute()
const router = useRouter()

// 状态
const loading = ref(true)
const noteLoaded = ref(false)
const commentSection = ref(null)
const allNotes = ref([])

// 当前笔记
const note = ref({
  id: '',
  title: '',
  author: 'ProteinHub',
  authorAvatar: 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
  publishTime: '',
  content: '',
  tags: [],
  likes: 0,
  favorites: 0,
  comments: 0,
  isLiked: false,
  isFavorited: false
})

// 评论数据
const comments = ref([])

// 从 markdown 内容提取标题
const extractTitle = (content) => {
  if (!content) return '学术笔记'
  const match = content.match(/^#\s+(.+)$/m)
  return match ? match[1].trim() : '学术笔记'
}

// 加载笔记数据
const fetchNoteDetail = async () => {
  loading.value = true
  noteLoaded.value = false
  
  try {
    const noteId = route.params.id
    
    // 使用配置化的数据源加载单篇笔记
    const targetNote = await loadNoteDetail(noteId)
    
    if (targetNote) {
      note.value = {
        id: targetNote.id || noteId,
        title: targetNote.title || extractTitle(targetNote.content),
        content: targetNote.content,
        author: targetNote.author || 'ProteinHub',
        authorAvatar: targetNote.authorAvatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
        publishTime: new Date().toLocaleString('zh-CN'),
        tags: targetNote.tags || ['科研', '生物'],
        likes: targetNote.likes || Math.floor(Math.random() * 500) + 10,
        favorites: targetNote.favorites || Math.floor(Math.random() * 200) + 5,
        comments: targetNote.comments || Math.floor(Math.random() * 100) + 1,
        isLiked: false,
        isFavorited: false
      }
      noteLoaded.value = true
    } else {
      noteLoaded.value = false
    }
  } catch (error) {
    console.error('加载笔记失败:', error)
    noteLoaded.value = false
  } finally {
    loading.value = false
  }
}

// Markdown渲染（简单实现）
const renderedContent = computed(() => {
  let content = note.value.content
  if (!content) return ''
  
  // 转换标题
  content = content.replace(/^###\s+(.+)$/gim, '<h3>$1</h3>')
  content = content.replace(/^##\s+(.+)$/gim, '<h2>$1</h2>')
  content = content.replace(/^#\s+(.+)$/gim, '<h1>$1</h1>')
  
  // 转换加粗
  content = content.replace(/\*\*(.+)\*\*/gim, '<strong>$1</strong>')
  
  // 转换列表
  content = content.replace(/^-\s+(.+)$/gim, '<li>$1</li>')
  
  // 包裹列表
  content = content.replace(/(<li>.+<\/li>\n?)+/g, '<ul>$1</ul>')
  
  // 转换段落（按行处理）
  const lines = content.split('\n')
  const result = []
  let inParagraph = false
  
  for (let line of lines) {
    const trimmed = line.trim()
    
    // 跳过空行
    if (!trimmed) {
      if (inParagraph) {
        result.push('</p>')
        inParagraph = false
      }
      continue
    }
    
    // 已经是标签的行直接添加
    if (trimmed.startsWith('<')) {
      if (inParagraph) {
        result.push('</p>')
        inParagraph = false
      }
      result.push(line)
      continue
    }
    
    // 普通文本
    if (!inParagraph) {
      result.push('<p>')
      inParagraph = true
    }
    result.push(line)
  }
  
  if (inParagraph) {
    result.push('</p>')
  }
  
  return result.join('\n')
})

// 返回上一页
const goBack = () => {
  router.back()
}

// 点赞
const handleLike = () => {
  note.value.isLiked = !note.value.isLiked
  note.value.likes += note.value.isLiked ? 1 : -1
}

// 收藏
const handleFavorite = () => {
  note.value.isFavorited = !note.value.isFavorited
  note.value.favorites += note.value.isFavorited ? 1 : -1
  ElMessage.success(note.value.isFavorited ? '已收藏' : '已取消收藏')
}

// 聚焦评论框
const focusComment = () => {
  commentSection.value?.focusInput()
}

// 提交评论
const handleCommentSubmit = (content) => {
  const newComment = {
    id: Date.now(),
    author: '我',
    avatar: 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png',
    content: content,
    time: '刚刚',
    likes: 0,
    isLiked: false,
    replies: []
  }
  comments.value.unshift(newComment)
  note.value.comments++
  ElMessage.success('评论发布成功')
}

// 回复评论
const handleReply = ({ commentId, content }) => {
  const comment = comments.value.find(c => c.id === commentId)
  if (comment) {
    comment.replies.push({
      id: Date.now(),
      author: '我',
      avatar: 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png',
      content: content,
      time: '刚刚',
      likes: 0,
      isLiked: false,
      replyTo: comment.author
    })
    note.value.comments++
    ElMessage.success('回复成功')
  }
}

onMounted(() => {
  fetchNoteDetail()
})
</script>

<style scoped>
.note-detail-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.detail-header {
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

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.header-right {
  display: flex;
  gap: 8px;
}

.detail-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 80px 20px 40px;
}

.content-main {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.author-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.author-link {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  flex: 1;
}

.author-info {
  flex: 1;
}

.author-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.publish-time {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.note-title {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
  margin-bottom: 20px;
}

.note-body {
  font-size: 15px;
  line-height: 1.8;
  color: #333;
}

.note-body :deep(h1) {
  font-size: 22px;
  font-weight: 600;
  margin: 28px 0 16px;
  color: #1a1a1a;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
}

.note-body :deep(h2) {
  font-size: 18px;
  font-weight: 600;
  margin: 24px 0 12px;
  color: #1a1a1a;
}

.note-body :deep(h3) {
  font-size: 16px;
  font-weight: 600;
  margin: 20px 0 10px;
  color: #1a1a1a;
}

.note-body :deep(p) {
  margin-bottom: 16px;
}

.note-body :deep(ul) {
  margin: 16px 0;
  padding-left: 24px;
}

.note-body :deep(li) {
  margin-bottom: 8px;
}

.note-body :deep(strong) {
  font-weight: 600;
  color: #1a1a1a;
}

.note-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 24px 0;
}

.note-meta {
  font-size: 13px;
  color: #999;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.loading-state {
  max-width: 800px;
  margin: 80px auto 0;
  padding: 24px;
}

.error-state {
  max-width: 400px;
  margin: 120px auto 0;
  text-align: center;
}

@media (max-width: 768px) {
  .detail-content {
    padding: 80px 12px 20px;
  }
  
  .content-main {
    padding: 16px;
  }
  
  .note-title {
    font-size: 20px;
  }
  
  .note-body {
    font-size: 14px;
  }
}
</style>
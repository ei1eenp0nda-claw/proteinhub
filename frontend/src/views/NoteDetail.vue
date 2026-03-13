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

    <div class="detail-content">
      <!-- 左侧内容区 -->
      <div class="content-main">
        <!-- 作者信息 -->
        <div class="author-section">
          <router-link :to="'/user/' + note.authorId" class="author-link">
            <el-avatar :size="48" :src="note.authorAvatar" />
            <div class="author-info">
              <div class="author-name">{{ note.author }}</div>
              <div class="publish-time">{{ note.publishTime }}</div>
            </div>
          </router-link>
          <el-button 
            :type="isFollowing ? 'default' : 'primary'" 
            @click="toggleFollow"
            class="follow-btn"
          >
            {{ isFollowing ? '已关注' : '关注' }}
          </el-button>
        </div>

        <!-- 笔记标题 -->
        <h1 class="note-title">{{ note.title }}</h1>

        <!-- 笔记正文 -->
        <div class="note-body" v-html="renderedContent"></div>

        <!-- 原文信息 -->
        <div class="source-info" v-if="note.source">
          <el-divider content-position="left">原文信息</el-divider>
          <div class="source-card">
            <div class="source-title">{{ note.source.title }}</div>
            <div class="source-meta">
              <span class="source-journal">{{ note.source.journal }}</span>
              <span class="source-year">{{ note.source.year }}</span>
              <span class="source-citations">被引 {{ note.source.citations }} 次</span>
            </div>
            <div class="source-authors">{{ note.source.authors }}</div>
            <el-link type="primary" :href="note.source.url" target="_blank">
              查看原文 <el-icon><ArrowRight /></el-icon>
            </el-link>
          </div>
        </div>

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

      <!-- 右侧相关推荐 -->
      <aside class="content-sidebar">
        <div class="sidebar-section">
          <h3>相关笔记推荐</h3>
          <div class="related-notes">
            <div 
              v-for="related in relatedNotes" 
              :key="related.id"
              class="related-item"
              @click="goToRelated(related.id)"
            >
              <div class="related-cover" v-if="related.cover">
                <img :src="related.cover" :alt="related.title">
              </div>
              <div class="related-info">
                <div class="related-title">{{ related.title }}</div>
                <div class="related-author">{{ related.author }}</div>
                <div class="related-stats">
                  <span><el-icon><Star /></el-icon> {{ related.likes }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import InteractionBar from '../components/InteractionBar.vue'
import CommentSection from '../components/CommentSection.vue'

const route = useRoute()
const router = useRouter()
const noteId = computed(() => route.params.id)

// 状态
const isFollowing = ref(false)
const commentSection = ref(null)

// Mock笔记数据
const note = ref({
  id: noteId.value,
  title: 'CRISPR-Cas9技术在基因编辑中的最新进展',
  author: '张博士',
  authorId: '1',
  authorAvatar: 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
  publishTime: '2024-03-10 14:30',
  content: `# CRISPR-Cas9技术概述

CRISPR-Cas9（规律成簇的间隔短回文重复序列及其相关蛋白9）是一种革命性的基因编辑技术，被誉为"基因剪刀"。

## 技术原理

CRISPR-Cas9系统主要由两部分组成：
1. **Cas9蛋白**：一种能够切割DNA的核酸酶
2. **sgRNA（单链向导RNA）**：引导Cas9蛋白到达特定基因位点

## 最新研究进展

### 1. 碱基编辑技术
2023年，研究人员开发了更精确的碱基编辑器，可以在不切断DNA双链的情况下实现单碱基替换，大大降低了脱靶效应。

### 2.  Prime Editing（先导编辑）
David Liu团队开发的先导编辑技术能够实现所有类型的碱基替换，以及小片段的插入和删除，精度更高。

### 3. 临床应用突破
- **地中海贫血**：2023年有多项临床试验显示积极结果
- **遗传性失明**：EDIT-101在临床试验中显示出安全性
- **癌症免疫治疗**：CRISPR改造的CAR-T细胞疗法获批上市

## 技术挑战与展望

尽管CRISPR-Cas9技术取得了巨大进展，但仍面临一些挑战：
- 脱靶效应的完全消除
- 体内递送效率的提升
- 伦理和监管问题

未来，随着技术的不断完善，CRISPR有望在遗传病治疗、农业育种、合成生物学等领域发挥更大作用。`,
  source: {
    title: 'CRISPR-Cas9: A Revolutionary Tool for Genome Editing',
    journal: 'Nature Reviews Molecular Cell Biology',
    year: '2023',
    citations: 12580,
    authors: 'Doudna JA, Charpentier E, et al.',
    url: 'https://www.nature.com/articles/crispr-review'
  },
  tags: ['CRISPR', '基因编辑', '生物技术', '医学进展'],
  likes: 1280,
  favorites: 456,
  comments: 89,
  isLiked: false,
  isFavorited: false
})

// Mock评论数据
const comments = ref([
  {
    id: 1,
    author: '李研究员',
    avatar: 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png',
    content: '总结得很全面！特别是碱基编辑和先导编辑的部分，这些新技术确实大大降低了脱靶风险。',
    time: '2小时前',
    likes: 24,
    isLiked: false,
    replies: [
      {
        id: 11,
        author: '张博士',
        avatar: 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
        content: '谢谢认可！确实，精准度是临床应用的关键。',
        time: '1小时前',
        likes: 8,
        isLiked: false,
        replyTo: '李研究员'
      }
    ]
  },
  {
    id: 2,
    author: '王教授',
    avatar: 'https://cube.elemecdn.com/9/9f/9f5c5f5c5f5c5f5c5f5c5f5c5f5c5f5c.png',
    content: '建议补充一下CRISPR在农业领域的应用，比如抗病作物的培育。',
    time: '5小时前',
    likes: 15,
    isLiked: false,
    replies: []
  },
  {
    id: 3,
    author: '陈学者',
    avatar: 'https://cube.elemecdn.com/1/1f/1f5c5f5c5f5c5f5c5f5c5f5c5f5c5f5c.png',
    content: '请问一下，目前CRISPR治疗遗传病的临床试验有哪些是开放招募的？',
    time: '1天前',
    likes: 32,
    isLiked: false,
    replies: []
  }
])

// Mock相关笔记
const relatedNotes = ref([
  {
    id: 101,
    title: 'mRNA疫苗技术原理与临床应用综述',
    author: '刘博士',
    cover: 'https://picsum.photos/200/150?random=101',
    likes: 892
  },
  {
    id: 102,
    title: 'AlphaFold2预测蛋白质结构的突破性研究',
    author: '赵研究员',
    cover: 'https://picsum.photos/200/150?random=102',
    likes: 2156
  },
  {
    id: 103,
    title: 'CAR-T细胞疗法治疗血液肿瘤的临床进展',
    author: '孙教授',
    cover: 'https://picsum.photos/200/150?random=103',
    likes: 567
  },
  {
    id: 104,
    title: '单细胞测序技术在肿瘤研究中的应用',
    author: '周博士',
    cover: null,
    likes: 423
  }
])

// Markdown渲染（简单实现）
const renderedContent = computed(() => {
  let content = note.value.content
  // 转换标题
  content = content.replace(/^### (.*$)/gim, '<h3>$1</h3>')
  content = content.replace(/^## (.*$)/gim, '<h2>$1</h2>')
  content = content.replace(/^# (.*$)/gim, '<h1>$1</h1>')
  // 转换加粗
  content = content.replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
  // 转换列表
  content = content.replace(/^- (.*$)/gim, '<li>$1</li>')
  content = content.replace(/(<li>.*<\/li>)/gims, '<ul>$1</ul>')
  // 转换段落
  content = content.replace(/\n\n/gim, '</p><p>')
  content = '<p>' + content + '</p>'
  // 清理多余的p标签
  content = content.replace(/<p><(h[123]|ul)/gim, '<$1')
  content = content.replace(/<\/(h[123]|ul)><\/p>/gim, '</$1>')
  return content
})

// 返回上一页
const goBack = () => {
  router.back()
}

// 关注/取消关注
const toggleFollow = () => {
  isFollowing.value = !isFollowing.value
  ElMessage.success(isFollowing.value ? '已关注' : '已取消关注')
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

// 跳转到相关笔记
const goToRelated = (id) => {
  router.push(`/note/${id}`)
  // 重新加载页面数据
  window.location.reload()
}

onMounted(() => {
  // 实际项目中这里会根据noteId获取笔记详情
  ElMessage.success('笔记加载完成')
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
  display: flex;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 80px 20px 40px;
}

.content-main {
  flex: 1;
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
  transition: opacity 0.2s;
}

.author-link:hover {
  opacity: 0.7;
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

.follow-btn {
  border-radius: 16px;
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
  font-size: 20px;
  font-weight: 600;
  margin: 24px 0 16px;
  color: #1a1a1a;
}

.note-body :deep(h2) {
  font-size: 18px;
  font-weight: 600;
  margin: 20px 0 12px;
  color: #1a1a1a;
}

.note-body :deep(h3) {
  font-size: 16px;
  font-weight: 600;
  margin: 16px 0 10px;
  color: #1a1a1a;
}

.note-body :deep(p) {
  margin-bottom: 12px;
}

.note-body :deep(ul) {
  margin: 12px 0;
  padding-left: 24px;
}

.note-body :deep(li) {
  margin-bottom: 6px;
}

.note-body :deep(strong) {
  font-weight: 600;
  color: #1a1a1a;
}

.source-info {
  margin: 24px 0;
}

.source-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  border-left: 4px solid #409eff;
}

.source-title {
  font-size: 15px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.source-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.source-authors {
  font-size: 13px;
  color: #999;
  margin-bottom: 12px;
}

.note-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 16px 0;
}

.note-meta {
  font-size: 13px;
  color: #999;
  margin-bottom: 20px;
}

.content-sidebar {
  width: 300px;
  flex-shrink: 0;
}

.sidebar-section {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.sidebar-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #1a1a1a;
}

.related-notes {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.related-item {
  display: flex;
  gap: 12px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.related-item:hover {
  background: #f5f7fa;
}

.related-cover {
  width: 80px;
  height: 60px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
}

.related-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.related-info {
  flex: 1;
  min-width: 0;
}

.related-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 4px;
}

.related-author {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.related-stats {
  font-size: 12px;
  color: #999;
}

@media (max-width: 968px) {
  .content-sidebar {
    display: none;
  }
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
}
</style>

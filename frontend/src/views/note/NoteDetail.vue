<template>
  <div class="note-detail">
    <div class="detail-container" v-if="note">
      <!-- 左侧内容 -->
      <div class="content-section">
        <!-- 图片画廊 -->
        <div class="image-gallery" v-if="note.images?.length">
          <el-carousel height="500px" :interval="5000" trigger="click">
            <el-carousel-item v-for="(img, idx) in note.images" :key="idx">
              <img :src="img" class="gallery-image" @click="previewImage(idx)" />
            </el-carousel-item>
          </el-carousel>
        </div>

        <!-- 笔记内容 -->
        <div class="note-content-wrapper">
          <h1 class="note-title">{{ note.title }}</h1>
          
          <div class="note-meta">
            <div class="author-info">
              <el-avatar :size="40" :src="note.author?.avatar">
                {{ note.author?.nickname?.charAt(0) }}
              </el-avatar>
              <div class="author-meta">
                <span class="author-name">{{ note.author?.nickname }}</span>
                <span class="publish-time">{{ timeAgo(note.createdAt) }}</span>
              </div>
            </div>
            <el-button
              type="primary"
              :class="{ 'is-followed': isFollowing }"
              @click="toggleFollow"
            >
              {{ isFollowing ? '已关注' : '+ 关注' }}
            </el-button>
          </div>

          <div class="note-body" v-html="renderedContent"></div>

          <div class="note-tags" v-if="note.tags?.length">
            <span v-for="tag in note.tags" :key="tag" class="tag">
              #{{ tag }}
            </span>
          </div>

          <div class="note-actions">
            <button
              class="action-btn"
              :class="{ active: note.isLiked }"
              @click="handleLike"
            >
              <Pointer v-if="note.isLiked" class="liked" />
              <Like v-else />
              <span>{{ note.likeCount || 0 }}</span>
            </button>
            
            <button
              class="action-btn"
              :class="{ active: note.isFavorited }"
              @click="handleFavorite"
            >
              <StarFilled v-if="note.isFavorited" class="favorited" />
              <Star v-else />
              <span>{{ note.favoriteCount || 0 }}</span>
            </button>
            
            <button class="action-btn" @click="handleShare">
              <Share />
              <span>分享</span>
            </button>
          </div>
        </div>

        <!-- 评论区 -->
        <div class="comments-section">
          <h3>评论 ({{ comments.length }})</h3>
          
          <div class="comment-input">
            <el-avatar :size="40" :src="currentUser?.avatar">
              {{ currentUser?.nickname?.charAt(0) }}
            </el-avatar>
            <div class="input-wrapper">
              <el-input
                v-model="newComment"
                type="textarea"
                :rows="3"
                placeholder="写下你的评论..."
                maxlength="500"
                show-word-limit
              />
              <el-button type="primary" @click="submitComment">发布</el-button>
            </div>
          </div>

          <div class="comments-list">
            <div v-for="comment in comments" :key="comment.id" class="comment-item">
              <el-avatar :size="36" :src="comment.author?.avatar">
                {{ comment.author?.nickname?.charAt(0) }}
              </el-avatar>
              <div class="comment-content">
                <div class="comment-header">
                  <span class="comment-author">{{ comment.author?.nickname }}</span>
                  <span class="comment-time">{{ timeAgo(comment.createdAt) }}</span>
                </div>
                <p class="comment-text">{{ comment.content }}</p>
                <div class="comment-actions">
                  <button @click="likeComment(comment)">
                    <Pointer v-if="comment.isLiked" />
                    <Pointer v-else />
                    {{ comment.likeCount || 0 }}
                  </button>
                  <button @click="replyComment(comment)">回复</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧侧边栏 -->
      <div class="sidebar-section" v-if="!isMobile">
        <div class="author-card">
          <el-avatar :size="60" :src="note.author?.avatar">
            {{ note.author?.nickname?.charAt(0) }}
          </el-avatar>
          <h4>{{ note.author?.nickname }}</h4>
          <p>{{ note.author?.bio || '暂无简介' }}</p>
          <div class="author-stats">
            <div>
              <span>{{ note.author?.noteCount || 0 }}</span>
              <label>笔记</label>
            </div>
            <div>
              <span>{{ note.author?.followerCount || 0 }}</span>
              <label>粉丝</label>
            </div>
            <div>
              <span>{{ note.author?.likeCount || 0 }}</span>
              <label>获赞</label>
            </div>
          </div>
        </div>

        <div class="related-notes">
          <h4>相关推荐</h4>
          <div
            v-for="related in relatedNotes"
            :key="related.id"
            class="related-item"
            @click="$router.push(`/note/${related.id}`)"
          >
            <img :src="related.coverImage" />
            <div class="related-info">
              <p>{{ related.title }}</p>
              <span>{{ related.likeCount }} 赞</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { timeAgo } from '@/utils'
import { noteApi } from '@/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const userStore = useUserStore()
const appStore = useAppStore()

const isMobile = computed(() => appStore.isMobile)
const currentUser = computed(() => userStore.currentUser)

const note = ref(null)
const comments = ref([])
const newComment = ref('')
const isFollowing = ref(false)
const relatedNotes = ref([])

// 模拟数据
note.value = {
  id: route.params.id,
  title: 'CRISPR-Cas9 基因编辑技术的最新进展与应用前景',
  content: `
## 简介

CRISPR-Cas9 是近年来生物技术领域最具革命性的技术之一。本文将介绍该技术的最新研究进展及其在各领域的应用前景。

## 技术原理

CRISPR-Cas9 系统由两部分组成：
1. **Cas9 蛋白** - 负责切割 DNA
2. **向导 RNA (gRNA)** - 引导 Cas9 到特定位置

## 最新研究进展

### 1. 碱基编辑技术
最近开发的碱基编辑器可以在不切断 DNA 双链的情况下实现精准的单碱基替换，大大降低了脱靶风险。

### 2. 先导编辑
先导编辑技术能够实现所有类型的碱基替换，以及小片段的插入和删除。

## 应用前景

- 基因治疗
- 农作物改良
- 疾病模型构建
- 功能基因组学研究

## 结语

CRISPR 技术正在快速发展，未来将在更多领域发挥重要作用。
  `,
  coverImage: 'https://picsum.photos/800/500?random=30',
  images: [
    'https://picsum.photos/800/500?random=30',
    'https://picsum.photos/800/500?random=31',
    'https://picsum.photos/800/500?random=32',
  ],
  author: {
    id: 1,
    nickname: '基因编辑专家',
    avatar: '',
    bio: '专注于CRISPR技术研究，分享最新科研进展',
    noteCount: 42,
    followerCount: 1234,
    likeCount: 5678,
  },
  tags: ['基因编辑', 'CRISPR', '研究进展', '生物技术'],
  createdAt: new Date(Date.now() - 86400000 * 2),
  likeCount: 234,
  favoriteCount: 89,
  viewCount: 3456,
  isLiked: false,
  isFavorited: false,
}

comments.value = [
  {
    id: 1,
    author: { nickname: '生物研究员', avatar: '' },
    content: '写得很详细，学到了很多！请问有推荐的gRNA设计工具吗？',
    createdAt: new Date(Date.now() - 3600000 * 2),
    likeCount: 12,
    isLiked: false,
  },
  {
    id: 2,
    author: { nickname: '实验室新人', avatar: '' },
    content: '正准备学习CRISPR，这篇文章太及时了，感谢分享！',
    createdAt: new Date(Date.now() - 3600000 * 5),
    likeCount: 8,
    isLiked: true,
  },
]

relatedNotes.value = [
  { id: 2, title: 'CRISPR实验protocol分享', coverImage: 'https://picsum.photos/200/150?random=40', likeCount: 156 },
  { id: 3, title: '基因编辑伦理问题探讨', coverImage: 'https://picsum.photos/200/150?random=41', likeCount: 89 },
  { id: 4, title: '新型Cas蛋白研究进展', coverImage: 'https://picsum.photos/200/150?random=42', likeCount: 234 },
]

const renderedContent = computed(() => {
  if (!note.value?.content) return ''
  return marked(note.value.content)
})

const handleLike = async () => {
  try {
    if (note.value.isLiked) {
      await noteApi.unlikeNote(note.value.id)
      note.value.isLiked = false
      note.value.likeCount--
    } else {
      await noteApi.likeNote(note.value.id)
      note.value.isLiked = true
      note.value.likeCount++
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleFavorite = async () => {
  try {
    if (note.value.isFavorited) {
      await noteApi.unfavoriteNote(note.value.id)
      note.value.isFavorited = false
      note.value.favoriteCount--
    } else {
      await noteApi.favoriteNote(note.value.id)
      note.value.isFavorited = true
      note.value.favoriteCount++
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleShare = () => {
  ElMessage.success('链接已复制到剪贴板')
}

const toggleFollow = () => {
  isFollowing.value = !isFollowing.value
}

const submitComment = async () => {
  if (!newComment.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  
  try {
    await noteApi.addComment(note.value.id, { content: newComment.value })
    comments.value.unshift({
      id: Date.now(),
      author: currentUser.value,
      content: newComment.value,
      createdAt: new Date(),
      likeCount: 0,
      isLiked: false,
    })
    newComment.value = ''
    ElMessage.success('评论发布成功')
  } catch (error) {
    ElMessage.error('发布失败')
  }
}

const likeComment = (comment) => {
  comment.isLiked = !comment.isLiked
  comment.likeCount += comment.isLiked ? 1 : -1
}

const replyComment = (comment) => {
  newComment.value = `@${comment.author.nickname} `
}

const previewImage = (idx) => {
  // 图片预览
}

onMounted(() => {
  // 加载笔记详情
})
</script>

<style scoped>
.note-detail {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 24px 0;
}

.detail-container {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 24px;
  padding: 0 24px;
}

.content-section {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
}

.image-gallery {
  background: #000;
}

.gallery-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  cursor: zoom-in;
}

.note-content-wrapper {
  padding: 24px;
}

.note-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
  line-height: 1.4;
}

.note-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.author-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.author-name {
  font-size: 15px;
  font-weight: 500;
  color: #333;
}

.publish-time {
  font-size: 13px;
  color: #999;
}

.is-followed {
  background: #f0f0f0;
  border-color: #f0f0f0;
  color: #999;
}

.note-body {
  font-size: 15px;
  line-height: 1.8;
  color: #333;
  margin-bottom: 24px;
}

.note-body :deep(h2) {
  font-size: 20px;
  font-weight: 600;
  margin: 24px 0 12px;
  color: #333;
}

.note-body :deep(p) {
  margin-bottom: 12px;
}

.note-body :deep(ul) {
  margin-bottom: 12px;
  padding-left: 24px;
}

.note-body :deep(li) {
  margin-bottom: 8px;
}

.note-body :deep(strong) {
  font-weight: 600;
  color: #222;
}

.note-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 24px;
}

.tag {
  font-size: 14px;
  color: #ff2442;
  background: rgba(255, 36, 66, 0.08);
  padding: 6px 12px;
  border-radius: 16px;
}

.note-actions {
  display: flex;
  gap: 16px;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  background: #f5f5f5;
  border: none;
  border-radius: 24px;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
}

.action-btn:hover {
  background: #eee;
}

.action-btn.active {
  background: rgba(255, 36, 66, 0.1);
  color: #ff2442;
}

.action-btn svg {
  font-size: 18px;
}

.liked {
  animation: likeAnimation 0.3s ease;
}

.favorited {
  animation: likeAnimation 0.3s ease;
}

@keyframes likeAnimation {
  0% { transform: scale(1); }
  50% { transform: scale(1.3); }
  100% { transform: scale(1); }
}

.comments-section {
  padding: 24px;
  border-top: 1px solid #f0f0f0;
}

.comments-section h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
}

.comment-input {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.input-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-end;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.comment-item {
  display: flex;
  gap: 12px;
}

.comment-content {
  flex: 1;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.comment-author {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.comment-time {
  font-size: 12px;
  color: #999;
}

.comment-text {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  margin-bottom: 8px;
}

.comment-actions {
  display: flex;
  gap: 16px;
}

.comment-actions button {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #999;
  background: none;
  border: none;
  cursor: pointer;
}

.comment-actions button:hover {
  color: #ff2442;
}

.sidebar-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.author-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  text-align: center;
}

.author-card h4 {
  margin: 12px 0 8px;
  font-size: 16px;
  font-weight: 600;
}

.author-card p {
  font-size: 13px;
  color: #999;
  margin-bottom: 16px;
}

.author-stats {
  display: flex;
  justify-content: center;
  gap: 24px;
}

.author-stats div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.author-stats span {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.author-stats label {
  font-size: 12px;
  color: #999;
}

.related-notes {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
}

.related-notes h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.related-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.3s;
}

.related-item:hover {
  background: #f5f5f5;
}

.related-item img {
  width: 80px;
  height: 60px;
  object-fit: cover;
  border-radius: 8px;
}

.related-info {
  flex: 1;
}

.related-info p {
  font-size: 14px;
  color: #333;
  line-height: 1.4;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.related-info span {
  font-size: 12px;
  color: #999;
}

@media (max-width: 768px) {
  .detail-container {
    grid-template-columns: 1fr;
    padding: 0 12px;
  }

  .note-title {
    font-size: 20px;
  }

  .note-content-wrapper {
    padding: 16px;
  }

  .comments-section {
    padding: 16px;
  }
}
</style>
<template>
  <div class="note-card" @click="handleClick">
    <!-- 内容区 -->
    <div class="card-content">
      <h3 class="card-title">{{ note.title }}</h3>
      
      <!-- 预览文本 -->
      <p v-if="note.preview" class="card-preview">{{ note.preview }}</p>
      
      <div class="card-footer">
        <div class="card-author">
          <el-avatar :size="20" :src="note.authorAvatar || defaultAvatar" />
          <span class="author-name">{{ note.author || 'ProteinHub' }}</span>
        </div>
        
        <div class="card-stats">
          <span class="stat-item" @click.stop="handleLike">
            <el-icon :size="14" v-if="note.isLiked"><StarFilled /></el-icon>
            <el-icon :size="14" v-else><Star /></el-icon>
            <span class="stat-num">{{ formatNumber(note.likes) }}</span>
          </span>
          
          <span v-if="note.comments" class="stat-item">
            <el-icon :size="14"><ChatRound /></el-icon>
            <span class="stat-num">{{ formatNumber(note.comments) }}</span>
          </span>
        </div>
      </div>
      
      <!-- 标签 -->
      <div v-if="note.tags && note.tags.length" class="card-tags">
        <span v-for="tag in note.tags.slice(0, 3)" :key="tag" class="tag">{{ tag }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Star, StarFilled, ChatRound } from '@element-plus/icons-vue'

const defaultAvatar = 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'

const props = defineProps({
  note: {
    type: Object,
    required: true,
    default: () => ({
      id: 0,
      title: '',
      preview: '',
      author: '',
      authorAvatar: '',
      likes: 0,
      comments: 0,
      isLiked: false,
      tags: []
    })
  }
})

const emit = defineEmits(['click', 'like'])

// 格式化数字（超过1000显示为1k）
const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

// 点击卡片
const handleClick = () => {
  emit('click')
}

// 点赞（阻止冒泡）
const handleLike = () => {
  emit('like', props.note.id)
}
</script>

<style scoped>
.note-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.note-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-content {
  padding: 16px;
}

.card-title {
  font-size: 15px;
  font-weight: 500;
  color: #1a1a1a;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
  min-height: 42px;
}

.card-preview {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 12px;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.card-author {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.author-name {
  font-size: 12px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.card-stats .stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #999;
  cursor: pointer;
  transition: color 0.2s;
  padding: 4px;
  border-radius: 4px;
}

.card-stats .stat-item:hover {
  color: #ff2442;
  background: rgba(255, 36, 66, 0.08);
}

.card-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  font-size: 11px;
  color: #409eff;
  background: #e6f7ff;
  padding: 2px 8px;
  border-radius: 4px;
}
</style>
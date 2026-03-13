<template>
  <div class="note-card" @click="handleClick">
    <!-- 封面图 -->
    <div class="card-cover" v-if="note.cover">
      <img :src="note.cover" :alt="note.title" loading="lazy">
      <div class="cover-overlay">
        <div class="overlay-stats">
          <span class="stat-item">
            <el-icon><View /></el-icon> {{ formatNumber(note.likes) }}
          </span>
        </div>
      </div>
    </div>
    
    <!-- 无封面时的占位 -->
    <div class="card-cover placeholder" v-else>
      <div class="placeholder-content">
        <el-icon :size="40"><Document /></el-icon>
        <span>学术笔记</span>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="card-content">
      <h3 class="card-title" :class="{ 'no-cover': !note.cover }">{{ note.title }}</h3>
      
      <div class="card-footer">
        <router-link 
          :to="'/user/' + (note.authorId || 1)" 
          class="card-author"
          @click.stop
        >
          <el-avatar :size="20" :src="note.authorAvatar" />
          <span class="author-name">{{ note.author }}</span>
        </router-link>
        
        <div class="card-stats">
          <span class="stat-item" @click.stop="handleLike">
            <el-icon :size="14">
              <StarFilled v-if="note.isLiked" />
              <Star v-else />
            </el-icon>
            <span class="stat-num">{{ formatNumber(note.likes) }}</span>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Star, StarFilled, View, Document } from '@element-plus/icons-vue'

const props = defineProps({
  note: {
    type: Object,
    required: true,
    default: () => ({
      id: 0,
      title: '',
      author: '',
      authorId: 1,
      authorAvatar: '',
      cover: null,
      likes: 0,
      isLiked: false
    })
  }
})

const emit = defineEmits(['click', 'like', 'author-click'])

// 格式化数字（超过1000显示为1k）
const formatNumber = (num) => {
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

.card-cover {
  position: relative;
  width: 100%;
  aspect-ratio: 3/4;
  overflow: hidden;
  background: #f5f7fa;
}

.card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.note-card:hover .card-cover img {
  transform: scale(1.05);
}

.cover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, transparent 60%, rgba(0, 0, 0, 0.4));
  opacity: 0;
  transition: opacity 0.3s ease;
  display: flex;
  align-items: flex-end;
  padding: 12px;
}

.note-card:hover .cover-overlay {
  opacity: 1;
}

.overlay-stats {
  color: #fff;
  font-size: 13px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-cover.placeholder {
  aspect-ratio: 3/4;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #fff;
  font-size: 14px;
}

.card-content {
  padding: 12px;
}

.card-title {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 10px;
  min-height: 42px;
}

.card-title.no-cover {
  font-size: 15px;
  -webkit-line-clamp: 3;
  min-height: 63px;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-author {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
  text-decoration: none;
  transition: opacity 0.2s;
}

.card-author:hover {
  opacity: 0.7;
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

.card-stats .stat-item .el-icon {
  transition: transform 0.2s;
}

.card-stats .stat-item:active .el-icon {
  transform: scale(1.2);
}

.card-stats .stat-item:deep(.el-icon) {
  color: inherit;
}

.card-stats .stat-item:deep(.el-icon svg) {
  fill: currentColor;
}

.stat-num {
  margin-left: 2px;
}
</style>

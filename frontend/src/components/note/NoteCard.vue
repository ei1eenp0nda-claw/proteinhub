<template>
  <div class="note-card" @click="goToDetail">
    <div class="card-image-wrapper">
      <img
        :src="note.coverImage || '/default-note-cover.jpg'"
        :alt="note.title"
        class="card-image"
        loading="lazy"
      />
      <div class="image-overlay">
        <div class="note-stats">
          <span class="stat-item">
            <View /> {{ formatNumber(note.viewCount || 0) }}
          </span>
        </div>
      </div>
    </div>
    
    <div class="card-content">
      <h3 class="note-title">{{ note.title }}</h3>
      <p class="note-desc">{{ note.summary }}</p>
      
      <div class="note-tags" v-if="note.tags?.length">
        <span
          v-for="tag in note.tags.slice(0, 3)"
          :key="tag"
          class="tag"
        >
          #{{ tag }}
        </span>
      </div>
      
      <div class="card-footer">
        <div class="author-info">
          <el-avatar
            :size="24"
            :src="note.author?.avatar"
            @click.stop="goToAuthor"
          >
            {{ note.author?.nickname?.charAt(0) || 'U' }}
          </el-avatar>
          <span class="author-name" @click.stop="goToAuthor">
            {{ note.author?.nickname }}
          </span>
        </div>
        
        <div class="actions">
          <button
            class="action-btn"
            :class="{ active: note.isLiked }"
            @click.stop="handleLike"
          >
            <Like v-if="!note.isLiked" />
            <Pointer v-else class="liked" />
            <span>{{ formatNumber(note.likeCount || 0) }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { formatNumber } from '@/utils'
import { noteApi } from '@/api'
import { ElMessage } from 'element-plus'

const props = defineProps({
  note: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['update'])
const router = useRouter()

const goToDetail = () => {
  router.push(`/note/${props.note.id}`)
}

const goToAuthor = () => {
  router.push(`/user/${props.note.author?.id}`)
}

const handleLike = async () => {
  try {
    if (props.note.isLiked) {
      await noteApi.unlikeNote(props.note.id)
      emit('update', {
        ...props.note,
        isLiked: false,
        likeCount: (props.note.likeCount || 0) - 1,
      })
    } else {
      await noteApi.likeNote(props.note.id)
      emit('update', {
        ...props.note,
        isLiked: true,
        likeCount: (props.note.likeCount || 0) + 1,
      })
    }
  } catch (error) {
    ElMessage.error('操作失败，请重试')
  }
}
</script>

<style scoped>
.note-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
  break-inside: avoid;
  margin-bottom: 16px;
}

.note-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-image-wrapper {
  position: relative;
  overflow: hidden;
}

.card-image {
  width: 100%;
  height: auto;
  display: block;
  transition: transform 0.3s;
}

.note-card:hover .card-image {
  transform: scale(1.05);
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, transparent 60%, rgba(0, 0, 0, 0.4));
  opacity: 0;
  transition: opacity 0.3s;
}

.note-card:hover .image-overlay {
  opacity: 1;
}

.note-stats {
  position: absolute;
  bottom: 8px;
  left: 12px;
  color: #fff;
  font-size: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-content {
  padding: 12px;
}

.note-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  line-height: 1.4;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.note-desc {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.note-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.tag {
  font-size: 12px;
  color: #ff2442;
  background: rgba(255, 36, 66, 0.08);
  padding: 2px 8px;
  border-radius: 10px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.author-name {
  font-size: 13px;
  color: #666;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.actions {
  display: flex;
  gap: 12px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: #999;
  font-size: 13px;
  cursor: pointer;
  transition: color 0.3s;
  padding: 4px;
}

.action-btn:hover {
  color: #ff2442;
}

.action-btn.active {
  color: #ff2442;
}

.action-btn svg {
  font-size: 16px;
}

.liked {
  animation: likeAnimation 0.3s ease;
}

@keyframes likeAnimation {
  0% { transform: scale(1); }
  50% { transform: scale(1.3); }
  100% { transform: scale(1); }
}
</style>
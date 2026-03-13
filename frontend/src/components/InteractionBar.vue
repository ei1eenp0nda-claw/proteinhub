<template>
  <div class="interaction-bar">
    <div class="interaction-actions">
      <!-- 点赞按钮 -->
      <button 
        class="action-btn"
        :class="{ 'is-active': isLiked, 'animating': likeAnimating }"
        @click="handleLike"
      >
        <div class="btn-icon">
          <div class="icon-wrapper">
            <svg v-if="isLiked" viewBox="0 0 24 24" class="heart-icon filled">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" fill="#ff2442"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" class="heart-icon">
              <path d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3zm-4.4 15.55l-.1.1-.1-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04.99 3.57 2.36h1.87C13.46 5.99 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05z" fill="#666"/>
            </svg>
          </div>
        </div>
        <span class="btn-count" :class="{ 'bounce': likeAnimating }">{{ formatCount(likes) }}</span>
        <span class="btn-label">赞</span>
      </button>

      <!-- 收藏按钮 -->
      <button 
        class="action-btn"
        :class="{ 'is-active': isFavorited, 'animating': favAnimating }"
        @click="handleFavorite"
      >
        <div class="btn-icon">
          <div class="icon-wrapper">
            <svg v-if="isFavorited" viewBox="0 0 24 24" class="star-icon filled">
              <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" fill="#ffb800"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" class="star-icon">
              <path d="M22 9.24l-7.19-.62L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.63-7.03L22 9.24zM12 15.4l-3.76 2.27 1-4.28-3.32-2.88 4.38-.38L12 6.1l1.71 4.04 4.38.38-3.32 2.88 1 4.28L12 15.4z" fill="#666"/>
            </svg>
          </div>
        </div>
        <span class="btn-count" :class="{ 'bounce': favAnimating }">{{ formatCount(favorites) }}</span>
        <span class="btn-label">收藏</span>
      </button>

      <!-- 评论按钮 -->
      <button class="action-btn" @click="handleComment">
        <div class="btn-icon">
          <div class="icon-wrapper">
            <svg viewBox="0 0 24 24" class="comment-icon">
              <path d="M21.99 4c0-1.1-.89-2-1.99-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4-.01-18zM18 14H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z" fill="#666"/>
            </svg>
          </div>
        </div>
        <span class="btn-count">{{ formatCount(comments) }}</span>
        <span class="btn-label">评论</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  likes: {
    type: Number,
    default: 0
  },
  favorites: {
    type: Number,
    default: 0
  },
  comments: {
    type: Number,
    default: 0
  },
  isLiked: {
    type: Boolean,
    default: false
  },
  isFavorited: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['like', 'favorite', 'comment'])

// 动画状态
const likeAnimating = ref(false)
const favAnimating = ref(false)

// 格式化数字
const formatCount = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

// 点赞
const handleLike = () => {
  likeAnimating.value = true
  emit('like')
  setTimeout(() => {
    likeAnimating.value = false
  }, 400)
}

// 收藏
const handleFavorite = () => {
  favAnimating.value = true
  emit('favorite')
  setTimeout(() => {
    favAnimating.value = false
  }, 400)
}

// 评论
const handleComment = () => {
  emit('comment')
}
</script>

<style scoped>
.interaction-bar {
  padding: 16px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
  margin: 20px 0;
}

.interaction-actions {
  display: flex;
  gap: 40px;
  justify-content: center;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border: none;
  background: none;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 8px;
}

.action-btn:hover {
  background: rgba(0, 0, 0, 0.03);
}

.btn-icon {
  position: relative;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-wrapper {
  position: relative;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.action-btn:hover .icon-wrapper {
  transform: scale(1.1);
}

.action-btn.animating .icon-wrapper {
  animation: heartBeat 0.4s ease;
}

.heart-icon,
.star-icon,
.comment-icon {
  width: 24px;
  height: 24px;
  transition: all 0.2s;
}

.heart-icon.filled {
  animation: heartPop 0.4s ease;
}

.star-icon.filled {
  animation: starPop 0.4s ease;
}

.btn-count {
  font-size: 13px;
  font-weight: 500;
  color: #666;
  transition: all 0.2s;
}

.btn-count.bounce {
  animation: countBounce 0.4s ease;
}

.action-btn.is-active .btn-count {
  color: #ff2442;
}

.action-btn.is-active:nth-child(2) .btn-count {
  color: #ffb800;
}

.btn-label {
  font-size: 12px;
  color: #999;
}

/* 动画效果 */
@keyframes heartBeat {
  0% { transform: scale(1); }
  25% { transform: scale(0.8); }
  50% { transform: scale(1.3); }
  75% { transform: scale(0.95); }
  100% { transform: scale(1); }
}

@keyframes heartPop {
  0% { transform: scale(0); opacity: 0; }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); opacity: 1; }
}

@keyframes starPop {
  0% { transform: scale(0) rotate(-180deg); opacity: 0; }
  50% { transform: scale(1.2) rotate(10deg); }
  100% { transform: scale(1) rotate(0deg); opacity: 1; }
}

@keyframes countBounce {
  0% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
  100% { transform: translateY(0); }
}

/* 粒子效果 */
.action-btn.animating .icon-wrapper::after {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  animation: ripple 0.4s ease-out;
}

@keyframes ripple {
  0% {
    box-shadow: 
      0 0 0 0 rgba(255, 36, 66, 0.4),
      0 0 0 0 rgba(255, 36, 66, 0.3),
      0 0 0 0 rgba(255, 36, 66, 0.2);
  }
  100% {
    box-shadow: 
      0 0 0 10px rgba(255, 36, 66, 0),
      0 0 0 20px rgba(255, 36, 66, 0),
      0 0 0 30px rgba(255, 36, 66, 0);
  }
}

@media (max-width: 768px) {
  .interaction-actions {
    gap: 24px;
  }
  
  .action-btn {
    padding: 6px 12px;
  }
}
</style>

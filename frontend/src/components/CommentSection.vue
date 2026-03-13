<template>
  <div class="comment-section">
    <h3 class="section-title">评论 {{ totalComments }}</h3>

    <!-- 评论输入框 -->
    <div class="comment-input-area">
      <el-avatar :size="40" :src="currentUserAvatar" class="input-avatar" />
      <div class="input-wrapper">
        <el-input
          ref="inputRef"
          v-model="commentContent"
          type="textarea"
          :rows="inputRows"
          :placeholder="replyTo ? `回复 ${replyTo}...` : '写下你的评论...'
          maxlength="500"
          show-word-limit
          @focus="inputRows = 3"
          @blur="handleBlur"
        />
        <div class="input-actions" v-if="showActions || commentContent">
          <el-button @click="cancelComment">取消</el-button>
          <el-button 
            type="primary" 
            :disabled="!commentContent.trim()"
            @click="submitComment"
          >
            {{ replyTo ? '回复' : '发布' }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- 评论列表 -->
    <div class="comment-list">
      <div 
        v-for="comment in comments" 
        :key="comment.id"
        class="comment-item"
      >
        <!-- 主评论 -->
        <div class="comment-main">
          <el-avatar :size="40" :src="comment.avatar" class="comment-avatar" />
          
          <div class="comment-content">
            <div class="comment-header">
              <span class="comment-author">{{ comment.author }}</span>
              <span class="comment-time">{{ comment.time }}</span>
            </div>
            
            <p class="comment-text">{{ comment.content }}</p>
            
            <div class="comment-actions">
              <button 
                class="action-item"
                :class="{ 'is-active': comment.isLiked }"
                @click="handleLikeComment(comment)"
              >
                <el-icon :size="14">
                  <StarFilled v-if="comment.isLiked" />
                  <Star v-else />
                </el-icon>
                <span>{{ comment.likes || '赞' }}</span>
              </button>
              
              <button class="action-item" @click="handleReply(comment)">
                <el-icon :size="14"><ChatRound /></el-icon>
                <span>回复</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 回复列表 -->
        <div v-if="comment.replies && comment.replies.length" class="reply-list">
          <div 
            v-for="reply in comment.replies" 
            :key="reply.id"
            class="reply-item"
          >
            <el-avatar :size="32" :src="reply.avatar" class="reply-avatar" />
            
            <div class="reply-content">
              <div class="reply-header">
                <span class="reply-author">{{ reply.author }}</span>
                <span v-if="reply.replyTo" class="reply-to">
                  回复 <span class="reply-to-name">{{ reply.replyTo }}</span>
                </span>
                <span class="reply-time">{{ reply.time }}</span>
              </div>
              
              <p class="reply-text">{{ reply.content }}</p>
              
              <div class="reply-actions">
                <button 
                  class="action-item"
                  :class="{ 'is-active': reply.isLiked }"
                  @click="handleLikeReply(reply)"
                >
                  <el-icon :size="12">
                    <StarFilled v-if="reply.isLiked" />
                    <Star v-else />
                  </el-icon>
                  <span>{{ reply.likes || '赞' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!comments.length" class="empty-state">
      <el-empty description="暂无评论，快来抢沙发吧~" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Star, StarFilled, ChatRound } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  comments: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['submit', 'reply', 'like'])

// 状态
const inputRef = ref(null)
const commentContent = ref('')
const inputRows = ref(1)
const showActions = ref(false)
const replyTo = ref(null)
const replyCommentId = ref(null)

const currentUserAvatar = ref('https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png')

// 计算总评论数（包括回复）
const totalComments = computed(() => {
  let count = props.comments.length
  props.comments.forEach(comment => {
    if (comment.replies) {
      count += comment.replies.length
    }
  })
  return count
})

// 处理失焦
const handleBlur = () => {
  if (!commentContent.value) {
    inputRows.value = 1
    showActions.value = false
  }
}

// 聚焦输入框（供父组件调用）
const focusInput = () => {
  inputRef.value?.focus()
  inputRows.value = 3
  showActions.value = true
  replyTo.value = null
  replyCommentId.value = null
}

// 取消评论
const cancelComment = () => {
  commentContent.value = ''
  replyTo.value = null
  replyCommentId.value = null
  inputRows.value = 1
  showActions.value = false
}

// 提交评论
const submitComment = () => {
  const content = commentContent.value.trim()
  if (!content) return

  if (replyCommentId.value) {
    // 回复评论
    emit('reply', {
      commentId: replyCommentId.value,
      content: content
    })
  } else {
    // 新评论
    emit('submit', content)
  }

  commentContent.value = ''
  replyTo.value = null
  replyCommentId.value = null
  inputRows.value = 1
  showActions.value = false
}

// 点赞评论
const handleLikeComment = (comment) => {
  comment.isLiked = !comment.isLiked
  comment.likes += comment.isLiked ? 1 : -1
  emit('like', { type: 'comment', id: comment.id, isLiked: comment.isLiked })
}

// 点赞回复
const handleLikeReply = (reply) => {
  reply.isLiked = !reply.isLiked
  reply.likes += reply.isLiked ? 1 : -1
}

// 回复评论
const handleReply = (comment) => {
  replyTo.value = comment.author
  replyCommentId.value = comment.id
  inputRows.value = 3
  showActions.value = true
  
  // 聚焦输入框
  setTimeout(() => {
    inputRef.value?.focus()
  }, 100)
}

// 暴露方法给父组件
defineExpose({
  focusInput
})
</script>

<style scoped>
.comment-section {
  margin-top: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 20px;
}

.comment-input-area {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.input-avatar {
  flex-shrink: 0;
}

.input-wrapper {
  flex: 1;
}

.input-wrapper :deep(.el-textarea__inner) {
  border-radius: 8px;
  resize: none;
  transition: all 0.2s;
}

.input-wrapper :deep(.el-textarea__inner:focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 12px;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.comment-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.comment-main {
  display: flex;
  gap: 12px;
}

.comment-avatar {
  flex-shrink: 0;
}

.comment-content {
  flex: 1;
  min-width: 0;
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
  color: #1a1a1a;
}

.comment-time {
  font-size: 12px;
  color: #999;
}

.comment-text {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
  margin: 0;
}

.comment-actions {
  display: flex;
  gap: 16px;
  margin-top: 8px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 13px;
  color: #999;
  border-radius: 4px;
  transition: all 0.2s;
}

.action-item:hover {
  background: rgba(0, 0, 0, 0.03);
  color: #666;
}

.action-item.is-active {
  color: #ff2442;
}

.action-item.is-active :deep(.el-icon) {
  color: #ff2442;
}

.reply-list {
  margin-left: 52px;
  padding-left: 12px;
  border-left: 2px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.reply-item {
  display: flex;
  gap: 10px;
}

.reply-avatar {
  flex-shrink: 0;
}

.reply-content {
  flex: 1;
  min-width: 0;
}

.reply-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.reply-author {
  font-size: 13px;
  font-weight: 500;
  color: #1a1a1a;
}

.reply-to {
  font-size: 12px;
  color: #999;
}

.reply-to-name {
  color: #409eff;
}

.reply-time {
  font-size: 11px;
  color: #ccc;
}

.reply-text {
  font-size: 13px;
  line-height: 1.5;
  color: #333;
  margin: 0;
}

.reply-actions {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}

.reply-actions .action-item {
  font-size: 12px;
  padding: 2px 6px;
}

.empty-state {
  padding: 40px 0;
}

@media (max-width: 768px) {
  .comment-input-area {
    gap: 10px;
  }
  
  .reply-list {
    margin-left: 0;
    padding-left: 8px;
  }
  
  .input-actions {
    flex-wrap: wrap;
  }
}
</style>

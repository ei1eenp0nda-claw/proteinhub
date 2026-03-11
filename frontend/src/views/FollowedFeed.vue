<template>
  <div class="followed-feed">
    <header>
      <h1>我的关注</h1>
      <p v-if="followedCount > 0">关注 {{ followedCount }} 个蛋白</p>
      <p v-else class="empty-hint">还没有关注任何蛋白，去 <router-link to="/explore">发现</router-link> 看看吧！</p>
    </header>

    <div v-if="loading" class="loading">加载中...</div>
    
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <div v-else-if="posts.length === 0" class="empty">
      关注的蛋白还没有发布内容
    </div>
    
    <div v-else class="posts-grid">
      <div v-for="post in posts" :key="post.id" class="post-card">
        <router-link :to="`/protein/${post.protein_id}`" class="protein-tag">
          {{ post.protein_name }}
        </router-link>
        <h3>{{ post.title }}</h3>
        <p class="summary">{{ post.summary }}</p>
        
        <div class="meta">
          <span>{{ formatDate(post.created_at) }}</span>
          <a v-if="post.source_url" :href="post.source_url" target="_blank">查看原文</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const posts = ref([])
const followedCount = ref(0)
const loading = ref(true)
const error = ref('')

const fetchFollowedFeed = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }
    
    const response = await fetch('/api/user/follow-feed', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      posts.value = data.items || []
    } else if (response.status === 401) {
      router.push('/login')
    } else {
      error.value = '获取数据失败'
    }
    
    // 获取关注数量
    const countRes = await fetch('/api/user/followed-proteins', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (countRes.ok) {
      const countData = await countRes.json()
      followedCount.value = countData.total || 0
    }
  } catch (err) {
    error.value = '网络错误'
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

onMounted(fetchFollowedFeed)
</script>

<style scoped>
.followed-feed {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

header {
  margin-bottom: 24px;
}

h1 {
  font-size: 24px;
  margin-bottom: 8px;
}

.empty-hint {
  color: #999;
}

.empty-hint a {
  color: #409eff;
}

.loading, .error, .empty {
  text-align: center;
  padding: 40px;
  color: #999;
}

.error {
  color: #f56c6c;
}

.posts-grid {
  display: grid;
  gap: 16px;
}

.post-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.protein-tag {
  display: inline-block;
  background: #e6f7ff;
  color: #1890ff;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  text-decoration: none;
  margin-bottom: 12px;
}

.post-card h3 {
  font-size: 16px;
  margin-bottom: 8px;
  color: #333;
}

.summary {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
}

.meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

.meta a {
  color: #409eff;
  text-decoration: none;
}
</style>

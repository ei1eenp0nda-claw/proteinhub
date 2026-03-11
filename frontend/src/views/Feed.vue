<template>
  <div class="feed-container">
    <header class="header">
      <h1>🧬 ProteinHub</h1>
      <p>发现你感兴趣的蛋白质</p>
    </header>
    
    <div class="feed-list">
      <div v-for="post in posts" :key="post.id" class="post-card" @click="goToProtein(post.protein_id)">
        <div class="post-header">
          <span class="protein-tag">{{ post.protein_name }}</span>
          <span class="post-time">{{ formatDate(post.created_at) }}</span>
        </div>
        <h3 class="post-title">{{ post.title }}</h3>
        
        <p class="post-summary" v-if="post.summary">{{ post.summary }}</p>
        
        <div class="post-footer">
          <a :href="post.source_url" target="_blank" @click.stop>查看原文 →</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

export default {
  name: 'Feed',
  setup() {
    const posts = ref([])
    const router = useRouter()
    
    const API_BASE = 'http://localhost:5000/api'
    
    const fetchFeed = async () => {
      try {
        const response = await axios.get(`${API_BASE}/feed`)
        posts.value = response.data
      } catch (error) {
        console.error('Failed to fetch feed:', error)
      }
    }
    
    const goToProtein = (proteinId) => {
      router.push(`/protein/${proteinId}`)
    }
    
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('zh-CN')
    }
    
    onMounted(() => {
      fetchFeed()
    })
    
    return {
      posts,
      goToProtein,
      formatDate
    }
  }
}
</script>

<style scoped>
.feed-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 28px;
  color: #303133;
  margin-bottom: 8px;
}

.header p {
  color: #909399;
}

.feed-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.post-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  cursor: pointer;
  transition: transform 0.2s;
}

.post-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.protein-tag {
  background: #409eff;
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
}

.post-time {
  color: #909399;
  font-size: 12px;
}

.post-title {
  font-size: 18px;
  color: #303133;
  margin-bottom: 12px;
  line-height: 1.4;
}

.post-summary {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-footer {
  border-top: 1px solid #ebeef5;
  padding-top: 12px;
}

.post-footer a {
  color: #409eff;
  text-decoration: none;
  font-size: 14px;
}
</style>

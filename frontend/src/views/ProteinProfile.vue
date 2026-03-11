<template>
  <div class="profile-container" v-if="profile">
    <header class="profile-header">
      <div class="protein-info">
        <h1>{{ profile.protein.name }}</h1>
        <span class="family-badge">{{ profile.protein.family }} 家族</span>
      </div>
      <button class="follow-btn" @click="followProtein">+ 关注</button>
    </header>
    
    <!-- 置顶传记 -->
    <section class="biography-section">
      <div class="section-title">📖 {{ profile.biography.title }}</div>
      <div class="biography-content">
        <p>{{ profile.biography.content }}</p>
        <div v-if="profile.protein.uniprot_id" class="uniprot-link">
          <a :href="`https://www.uniprot.org/uniprotkb/${profile.protein.uniprot_id}`" target="_blank">
            查看 UniProt 详情 →
          </a>
        </div>
      </div>
    </section>
    
    <!-- 相关帖子 -->
    <section class="posts-section">
      <div class="section-title">📝 相关文献</div>
      
      <div v-if="profile.posts.length === 0" class="empty-state">
        暂无相关文献
      </div>
      
      <div v-else class="posts-list">
        <div v-for="post in profile.posts" :key="post.id" class="post-item">
          <h4>{{ post.title }}</h4>
          <p v-if="post.summary">{{ post.summary }}</p>
          <a v-if="post.source_url" :href="post.source_url" target="_blank">阅读原文 →</a>
        </div>
      </div>
    </section>
    
    <div class="back-link">
      <router-link to="/">← 返回首页</router-link>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

export default {
  name: 'ProteinProfile',
  setup() {
    const route = useRoute()
    const profile = ref(null)
    
    const API_BASE = 'http://localhost:5000/api'
    
    const fetchProfile = async () => {
      try {
        const proteinId = route.params.id
        const response = await axios.get(`${API_BASE}/proteins/${proteinId}/profile`)
        profile.value = response.data
      } catch (error) {
        console.error('Failed to fetch profile:', error)
      }
    }
    
    const followProtein = () => {
      alert('关注功能开发中...')
    }
    
    onMounted(() => {
      fetchProfile()
    })
    
    return {
      profile,
      followProtein
    }
  }
}
</script>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #ebeef5;
}

.protein-info h1 {
  font-size: 32px;
  color: #303133;
  margin-bottom: 8px;
}

.family-badge {
  background: #67c23a;
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
}

.follow-btn {
  background: #409eff;
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 20px;
  font-size: 16px;
  cursor: pointer;
}

.follow-btn:hover {
  background: #66b1ff;
}

.section-title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.biography-section {
  background: #f5f7fa;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 30px;
}

.biography-content p {
  color: #606266;
  line-height: 1.8;
  font-size: 16px;
}

.uniprot-link {
  margin-top: 16px;
}

.uniprot-link a {
  color: #409eff;
  text-decoration: none;
}

.posts-section {
  margin-bottom: 30px;
}

.post-item {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.post-item h4 {
  color: #303133;
  margin-bottom: 8px;
}

.post-item p {
  color: #606266;
  font-size: 14px;
  margin-bottom: 8px;
}

.post-item a {
  color: #409eff;
  font-size: 14px;
  text-decoration: none;
}

.empty-state {
  text-align: center;
  color: #909399;
  padding: 40px;
}

.back-link {
  margin-top: 30px;
}

.back-link a {
  color: #409eff;
  text-decoration: none;
}
</style>

<template>
  <div class="explore-page">
    <header>
      <h1>发现蛋白</h1>
      <p>探索你感兴趣的蛋白质世界</p>
    </header>

    <!-- 家族筛选 -->
    <div class="family-filter">
      <span class="label">感兴趣的家族：</span>
      <div class="family-tags"
        <span 
          v-for="family in families" 
          :key="family"
          :class="['tag', { active: selectedFamilies.includes(family) }]"
          @click="toggleFamily(family)"
        >
          {{ family }}
        </span>
      </div>
      <button @click="getRecommendations" :disabled="loading">
        {{ loading ? '推荐中...' : '获取推荐' }}
      </button>
    </div>

    <!-- 推荐结果 -->
    <div v-if="recommendations.length > 0" class="recommendations">
      <h2>为你推荐</h2>
      <div class="protein-grid">
        <div 
          v-for="protein in recommendations" 
          :key="protein.id"
          class="protein-card"
        >
          <router-link :to="`/protein/${protein.id}`">
            <div class="protein-header">
              <h3>{{ protein.name }}</h3>
              <span class="family-badge">{{ protein.family }}</span>
            </div>
            <p class="description">{{ protein.description }}</p>
            
            <div class="score" v-if="protein.recommend_score">
              匹配度: {{ (protein.recommend_score * 100).toFixed(1) }}%
            </div>
          </router-link>
          
          <button 
            v-if="isLoggedIn"
            @click="followProtein(protein.id)"
            :disabled="protein.isFollowed"
            class="follow-btn"
          >
            {{ protein.isFollowed ? '已关注' : '+ 关注' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 随机探索 -->
    <div class="random-explore">
      <h2>随机探索</h2>
      <button @click="getRandomProteins" :disabled="randomLoading">
        {{ randomLoading ? '加载中...' : '换一批' }}
      </button>
      
      <div class="protein-grid">
        <div 
          v-for="protein in randomProteins" 
          :key="protein.id"
          class="protein-card"
        >
          <router-link :to="`/protein/${protein.id}`">
            <h3>{{ protein.name }}</h3>
            <span class="family-badge">{{ protein.family }}</span>
            <p>{{ protein.description }}</p>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const families = ref(['CIDE', 'PLIN', 'FSP', 'ATGL'])
const selectedFamilies = ref([])
const recommendations = ref([])
const randomProteins = ref([])
const loading = ref(false)
const randomLoading = ref(false)
const isLoggedIn = ref(false)

const toggleFamily = (family) => {
  const index = selectedFamilies.value.indexOf(family)
  if (index > -1) {
    selectedFamilies.value.splice(index, 1)
  } else {
    selectedFamilies.value.push(family)
  }
}

const getRecommendations = async () => {
  loading.value = true
  
  try {
    const response = await fetch('/api/recommend/cold-start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        selected_families: selectedFamilies.value,
        top_k: 6
      })
    })
    
    if (response.ok) {
      const data = await response.json()
      recommendations.value = data.recommendations || []
    }
  } catch (err) {
    console.error('获取推荐失败:', err)
  } finally {
    loading.value = false
  }
}

const getRandomProteins = async () => {
  randomLoading.value = true
  
  try {
    const response = await fetch('/api/recommend/explore?top_k=4')
    if (response.ok) {
      const data = await response.json()
      randomProteins.value = data.recommendations || []
    }
  } catch (err) {
    console.error('获取失败:', err)
  } finally {
    randomLoading.value = false
  }
}

const followProtein = async (proteinId) => {
  const token = localStorage.getItem('access_token')
  if (!token) return
  
  try {
    const response = await fetch(`/api/proteins/${proteinId}/follow`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    if (response.ok) {
      // 标记为已关注
      const protein = recommendations.value.find(p => p.id === proteinId)
      if (protein) protein.isFollowed = true
    }
  } catch (err) {
    console.error('关注失败:', err)
  }
}

onMounted(() => {
  isLoggedIn.value = !!localStorage.getItem('access_token')
  getRandomProteins()
})
</script>

<style scoped>
.explore-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

header {
  text-align: center;
  margin-bottom: 32px;
}

h1 {
  font-size: 28px;
  margin-bottom: 8px;
}

.family-filter {
  background: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.label {
  font-weight: 500;
  margin-bottom: 12px;
  display: block;
}

.family-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.tag {
  padding: 6px 16px;
  border-radius: 16px;
  background: #f0f0f0;
  cursor: pointer;
  transition: all 0.2s;
}

.tag.active {
  background: #409eff;
  color: white;
}

button {
  padding: 10px 24px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

button:disabled {
  background: #a0cfff;
}

.recommendations, .random-explore {
  margin-bottom: 40px;
}

h2 {
  font-size: 20px;
  margin-bottom: 16px;
}

.protein-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.protein-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  position: relative;
}

.protein-card a {
  text-decoration: none;
  color: inherit;
}

.protein-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

h3 {
  font-size: 18px;
  color: #333;
}

.family-badge {
  background: #e6f7ff;
  color: #1890ff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.description {
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 12px;
}

.score {
  font-size: 12px;
  color: #67c23a;
  margin-bottom: 12px;
}

.follow-btn {
  width: 100%;
  padding: 8px;
  background: #67c23a;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.follow-btn:disabled {
  background: #b3e19d;
  cursor: default;
}
</style>

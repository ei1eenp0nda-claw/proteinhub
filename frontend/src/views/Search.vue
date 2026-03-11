<template>
  <div class="search-page">
    <div class="search-header">
      <div class="search-box"
        <input
          v-model="searchQuery"
          @input="handleInput"
          @keyup.enter="performSearch"
          type="text"
          placeholder="搜索蛋白质、文献、家族..."
          class="search-input"
        />
        <button @click="performSearch" class="search-btn">
          🔍 搜索
        </button>
      </div>
      
      <!-- 搜索建议 -->
      <div v-if="suggestions.length > 0 && showSuggestions" class="suggestions">
        <div
          v-for="(item, index) in suggestions"
          :key="index"
          @click="selectSuggestion(item)"
          class="suggestion-item"
        >
          <span class="suggestion-type">{{ item.type === 'protein' ? '🧬' : '📁' }}</span>
          <span class="suggestion-value">{{ item.value }}</span>
          <span v-if="item.family" class="suggestion-family">{{ item.family }}</span>
        </div>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-if="hasSearched" class="search-results">
      <!-- 蛋白结果 -->
      <section v-if="proteinResults.items.length > 0" class="result-section">
        <h2>蛋白质 ({{ proteinResults.total }})</h2>
        <div class="protein-list"
          <div
            v-for="protein in proteinResults.items"
            :key="protein.id"
            class="protein-item"
          >
            <router-link :to="`/protein/${protein.id}`">
              <h3>{{ protein.name }}</h3>
              <span class="family-tag">{{ protein.family }}</span>
              <p>{{ protein.description }}</p>
              
              <div v-if="protein.search_score" class="relevance">
                相关度: {{ (protein.search_score * 100).toFixed(0) }}%
              </div>
            </router-link>
          </div>
        </div>
        
        <!-- 分页 -->
        <div v-if="proteinResults.pages > 1" class="pagination">
          <button 
            @click="changePage(currentPage - 1)"
            :disabled="currentPage === 1"
          >上一页</button>
          
          <span>{{ currentPage }} / {{ proteinResults.pages }}</span>
          
          <button 
            @click="changePage(currentPage + 1)"
            :disabled="currentPage === proteinResults.pages"
          >下一页</button>
        </div>
      </section>

      <!-- 帖子结果 -->
      <section v-if="postResults.items.length > 0" class="result-section">
        <h2>文献解读 ({{ postResults.total }})</h2>
        <div class="post-list"
          <div
            v-for="post in postResults.items"
            :key="post.id"
            class="post-item"
          >
            <router-link :to="`/protein/${post.protein_id}`">
              <h3>{{ post.title }}</h3>
              <p>{{ post.summary }}</p>
              <div class="meta">
                <span>{{ post.protein_name }}</span>
                <span>{{ formatDate(post.created_at) }}</span>
              </div>
            </router-link>
          </div>
        </div>
      </section>

      <!-- 无结果 -->
      <div v-if="noResults" class="no-results">
        未找到 "{{ searchQuery }}" 相关结果
        <p>建议：</p>
        <ul>
          <li>检查拼写</li>
          <li>尝试更简短的关键词</li>
          <li>搜索蛋白家族名称（如 CIDE、PLIN）</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const searchQuery = ref('')
const suggestions = ref([])
const showSuggestions = ref(false)
const hasSearched = ref(false)
const currentPage = ref(1)

const proteinResults = ref({ items: [], total: 0, pages: 0 })
const postResults = ref({ items: [], total: 0 })

const noResults = computed(() => {
  return hasSearched.value && 
         proteinResults.value.items.length === 0 && 
         postResults.value.items.length === 0
})

let debounceTimer = null

const handleInput = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    if (searchQuery.value.length >= 2) {
      fetchSuggestions()
    } else {
      suggestions.value = []
      showSuggestions.value = false
    }
  }, 300)
}

const fetchSuggestions = async () => {
  try {
    const response = await fetch(
      `/api/search/suggestions?q=${encodeURIComponent(searchQuery.value)}`
    )
    
    if (response.ok) {
      const data = await response.json()
      suggestions.value = data.suggestions || []
      showSuggestions.value = suggestions.value.length > 0
    }
  } catch (err) {
    console.error('获取建议失败:', err)
  }
}

const selectSuggestion = (item) => {
  searchQuery.value = item.value
  showSuggestions.value = false
  
  if (item.type === 'protein' && item.id) {
    router.push(`/protein/${item.id}`)
  } else {
    performSearch()
  }
}

const performSearch = async () => {
  if (!searchQuery.value.trim()) return
  
  hasSearched.value = true
  showSuggestions.value = false
  currentPage.value = 1
  
  await fetchResults()
}

const fetchResults = async () => {
  try {
    const query = encodeURIComponent(searchQuery.value)
    const response = await fetch(
      `/api/search?q=${query}&page=${currentPage.value}&per_page=10`
    )
    
    if (response.ok) {
      const data = await response.json()
      proteinResults.value = data.proteins || { items: [], total: 0, pages: 0 }
      postResults.value = data.posts || { items: [], total: 0 }
    }
  } catch (err) {
    console.error('搜索失败:', err)
  }
}

const changePage = (page) => {
  currentPage.value = page
  fetchResults()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

// 从 URL 参数初始化
watch(() => route.query.q, (newQuery) => {
  if (newQuery) {
    searchQuery.value = newQuery
    performSearch()
  }
}, { immediate: true })
</script>

<style scoped>
.search-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.search-header {
  position: relative;
  margin-bottom: 32px;
}

.search-box {
  display: flex;
  gap: 12px;
}

.search-input {
  flex: 1;
  padding: 14px 20px;
  font-size: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: #409eff;
}

.search-btn {
  padding: 14px 28px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.search-btn:hover {
  background: #66b1ff;
}

.suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-top: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  z-index: 100;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.suggestion-item:hover {
  background: #f5f5f5;
}

.suggestion-type {
  font-size: 20px;
}

.suggestion-value {
  flex: 1;
  font-weight: 500;
}

.suggestion-family {
  color: #999;
  font-size: 12px;
}

.result-section {
  margin-bottom: 40px;
}

.result-section h2 {
  font-size: 18px;
  margin-bottom: 16px;
  color: #333;
}

.protein-item, .post-item {
  background: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.protein-item a, .post-item a {
  text-decoration: none;
  color: inherit;
  display: block;
}

.protein-item h3 {
  font-size: 18px;
  color: #333;
  margin-bottom: 8px;
}

.family-tag {
  display: inline-block;
  background: #e6f7ff;
  color: #1890ff;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  margin-bottom: 8px;
}

.protein-item p {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
}

.relevance {
  margin-top: 8px;
  font-size: 12px;
  color: #67c23a;
}

.post-item h3 {
  font-size: 16px;
  margin-bottom: 8px;
  color: #333;
}

.post-item p {
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 12px;
}

.meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 24px;
}

.pagination button {
  padding: 8px 16px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.no-results {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.no-results p {
  margin-top: 16px;
  font-weight: 500;
}

.no-results ul {
  margin-top: 12px;
  text-align: left;
  display: inline-block;
}

.no-results li {
  margin: 8px 0;
}
</style>

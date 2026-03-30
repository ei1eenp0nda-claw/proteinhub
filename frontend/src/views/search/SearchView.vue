<template>
  <div class="search-view">
    <div class="search-header">
      <div class="search-box">
        <el-input
          v-model="searchQuery"
          placeholder="搜索笔记、作者、标签..."
          size="large"
          class="search-input"
          @keyup.enter="performSearch"
        >
          <template #append>
            <el-button @click="performSearch">
              <Search />
            </el-button>
          </template>
        </el-input>
      </div>

      <div class="hot-keywords" v-if="!hasSearched">
        <span class="label">热门搜索：</span>
        <span
          v-for="keyword in hotKeywords"
          :key="keyword"
          class="keyword-tag"
          @click="searchByKeyword(keyword)"
        >
          {{ keyword }}
        </span>
      </div>
    </div>

    <div class="search-content" v-if="hasSearched">
      <div class="search-filters">
        <div class="filter-tabs">
          <span
            v-for="tab in filterTabs"
            :key="tab.value"
            class="filter-tab"
            :class="{ active: currentFilter === tab.value }"
            @click="currentFilter = tab.value"
          >
            {{ tab.label }}
          </span>
        </div>

        <el-select v-model="sortBy" size="small" style="width: 120px">
          <el-option label="综合排序" value="relevance" />
          <el-option label="最新发布" value="newest" />
          <el-option label="最多点赞" value="likes" />
          <el-option label="最多浏览" value="views" />
        </el-select>
      </div>

      <div class="search-results">
        <div class="results-header">
          <p>找到 {{ results.length }} 个结果</p>
        </div>

        <!-- 笔记结果 -->
        <WaterfallLayout :items="results" :columnCount="isMobile ? 2 : 5">
          <template #default="{ item }">
            <NoteCard :note="item" />
          </template>
        </WaterfallLayout>

        <!-- 用户结果 -->
        <div v-if="currentFilter === 'users'" class="users-results">
          <div
            v-for="user in userResults"
            :key="user.id"
            class="user-item"
            @click="$router.push(`/user/${user.id}`)"
          >
            <el-avatar :size="60" :src="user.avatar">
              {{ user.nickname?.charAt(0) }}
            </el-avatar>
            <div class="user-info">
              <h4>{{ user.nickname }}</h4>
              <p>{{ user.bio }}</p>
              <span>{{ user.noteCount }} 笔记 · {{ user.followerCount }} 粉丝</span>
            </div>
            <el-button type="primary" size="small">+ 关注</el-button>
          </div>
        </div>

        <div v-if="results.length === 0" class="empty-state">
          <el-empty description="没有找到相关结果">
            <template #description>
              <p>没有找到 "{{ searchQuery }}" 的相关结果</p>
              <p class="suggestions">建议：检查拼写、尝试更通用的关键词</p>
            </template>
          </el-empty>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import WaterfallLayout from '@/components/common/WaterfallLayout.vue'
import NoteCard from '@/components/note/NoteCard.vue'
import { searchApi } from '@/api'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const isMobile = computed(() => appStore.isMobile)

const searchQuery = ref('')
const hasSearched = ref(false)
const currentFilter = ref('all')
const sortBy = ref('relevance')
const results = ref([])
const userResults = ref([])

const hotKeywords = ['CRISPR', '免疫治疗', '单细胞测序', 'Western Blot', '细胞培养']

const filterTabs = [
  { label: '全部', value: 'all' },
  { label: '笔记', value: 'notes' },
  { label: '用户', value: 'users' },
]

// 模拟搜索结果
const mockResults = [
  {
    id: 1,
    title: 'CRISPR-Cas9 基因编辑技术的最新进展',
    summary: '本文综述了CRISPR-Cas9技术在基因治疗领域的最新应用...',
    coverImage: 'https://picsum.photos/300/400?random=1',
    author: { id: 1, nickname: '生物研究员小王', avatar: '' },
    tags: ['基因编辑', 'CRISPR', '研究进展'],
    viewCount: 1234,
    likeCount: 89,
    isLiked: false,
  },
  {
    id: 2,
    title: 'Western Blot 实验技巧分享',
    summary: '总结了我三年WB实验的经验...',
    coverImage: 'https://picsum.photos/300/350?random=2',
    author: { id: 2, nickname: '实验小能手', avatar: '' },
    tags: ['实验方法', 'Western Blot'],
    viewCount: 2345,
    likeCount: 156,
    isLiked: false,
  },
]

const performSearch = () => {
  if (!searchQuery.value.trim()) return
  
  hasSearched.value = true
  router.push({ query: { q: searchQuery.value } })
  
  // 模拟搜索
  results.value = mockResults.filter(n => 
    n.title.includes(searchQuery.value) || 
    n.summary.includes(searchQuery.value)
  )
}

const searchByKeyword = (keyword) => {
  searchQuery.value = keyword
  performSearch()
}

onMounted(() => {
  if (route.query.q) {
    searchQuery.value = route.query.q
    performSearch()
  }
})

watch(() => route.query.q, (newQuery) => {
  if (newQuery) {
    searchQuery.value = newQuery
    performSearch()
  }
})
</script>

<style scoped>
.search-view {
  min-height: 100vh;
  background: #f5f5f5;
}

.search-header {
  background: #fff;
  padding: 40px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.search-box {
  max-width: 600px;
  margin: 0 auto 24px;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 24px;
}

.hot-keywords {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
}

.label {
  font-size: 14px;
  color: #999;
}

.keyword-tag {
  display: inline-block;
  padding: 4px 12px;
  margin: 0 6px;
  background: #f5f5f5;
  border-radius: 16px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
}

.keyword-tag:hover {
  background: rgba(255, 36, 66, 0.1);
  color: #ff2442;
}

.search-content {
  max-width: 1440px;
  margin: 0 auto;
  padding: 24px;
}

.search-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.filter-tabs {
  display: flex;
  gap: 24px;
}

.filter-tab {
  font-size: 15px;
  color: #666;
  cursor: pointer;
  padding: 8px 0;
  position: relative;
  transition: color 0.3s;
}

.filter-tab:hover {
  color: #ff2442;
}

.filter-tab.active {
  color: #ff2442;
  font-weight: 500;
}

.filter-tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: #ff2442;
  border-radius: 1px;
}

.results-header {
  margin-bottom: 16px;
  color: #999;
  font-size: 14px;
}

.users-results {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #fff;
  border-radius: 12px;
  cursor: pointer;
  transition: box-shadow 0.3s;
}

.user-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.user-info {
  flex: 1;
}

.user-info h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.user-info p {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.user-info span {
  font-size: 12px;
  color: #999;
}

.empty-state {
  padding: 60px 0;
}

.suggestions {
  font-size: 13px;
  color: #999;
  margin-top: 8px;
}

@media (max-width: 768px) {
  .search-header {
    padding: 20px 16px;
  }

  .search-content {
    padding: 16px;
  }

  .search-filters {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
}
</style>
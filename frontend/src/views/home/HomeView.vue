<template>
  <div class="home-view">
    <!-- 分类筛选栏 -->
    <div class="category-bar" :class="{ sticky: isScrolled }">
      <div class="category-container">
        <div
          v-for="cat in categories"
          :key="cat.value"
          class="category-item"
          :class="{ active: currentCategory === cat.value }"
          @click="selectCategory(cat.value)"
        >
          {{ cat.label }}
        </div>
      </div>
    </div>

    <!-- 瀑布流内容 -->
    <div class="content-container">
      <WaterfallLayout :items="notes" :columnCount="isMobile ? 2 : 5">
        <template #default="{ item }">
          <NoteCard :note="item" @update="updateNote" />
        </template>
      </WaterfallLayout>

      <!-- 加载更多 -->
      <div v-if="loading" class="loading-more">
        <el-skeleton :rows="3" animated />
      </div>
      
      <div v-else-if="!hasMore" class="no-more">
        已经到底啦 ~
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/app'
import WaterfallLayout from '@/components/common/WaterfallLayout.vue'
import NoteCard from '@/components/note/NoteCard.vue'
import { noteApi } from '@/api'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()
const isMobile = computed(() => appStore.isMobile)

const categories = [
  { label: '推荐', value: 'all' },
  { label: '研究进展', value: 'research' },
  { label: '实验方法', value: 'method' },
  { label: '文献解读', value: 'literature' },
  { label: '经验分享', value: 'experience' },
]

const currentCategory = ref('all')
const notes = ref([])
const loading = ref(false)
const hasMore = ref(true)
const page = ref(1)
const isScrolled = ref(false)

// 模拟数据
const mockNotes = [
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
    summary: '总结了我三年WB实验的经验，包括转膜、封闭、抗体孵育等关键步骤...',
    coverImage: 'https://picsum.photos/300/350?random=2',
    author: { id: 2, nickname: '实验小能手', avatar: '' },
    tags: ['实验方法', 'Western Blot'],
    viewCount: 2345,
    likeCount: 156,
    isLiked: true,
  },
  {
    id: 3,
    title: 'Nature 最新癌症免疫治疗论文解读',
    summary: '这是一篇关于PD-1/PD-L1抑制剂在肺癌治疗中的突破性研究...',
    coverImage: 'https://picsum.photos/300/450?random=3',
    author: { id: 3, nickname: '文献解读君', avatar: '' },
    tags: ['文献解读', '免疫治疗', '癌症'],
    viewCount: 3456,
    likeCount: 234,
    isLiked: false,
  },
  {
    id: 4,
    title: '细胞培养常见问题及解决方案',
    summary: '细胞污染、生长缓慢、贴壁不良...这些问题你遇到过吗？',
    coverImage: 'https://picsum.photos/300/380?random=4',
    author: { id: 4, nickname: '细胞培养达人', avatar: '' },
    tags: ['细胞培养', '经验分享'],
    viewCount: 5678,
    likeCount: 345,
    isLiked: false,
  },
  {
    id: 5,
    title: '单细胞测序数据分析入门',
    summary: '从Seurat包安装到降维聚类，手把手教你做单细胞分析...',
    coverImage: 'https://picsum.photos/300/420?random=5',
    author: { id: 5, nickname: '生物信息小白', avatar: '' },
    tags: ['生物信息', '单细胞', '数据分析'],
    viewCount: 4567,
    likeCount: 278,
    isLiked: true,
  },
  {
    id: 6,
    title: '流式细胞术实验protocol',
    summary: '完整的流式细胞术实验流程，包括样品制备、染色、上机分析...',
    coverImage: 'https://picsum.photos/300/360?random=6',
    author: { id: 6, nickname: '流式专家', avatar: '' },
    tags: ['流式细胞术', '实验方法'],
    viewCount: 2890,
    likeCount: 167,
    isLiked: false,
  },
  {
    id: 7,
    title: '蛋白质纯化经验总结',
    summary: 'His-tag、GST-tag、MBP-tag等各种标签蛋白纯化经验分享...',
    coverImage: 'https://picsum.photos/300/400?random=7',
    author: { id: 7, nickname: '蛋白纯化师', avatar: '' },
    tags: ['蛋白纯化', '经验分享'],
    viewCount: 1890,
    likeCount: 123,
    isLiked: false,
  },
  {
    id: 8,
    title: '2024年肿瘤免疫治疗研究热点',
    summary: '盘点今年肿瘤免疫领域最受关注的几个研究方向...',
    coverImage: 'https://picsum.photos/300/440?random=8',
    author: { id: 8, nickname: '肿瘤研究者', avatar: '' },
    tags: ['肿瘤免疫', '研究进展'],
    viewCount: 6789,
    likeCount: 456,
    isLiked: false,
  },
]

const fetchNotes = async () => {
  if (loading.value || !hasMore.value) return
  
  loading.value = true
  try {
    // 实际使用时调用API
    // const res = await noteApi.getNotes({
    //   category: currentCategory.value,
    //   page: page.value,
    //   pageSize: 20,
    // })
    // notes.value.push(...res.data)
    
    // 模拟延迟和分页
    await new Promise(resolve => setTimeout(resolve, 500))
    const start = (page.value - 1) * 8
    const newNotes = mockNotes.slice(start, start + 8).map((note, idx) => ({
      ...note,
      id: page.value * 100 + idx,
      coverImage: `https://picsum.photos/300/${350 + Math.random() * 100}?random=${page.value * 100 + idx}`,
    }))
    
    if (newNotes.length < 8) {
      hasMore.value = false
    }
    
    notes.value.push(...newNotes)
    page.value++
  } catch (error) {
    ElMessage.error('加载失败，请重试')
  } finally {
    loading.value = false
  }
}

const selectCategory = (value) => {
  currentCategory.value = value
  notes.value = []
  page.value = 1
  hasMore.value = true
  fetchNotes()
}

const updateNote = (updatedNote) => {
  const index = notes.value.findIndex(n => n.id === updatedNote.id)
  if (index !== -1) {
    notes.value[index] = updatedNote
  }
}

// 无限滚动
const handleScroll = () => {
  const scrollTop = window.scrollY
  const windowHeight = window.innerHeight
  const documentHeight = document.documentElement.scrollHeight
  
  isScrolled.value = scrollTop > 50
  
  if (scrollTop + windowHeight >= documentHeight - 200) {
    fetchNotes()
  }
}

onMounted(() => {
  fetchNotes()
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.home-view {
  min-height: 100vh;
}

.category-bar {
  background: #fff;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
  transition: box-shadow 0.3s;
}

.category-bar.sticky {
  position: fixed;
  top: 60px;
  left: 0;
  right: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.category-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  gap: 32px;
  overflow-x: auto;
  scrollbar-width: none;
}

.category-container::-webkit-scrollbar {
  display: none;
}

.category-item {
  font-size: 15px;
  color: #666;
  cursor: pointer;
  white-space: nowrap;
  padding: 8px 0;
  position: relative;
  transition: color 0.3s;
}

.category-item:hover {
  color: #ff2442;
}

.category-item.active {
  color: #ff2442;
  font-weight: 600;
}

.category-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 3px;
  background: #ff2442;
  border-radius: 2px;
}

.content-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 24px;
}

.loading-more {
  padding: 40px 0;
  text-align: center;
}

.no-more {
  padding: 40px 0;
  text-align: center;
  color: #999;
  font-size: 14px;
}

@media (max-width: 768px) {
  .category-bar {
    padding: 12px 0;
  }

  .category-bar.sticky {
    top: 50px;
  }

  .category-container {
    padding: 0 16px;
    gap: 20px;
  }

  .category-item {
    font-size: 14px;
  }

  .content-container {
    padding: 12px;
  }
}
</style>
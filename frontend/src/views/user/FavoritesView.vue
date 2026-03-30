<template>
  <div class="favorites-view">
    <div class="favorites-container">
      <div class="page-header">
        <h2>我的收藏</h2>
        <p class="subtitle">共 {{ favorites.length }} 篇笔记</p>
      </div>

      <WaterfallLayout :items="favorites" :columnCount="isMobile ? 2 : 5">
        <template #default="{ item }">
          <NoteCard :note="item" @update="updateFavorite" />
        </template>
      </WaterfallLayout>

      <div v-if="favorites.length === 0" class="empty-state">
        <el-empty description="还没有收藏任何笔记">
          <el-button type="primary" @click="$router.push('/')">去发现</el-button>
        </el-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/app'
import WaterfallLayout from '@/components/common/WaterfallLayout.vue'
import NoteCard from '@/components/note/NoteCard.vue'
import { userApi } from '@/api'

const appStore = useAppStore()
const isMobile = computed(() => appStore.isMobile)

const favorites = ref([])

// 模拟数据
favorites.value = [
  {
    id: 1,
    title: '细胞培养常见问题及解决方案',
    summary: '细胞污染、生长缓慢、贴壁不良...这些问题你遇到过吗？',
    coverImage: 'https://picsum.photos/300/380?random=4',
    author: { id: 4, nickname: '细胞培养达人', avatar: '' },
    tags: ['细胞培养', '经验分享'],
    viewCount: 5678,
    likeCount: 345,
    isLiked: false,
    isFavorited: true,
  },
  {
    id: 2,
    title: '单细胞测序数据分析入门',
    summary: '从Seurat包安装到降维聚类，手把手教你做单细胞分析...',
    coverImage: 'https://picsum.photos/300/420?random=5',
    author: { id: 5, nickname: '生物信息小白', avatar: '' },
    tags: ['生物信息', '单细胞', '数据分析'],
    viewCount: 4567,
    likeCount: 278,
    isLiked: true,
    isFavorited: true,
  },
]

const updateFavorite = (updatedNote) => {
  const index = favorites.value.findIndex(n => n.id === updatedNote.id)
  if (index !== -1) {
    if (!updatedNote.isFavorited) {
      favorites.value.splice(index, 1)
    } else {
      favorites.value[index] = updatedNote
    }
  }
}
</script>

<style scoped>
.favorites-view {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 24px;
}

.favorites-container {
  max-width: 1440px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.subtitle {
  font-size: 14px;
  color: #999;
  margin-top: 8px;
}

.empty-state {
  padding: 60px 0;
}
</style>
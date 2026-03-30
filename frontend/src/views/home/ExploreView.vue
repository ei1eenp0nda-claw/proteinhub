<template>
  <div class="explore-view">
    <!-- Banner 轮播 -->
    <div class="explore-banner">
      <el-carousel height="320px" :interval="5000">
        <el-carousel-item v-for="banner in banners" :key="banner.id">
          <div
            class="banner-item"
            :style="{ backgroundImage: `url(${banner.image})` }"
            @click="$router.push(banner.link)"
          >
            <div class="banner-content">
              <h2>{{ banner.title }}</h2>
              <p>{{ banner.subtitle }}</p>
            </div>
          </div>
        </el-carousel-item>
      </el-carousel>
    </div>

    <!-- 热门标签 -->
    <div class="hot-tags-section">
      <div class="section-header">
        <h3>热门标签</h3>
      </div>
      <div class="tags-list">
        <div
          v-for="tag in hotTags"
          :key="tag.name"
          class="tag-item"
          :style="{ fontSize: tag.size + 'px' }"
          @click="searchByTag(tag.name)"
        >
          {{ tag.name }}
        </div>
      </div>
    </div>

    <!-- 推荐作者 -->
    <div class="recommended-authors">
      <div class="section-header">
        <h3>推荐关注</h3>
        <a href="#" @click.prevent="refreshAuthors">换一批</a>
      </div>
      <div class="authors-grid">
        <div
          v-for="author in recommendedAuthors"
          :key="author.id"
          class="author-card"
        >
          <el-avatar :size="64" :src="author.avatar">
            {{ author.nickname?.charAt(0) }}
          </el-avatar>
          <h4>{{ author.nickname }}</h4>
          <p>{{ author.bio }}</p>
          <el-button
            type="primary"
            size="small"
            :class="{ 'is-followed': author.isFollowed }"
            @click="toggleFollow(author)"
          >
            {{ author.isFollowed ? '已关注' : '+ 关注' }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- 热门内容 -->
    <div class="hot-content">
      <div class="section-header">
        <h3>热门笔记</h3>
      </div>
      <WaterfallLayout :items="hotNotes" :columnCount="isMobile ? 2 : 4">
        <template #default="{ item }">
          <NoteCard :note="item" />
        </template>
      </WaterfallLayout>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import WaterfallLayout from '@/components/common/WaterfallLayout.vue'
import NoteCard from '@/components/note/NoteCard.vue'

const router = useRouter()
const appStore = useAppStore()
const isMobile = computed(() => appStore.isMobile)

const banners = [
  {
    id: 1,
    title: '2024年生物医学研究热点',
    subtitle: '探索前沿科技，分享科研心得',
    image: 'https://picsum.photos/1200/400?random=10',
    link: '/search?q=2024热点',
  },
  {
    id: 2,
    title: '新手实验技巧大赛',
    subtitle: '分享你的实验技巧，赢取精美礼品',
    image: 'https://picsum.photos/1200/400?random=11',
    link: '/search?q=实验技巧',
  },
  {
    id: 3,
    title: '文献解读达人招募',
    subtitle: '加入我们的解读团队，影响更多科研人',
    image: 'https://picsum.photos/1200/400?random=12',
    link: '/search?q=文献解读',
  },
]

const hotTags = [
  { name: 'CRISPR', size: 24 },
  { name: '免疫治疗', size: 20 },
  { name: '单细胞测序', size: 18 },
  { name: '蛋白质组学', size: 22 },
  { name: '基因编辑', size: 16 },
  { name: '癌症研究', size: 19 },
  { name: '干细胞', size: 17 },
  { name: '神经科学', size: 15 },
  { name: '生物信息学', size: 21 },
  { name: '疫苗研发', size: 14 },
]

const recommendedAuthors = ref([
  {
    id: 1,
    nickname: '基因编辑专家',
    avatar: '',
    bio: 'CRISPR技术研究者，分享最新基因编辑进展',
    isFollowed: false,
  },
  {
    id: 2,
    nickname: '免疫学博士',
    avatar: '',
    bio: '肿瘤免疫治疗领域，专注CAR-T研究',
    isFollowed: true,
  },
  {
    id: 3,
    nickname: '细胞培养达人',
    avatar: '',
    bio: '十年细胞培养经验，解决各种培养难题',
    isFollowed: false,
  },
  {
    id: 4,
    nickname: '生物信息小白',
    avatar: '',
    bio: '从零开始学习生物信息，记录成长历程',
    isFollowed: false,
  },
])

const hotNotes = ref([
  {
    id: 101,
    title: 'Science最新：人工智能预测蛋白质结构',
    summary: 'DeepMind团队发表最新研究成果...',
    coverImage: 'https://picsum.photos/300/400?random=20',
    author: { id: 1, nickname: 'AI生物', avatar: '' },
    tags: ['AI', '蛋白质结构', 'Science'],
    viewCount: 12345,
    likeCount: 890,
    isLiked: false,
  },
  {
    id: 102,
    title: 'RT-PCR实验 troubleshooting 指南',
    summary: '总结了RT-PCR常见问题及解决方案...',
    coverImage: 'https://picsum.photos/300/380?random=21',
    author: { id: 2, nickname: '实验小能手', avatar: '' },
    tags: ['PCR', '实验方法'],
    viewCount: 8765,
    likeCount: 654,
    isLiked: true,
  },
  {
    id: 103,
    title: 'Nature Medicine：mRNA疫苗新进展',
    summary: ' Moderna公司最新临床试验结果公布...',
    coverImage: 'https://picsum.photos/300/420?random=22',
    author: { id: 3, nickname: '疫苗追踪', avatar: '' },
    tags: ['mRNA', '疫苗', 'Nature'],
    viewCount: 9876,
    likeCount: 765,
    isLiked: false,
  },
  {
    id: 104,
    title: '流式细胞术抗体选择指南',
    summary: '如何选择合适的荧光抗体，避免补偿错误...',
    coverImage: 'https://picsum.photos/300/360?random=23',
    author: { id: 4, nickname: '流式专家', avatar: '' },
    tags: ['流式', '抗体'],
    viewCount: 5432,
    likeCount: 432,
    isLiked: false,
  },
])

const searchByTag = (tag) => {
  router.push(`/search?q=${encodeURIComponent(tag)}`)
}

const toggleFollow = (author) => {
  author.isFollowed = !author.isFollowed
}

const refreshAuthors = () => {
  // 刷新推荐作者
}
</script>

<style scoped>
.explore-view {
  max-width: 1440px;
  margin: 0 auto;
  padding: 24px;
}

.explore-banner {
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 40px;
}

.banner-item {
  height: 100%;
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: flex-end;
  cursor: pointer;
}

.banner-content {
  padding: 40px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7), transparent);
  color: #fff;
  width: 100%;
}

.banner-content h2 {
  font-size: 28px;
  margin-bottom: 8px;
}

.banner-content p {
  font-size: 16px;
  opacity: 0.9;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.section-header a {
  font-size: 14px;
  color: #ff2442;
  text-decoration: none;
}

.hot-tags-section {
  margin-bottom: 40px;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 20px;
  background: #fff;
  border-radius: 12px;
}

.tag-item {
  color: #666;
  cursor: pointer;
  transition: color 0.3s;
}

.tag-item:hover {
  color: #ff2442;
}

.recommended-authors {
  margin-bottom: 40px;
}

.authors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
}

.author-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  transition: transform 0.3s, box-shadow 0.3s;
}

.author-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.author-card h4 {
  margin: 12px 0 8px;
  font-size: 16px;
  color: #333;
}

.author-card p {
  font-size: 13px;
  color: #999;
  margin-bottom: 16px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.is-followed {
  background: #f0f0f0;
  border-color: #f0f0f0;
  color: #999;
}

.hot-content {
  margin-bottom: 40px;
}

@media (max-width: 768px) {
  .explore-view {
    padding: 12px;
  }

  .explore-banner {
    margin-bottom: 24px;
  }

  .banner-content {
    padding: 20px;
  }

  .banner-content h2 {
    font-size: 20px;
  }

  .authors-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .author-card {
    padding: 16px;
  }
}
</style>
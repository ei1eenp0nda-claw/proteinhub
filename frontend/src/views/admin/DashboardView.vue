<template>
  <div class="dashboard-view">
    <!-- 统计卡片 -->
    <div class="stats-row">
      <div v-for="stat in stats" :key="stat.title" class="stat-card">
        <div class="stat-icon" :style="{ background: stat.color }">
          <component :is="stat.icon" />
        </div>
        <div class="stat-info">
          <p class="stat-title">{{ stat.title }}</p>
          <p class="stat-value">{{ stat.value }}</p>
          <p class="stat-change" :class="stat.trend">
            <ArrowUp v-if="stat.trend === 'up'" />
            <ArrowDown v-else />
            {{ stat.change }} 较上月
          </p>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-row">
      <div class="chart-card">
        <h3>内容趋势</h3>
        <div class="chart-placeholder">
          <div class="mock-chart">
            <div v-for="i in 7" :key="i" class="bar" :style="{ height: Math.random() * 60 + 40 + '%' }"></div>
          </div>
          <div class="chart-labels">
            <span v-for="day in ['周一', '周二', '周三', '周四', '周五', '周六', '周日']" :key="day">{{ day }}</span>
          </div>
        </div>
      </div>

      <div class="chart-card">
        <h3>用户增长</h3>
        <div class="chart-placeholder">
          <div class="mock-line">
            <svg viewBox="0 0 300 100">
              <path d="M0,80 Q50,60 100,70 T200,40 T300,20" fill="none" stroke="#ff2442" stroke-width="2" />
              <circle cx="300" cy="20" r="4" fill="#ff2442" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 待审核内容 -->
    <div class="pending-section">
      <div class="section-header">
        <h3>待审核笔记</h3>
        <el-button type="primary" text @click="$router.push('/admin/content')">查看全部</el-button>
      </div>

      <el-table :data="pendingNotes" style="width: 100%">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="author" label="作者" width="120" />
        <el-table-column prop="category" label="分类" width="100" />
        <el-table-column prop="createdAt" label="提交时间" width="150" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="approveNote(row)">通过</el-button>
            <el-button type="danger" size="small" @click="rejectNote(row)">拒绝</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Document, User, View, Star, ArrowUp, ArrowDown } from '@element-plus/icons-vue'
import { adminApi } from '@/api'
import { ElMessage } from 'element-plus'

const stats = ref([
  { title: '总笔记数', value: '1,234', change: '12%', trend: 'up', color: '#ff2442', icon: Document },
  { title: '总用户数', value: '5,678', change: '8%', trend: 'up', color: '#52c41a', icon: User },
  { title: '今日浏览', value: '12,345', change: '15%', trend: 'up', color: '#1890ff', icon: View },
  { title: '总点赞数', value: '45,678', change: '5%', trend: 'down', color: '#faad14', icon: Star },
])

const pendingNotes = ref([
  { id: 1, title: 'CRISPR实验protocol分享', author: '研究员小王', category: '实验方法', createdAt: '2024-01-15 14:30' },
  { id: 2, title: '肿瘤免疫治疗新进展', author: '免疫学博士', category: '研究进展', createdAt: '2024-01-15 13:20' },
  { id: 3, title: '细胞培养经验总结', author: '细胞达人', category: '经验分享', createdAt: '2024-01-15 12:10' },
])

const approveNote = async (note) => {
  try {
    await adminApi.approveNote(note.id)
    ElMessage.success('已通过')
    pendingNotes.value = pendingNotes.value.filter(n => n.id !== note.id)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const rejectNote = async (note) => {
  try {
    await adminApi.rejectNote(note.id, '内容不符合规范')
    ElMessage.success('已拒绝')
    pendingNotes.value = pendingNotes.value.filter(n => n.id !== note.id)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}
</script>

<style scoped>
.dashboard-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24px;
}

.stat-info {
  flex: 1;
}

.stat-title {
  font-size: 14px;
  color: #999;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.stat-change {
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-change.up {
  color: #52c41a;
}

.stat-change.down {
  color: #ff4d4f;
}

.charts-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.chart-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
}

.chart-card h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #333;
}

.chart-placeholder {
  height: 200px;
}

.mock-chart {
  height: 160px;
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  gap: 12px;
  padding: 0 20px;
}

.bar {
  flex: 1;
  background: linear-gradient(to top, #ff2442, #ff6b7a);
  border-radius: 4px 4px 0 0;
  transition: height 0.5s ease;
}

.chart-labels {
  display: flex;
  justify-content: space-around;
  margin-top: 12px;
  font-size: 12px;
  color: #999;
}

.mock-line {
  height: 160px;
  padding: 20px;
}

.mock-line svg {
  width: 100%;
  height: 100%;
}

.pending-section {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-row {
    grid-template-columns: 1fr;
  }
}
</style>
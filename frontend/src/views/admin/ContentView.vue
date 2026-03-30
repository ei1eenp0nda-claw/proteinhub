<template>
  <div class="content-view">
    <div class="page-header">
      <h2>内容管理</h2>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索笔记..."
          style="width: 240px"
          clearable
        >
          <template #suffix>
            <Search />
          </template>
        </el-input>
      </div>
    </div>

    <div class="filter-bar">
      <el-radio-group v-model="filterStatus">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="pending">待审核</el-radio-button>
        <el-radio-button label="approved">已通过</el-radio-button>
        <el-radio-button label="rejected">已拒绝</el-radio-button>
      </el-radio-group>

      <el-select v-model="filterCategory" placeholder="分类" clearable style="width: 120px">
        <el-option label="研究进展" value="research" />
        <el-option label="实验方法" value="method" />
        <el-option label="文献解读" value="literature" />
        <el-option label="经验分享" value="experience" />
      </el-select>
    </div>

    <el-table :data="filteredNotes" style="width: 100%" v-loading="loading">
      <el-table-column type="selection" width="55" />
      
      <el-table-column label="笔记信息" min-width="250">
        <template #default="{ row }">
          <div class="note-info">
            <img :src="row.coverImage" class="note-cover" />
            <div class="note-details">
              <p class="note-title">{{ row.title }}</p>
              <p class="note-author">{{ row.author }}</p>
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="category" label="分类" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ categoryMap[row.category] }}</el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType[row.status]" size="small">
            {{ statusMap[row.status] }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="viewCount" label="浏览" width="80" />
      <el-table-column prop="likeCount" label="点赞" width="80" />

      <el-table-column prop="createdAt" label="创建时间" width="150" />

      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="viewNote(row)">查看</el-button>
          
          <template v-if="row.status === 'pending'">
            <el-button link type="success" @click="approveNote(row)">通过</el-button>
            <el-button link type="danger" @click="rejectNote(row)">拒绝</el-button>
          </template>
          
          <el-button link type="danger" @click="deleteNote(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
      />
    </div>

    <!-- 拒绝弹窗 -->
    <el-dialog v-model="rejectDialogVisible" title="拒绝原因" width="400px">
      <el-input
        v-model="rejectReason"
        type="textarea"
        :rows="3"
        placeholder="请输入拒绝原因..."
      />
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmReject">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { adminApi, noteApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

const searchQuery = ref('')
const filterStatus = ref('all')
const filterCategory = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(100)
const loading = ref(false)
const rejectDialogVisible = ref(false)
const rejectReason = ref('')
const currentNote = ref(null)

const categoryMap = {
  research: '研究进展',
  method: '实验方法',
  literature: '文献解读',
  experience: '经验分享',
}

const statusMap = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已拒绝',
}

const statusType = {
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
}

const notes = ref([
  {
    id: 1,
    title: 'CRISPR-Cas9 基因编辑技术的最新进展',
    author: '生物研究员小王',
    coverImage: 'https://picsum.photos/100/100?random=1',
    category: 'research',
    status: 'pending',
    viewCount: 1234,
    likeCount: 89,
    createdAt: '2024-01-15 14:30',
  },
  {
    id: 2,
    title: 'Western Blot 实验技巧分享',
    author: '实验小能手',
    coverImage: 'https://picsum.photos/100/100?random=2',
    category: 'method',
    status: 'approved',
    viewCount: 2345,
    likeCount: 156,
    createdAt: '2024-01-15 10:20',
  },
  {
    id: 3,
    title: 'Nature 最新癌症免疫治疗论文解读',
    author: '文献解读君',
    coverImage: 'https://picsum.photos/100/100?random=3',
    category: 'literature',
    status: 'rejected',
    viewCount: 3456,
    likeCount: 234,
    createdAt: '2024-01-14 16:45',
  },
])

const filteredNotes = computed(() => {
  return notes.value.filter(note => {
    if (filterStatus.value !== 'all' && note.status !== filterStatus.value) {
      return false
    }
    if (filterCategory.value && note.category !== filterCategory.value) {
      return false
    }
    if (searchQuery.value && !note.title.includes(searchQuery.value)) {
      return false
    }
    return true
  })
})

const viewNote = (note) => {
  router.push(`/note/${note.id}`)
}

const approveNote = async (note) => {
  try {
    await adminApi.approveNote(note.id)
    note.status = 'approved'
    ElMessage.success('已通过')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const rejectNote = (note) => {
  currentNote.value = note
  rejectReason.value = ''
  rejectDialogVisible.value = true
}

const confirmReject = async () => {
  if (!rejectReason.value.trim()) {
    ElMessage.warning('请输入拒绝原因')
    return
  }
  try {
    await adminApi.rejectNote(currentNote.value.id, rejectReason.value)
    currentNote.value.status = 'rejected'
    rejectDialogVisible.value = false
    ElMessage.success('已拒绝')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deleteNote = async (note) => {
  try {
    await ElMessageBox.confirm('确定要删除这篇笔记吗？', '提示', {
      type: 'warning',
    })
    await noteApi.deleteNote(note.id)
    notes.value = notes.value.filter(n => n.id !== note.id)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}
</script>

<style scoped>
.content-view {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.note-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.note-cover {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 8px;
}

.note-details {
  flex: 1;
}

.note-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.note-author {
  font-size: 12px;
  color: #999;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
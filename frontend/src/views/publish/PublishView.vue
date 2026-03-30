<template>
  <div class="publish-view">
    <div class="publish-container">
      <div class="publish-header">
        <h2>{{ isEdit ? '编辑笔记' : '发布笔记' }}</h2>
        <div class="header-actions">
          <el-button @click="saveDraft">存草稿</el-button>
          <el-button type="primary" @click="publishNote">发布</el-button>
        </div>
      </div>

      <div class="publish-form">
        <!-- 标题 -->
        <div class="form-item">
          <el-input
            v-model="noteForm.title"
            placeholder="请输入标题（最多50字）"
            maxlength="50"
            show-word-limit
            size="large"
            class="title-input"
          />
        </div>

        <!-- 分类 -->
        <div class="form-item">
          <span class="form-label">分类：</span>
          <el-radio-group v-model="noteForm.category">
            <el-radio-button label="research">研究进展</el-radio-button>
            <el-radio-button label="method">实验方法</el-radio-button>
            <el-radio-button label="literature">文献解读</el-radio-button>
            <el-radio-button label="experience">经验分享</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 图片上传 -->
        <div class="form-item">
          <span class="form-label">图片：</span>
          <div class="image-uploader">
            <el-upload
              v-model:file-list="noteForm.images"
              action="/api/v1/upload/image"
              list-type="picture-card"
              :on-preview="handlePreview"
              :on-remove="handleRemove"
              :on-success="handleUploadSuccess"
              :before-upload="beforeUpload"
              :headers="uploadHeaders"
              multiple
              :limit="9"
            >
              <el-icon><Plus /></el-icon>
            </el-upload>
            <p class="upload-tip">最多可上传9张图片，支持 jpg/png 格式，单张不超过 10MB</p>
          </div>
        </div>

        <!-- 内容编辑 -->
        <div class="form-item">
          <span class="form-label">内容：</span>
          <div class="editor-wrapper">
            <el-tabs v-model="activeTab">
              <el-tab-pane label="可视化编辑" name="visual">
                <div class="visual-editor">
                  <el-input
                    v-model="noteForm.content"
                    type="textarea"
                    :rows="15"
                    placeholder="分享你的研究心得、实验技巧..."
                    class="content-textarea"
                  />
                  <div class="editor-toolbar">
                    <button @click="insertText('**粗体**')"><B /></button>
                    <button @click="insertText('*斜体*')"><I /></button>
                    <button @click="insertText('# 标题')">H1</button>
                    <button @click="insertText('## 标题')">H2</button>
                    <button @click="insertText('- 列表项')">列表</button>
                    <button @click="insertText('[链接文本](url)')">链接</button>
                  </div>
                </div>
              </el-tab-pane>
              
              <el-tab-pane label="Markdown" name="markdown">
                <el-input
                  v-model="noteForm.content"
                  type="textarea"
                  :rows="15"
                  placeholder="使用 Markdown 格式编写内容..."
                  class="content-textarea"
                />
              </el-tab-pane>
              
              <el-tab-pane label="预览" name="preview">
                <div class="preview-content" v-html="renderedContent"></div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </div>

        <!-- 标签 -->
        <div class="form-item">
          <span class="form-label">标签：</span>
          <div class="tags-wrapper">
            <el-tag
              v-for="tag in noteForm.tags"
              :key="tag"
              closable
              @close="removeTag(tag)"
              class="tag-item"
            >
              {{ tag }}
            </el-tag>
            <el-input
              v-if="inputVisible"
              ref="tagInputRef"
              v-model="inputValue"
              size="small"
              @keyup.enter="addTag"
              @blur="addTag"
              style="width: 100px"
            />
            <el-button v-else size="small" @click="showTagInput">+ 添加标签</el-button>
          </div>
          <p class="form-tip">添加相关标签，最多5个，帮助更多人发现你的笔记</p>
        </div>

        <!-- 摘要 -->
        <div class="form-item">
          <span class="form-label">摘要：</span>
          <el-input
            v-model="noteForm.summary"
            type="textarea"
            :rows="3"
            placeholder="输入摘要，如果不填将自动提取内容前100字"
            maxlength="200"
            show-word-limit
          />
        </div>

        <!-- 封面设置 -->
        <div class="form-item">
          <span class="form-label">封面：</span>
          <el-radio-group v-model="coverType">
            <el-radio label="auto">自动使用第一张图片</el-radio>
            <el-radio label="custom">自定义封面</el-radio>
          </el-radio-group>
          
          <div v-if="coverType === 'custom'" class="cover-selector">
            <div
              v-for="(img, idx) in noteForm.images"
              :key="idx"
              class="cover-option"
              :class="{ selected: noteForm.coverImage === img.url }"
              @click="selectCover(img.url)"
            >
              <img :src="img.url" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 图片预览 -->
    <el-dialog v-model="previewVisible">
      <img :src="previewImage" style="width: 100%" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import { useUserStore } from '@/stores/user'
import { noteApi } from '@/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isEdit = computed(() => !!route.params.id)
const activeTab = ref('visual')
const coverType = ref('auto')

const noteForm = ref({
  title: '',
  category: 'research',
  content: '',
  images: [],
  tags: [],
  summary: '',
  coverImage: '',
})

const inputVisible = ref(false)
const inputValue = ref('')
const tagInputRef = ref()
const previewVisible = ref(false)
const previewImage = ref('')

const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${userStore.token}`,
}))

const renderedContent = computed(() => {
  return marked(noteForm.value.content || '')
})

const insertText = (text) => {
  const textarea = document.querySelector('.content-textarea textarea')
  if (!textarea) return
  
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const value = noteForm.value.content
  
  noteForm.value.content = value.substring(0, start) + text + value.substring(end)
  
  nextTick(() => {
    textarea.focus()
    textarea.setSelectionRange(start + text.length, start + text.length)
  })
}

const showTagInput = () => {
  inputVisible.value = true
  nextTick(() => tagInputRef.value?.focus())
}

const addTag = () => {
  if (inputValue.value && !noteForm.value.tags.includes(inputValue.value)) {
    if (noteForm.value.tags.length >= 5) {
      ElMessage.warning('最多只能添加5个标签')
      return
    }
    noteForm.value.tags.push(inputValue.value)
  }
  inputVisible.value = false
  inputValue.value = ''
}

const removeTag = (tag) => {
  const index = noteForm.value.tags.indexOf(tag)
  if (index > -1) {
    noteForm.value.tags.splice(index, 1)
  }
}

const selectCover = (url) => {
  noteForm.value.coverImage = url
}

const beforeUpload = (file) => {
  const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isJpgOrPng) {
    ElMessage.error('只支持 JPG/PNG 格式!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过 10MB!')
    return false
  }
  return true
}

const handleUploadSuccess = (response, file) => {
  file.url = response.url
  if (coverType.value === 'auto' && !noteForm.value.coverImage) {
    noteForm.value.coverImage = response.url
  }
}

const handleRemove = () => {
  // 处理移除
}

const handlePreview = (file) => {
  previewImage.value = file.url
  previewVisible.value = true
}

const validateForm = () => {
  if (!noteForm.value.title.trim()) {
    ElMessage.warning('请输入标题')
    return false
  }
  if (!noteForm.value.content.trim()) {
    ElMessage.warning('请输入内容')
    return false
  }
  return true
}

const saveDraft = async () => {
  try {
    await noteApi.createNote({ ...noteForm.value, status: 'draft' })
    ElMessage.success('草稿保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const publishNote = async () => {
  if (!validateForm()) return

  try {
    if (isEdit.value) {
      await noteApi.updateNote(route.params.id, noteForm.value)
      ElMessage.success('笔记更新成功')
    } else {
      await noteApi.createNote({ ...noteForm.value, status: 'published' })
      ElMessage.success('笔记发布成功')
    }
    router.push('/')
  } catch (error) {
    ElMessage.error('发布失败')
  }
}
</script>

<style scoped>
.publish-view {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 24px;
}

.publish-container {
  max-width: 1000px;
  margin: 0 auto;
  background: #fff;
  border-radius: 16px;
  padding: 32px;
}

.publish-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.publish-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.form-item {
  margin-bottom: 24px;
}

.form-label {
  display: inline-block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
  min-width: 60px;
}

.title-input :deep(.el-input__inner) {
  font-size: 18px;
}

.image-uploader {
  margin-top: 8px;
}

.upload-tip {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.editor-wrapper {
  margin-top: 8px;
}

.visual-editor {
  position: relative;
}

.editor-toolbar {
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
  gap: 8px;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 4px;
}

.editor-toolbar button {
  width: 32px;
  height: 32px;
  border: none;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.editor-toolbar button:hover {
  background: #eee;
}

.preview-content {
  padding: 16px;
  background: #f9f9f9;
  border-radius: 8px;
  min-height: 300px;
}

.preview-content :deep(h1),
.preview-content :deep(h2) {
  margin: 16px 0 8px;
}

.preview-content :deep(p) {
  margin-bottom: 12px;
  line-height: 1.6;
}

.tags-wrapper {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.tag-item {
  margin-right: 0;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.cover-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
}

.cover-option {
  width: 120px;
  height: 90px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: border-color 0.3s;
}

.cover-option.selected {
  border-color: #ff2442;
}

.cover-option img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

@media (max-width: 768px) {
  .publish-view {
    padding: 12px;
  }

  .publish-container {
    padding: 16px;
  }

  .publish-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
}
</style>
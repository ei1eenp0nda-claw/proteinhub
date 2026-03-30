<template>
  <div class="settings-view">
    <div class="settings-container">
      <div class="page-header">
        <h2>账号设置</h2>
      </div>

      <el-tabs tab-position="left" class="settings-tabs">
        <!-- 个人资料 -->
        <el-tab-pane label="个人资料">
          <div class="settings-section">
            <h3>个人资料</h3>
            
            <div class="form-item">
              <label>头像</label>
              <div class="avatar-upload">
                <el-avatar :size="100" :src="form.avatar">
                  {{ form.nickname?.charAt(0) }}
                </el-avatar>
                <el-upload
                  action="/api/v1/upload/avatar"
                  :show-file-list="false"
                  :on-success="handleAvatarSuccess"
                  :before-upload="beforeAvatarUpload"
                  :headers="uploadHeaders"
                >
                  <el-button type="primary" plain>更换头像</el-button>
                </el-upload>
              </div>
            </div>

            <div class="form-item">
              <label>昵称</label>
              <el-input v-model="form.nickname" maxlength="20" show-word-limit />
            </div>

            <div class="form-item">
              <label>简介</label>
              <el-input
                v-model="form.bio"
                type="textarea"
                :rows="3"
                maxlength="200"
                show-word-limit
                placeholder="介绍一下你自己..."
              />
            </div>

            <div class="form-item">
              <label>所在地区</label>
              <el-input v-model="form.location" placeholder="如：北京" />
            </div>

            <div class="form-item">
              <label>个人网站</label>
              <el-input v-model="form.website" placeholder="https://" />
            </div>

            <el-button type="primary" @click="saveProfile">保存修改</el-button>
          </div>
        </el-tab-pane>

        <!-- 账号安全 -->
        <el-tab-pane label="账号安全">
          <div class="settings-section">
            <h3>修改密码</h3>
            
            <div class="form-item">
              <label>当前密码</label>
              <el-input v-model="passwordForm.oldPassword" type="password" show-password />
            </div>

            <div class="form-item">
              <label>新密码</label>
              <el-input v-model="passwordForm.newPassword" type="password" show-password />
            </div>

            <div class="form-item">
              <label>确认新密码</label>
              <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
            </div>

            <el-button type="primary" @click="changePassword">修改密码</el-button>
          </div>
        </el-tab-pane>

        <!-- 通知设置 -->
        <el-tab-pane label="通知设置">
          <div class="settings-section">
            <h3>消息通知</h3>
            
            <div class="setting-item">
              <span>收到点赞</span>
              <el-switch v-model="notificationSettings.like" />
            </div>
            
            <div class="setting-item">
              <span>收到评论</span>
              <el-switch v-model="notificationSettings.comment" />
            </div>
            
            <div class="setting-item">
              <span>新增关注</span>
              <el-switch v-model="notificationSettings.follow" />
            </div>
            
            <div class="setting-item">
              <span>系统通知</span>
              <el-switch v-model="notificationSettings.system" />
            </div>

            <el-button type="primary" @click="saveNotificationSettings">保存设置</el-button>
          </div>
        </el-tab-pane>

        <!-- 隐私设置 -->
        <el-tab-pane label="隐私设置">
          <div class="settings-section">
            <h3>隐私设置</h3>
            
            <div class="setting-item">
              <span>公开我的收藏列表</span>
              <el-switch v-model="privacySettings.showFavorites" />
            </div>
            
            <div class="setting-item">
              <span>公开我的关注列表</span>
              <el-switch v-model="privacySettings.showFollowing" />
            </div>

            <el-button type="primary" @click="savePrivacySettings">保存设置</el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { userApi, authApi } from '@/api'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()

const form = ref({
  nickname: userStore.currentUser?.nickname || '',
  avatar: userStore.currentUser?.avatar || '',
  bio: userStore.currentUser?.bio || '',
  location: userStore.currentUser?.location || '',
  website: userStore.currentUser?.website || '',
})

const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const notificationSettings = ref({
  like: true,
  comment: true,
  follow: true,
  system: true,
})

const privacySettings = ref({
  showFavorites: true,
  showFollowing: true,
})

const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${userStore.token}`,
}))

const handleAvatarSuccess = (res) => {
  form.value.avatar = res.url
  ElMessage.success('头像上传成功')
}

const beforeAvatarUpload = (file) => {
  const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isJpgOrPng) {
    ElMessage.error('只支持 JPG/PNG 格式!')
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
  }
  return isJpgOrPng && isLt2M
}

const saveProfile = async () => {
  try {
    await authApi.updateProfile(form.value)
    userStore.setUserInfo({ ...userStore.currentUser, ...form.value })
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const changePassword = async () => {
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  try {
    await authApi.updateProfile({
      oldPassword: passwordForm.value.oldPassword,
      newPassword: passwordForm.value.newPassword,
    })
    ElMessage.success('密码修改成功')
    passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
  } catch (error) {
    ElMessage.error('密码修改失败')
  }
}

const saveNotificationSettings = () => {
  ElMessage.success('通知设置已保存')
}

const savePrivacySettings = () => {
  ElMessage.success('隐私设置已保存')
}
</script>

<style scoped>
.settings-view {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 24px;
}

.settings-container {
  max-width: 1000px;
  margin: 0 auto;
  background: #fff;
  border-radius: 16px;
  padding: 32px;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
}

.settings-tabs :deep(.el-tabs__content) {
  padding-left: 32px;
}

.settings-section {
  max-width: 500px;
}

.settings-section h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.form-item {
  margin-bottom: 20px;
}

.form-item label {
  display: block;
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
}

.avatar-upload {
  display: flex;
  align-items: center;
  gap: 20px;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f5f5f5;
}

.setting-item span {
  font-size: 14px;
  color: #333;
}

@media (max-width: 768px) {
  .settings-container {
    padding: 16px;
  }

  .settings-tabs :deep(.el-tabs__header) {
    display: none;
  }

  .settings-tabs :deep(.el-tabs__content) {
    padding-left: 0;
  }
}
</style>
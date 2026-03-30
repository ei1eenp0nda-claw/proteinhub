<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-left">
        <div class="brand">
          <img src="/vite.svg" alt="ProteinHub" class="logo" />
          <h1>ProteinHub</h1>
          <p>生物医学笔记分享平台</p>
        </div>
        <div class="features">
          <div class="feature-item">
            <Document />
            <span>记录研究心得</span>
          </div>
          <div class="feature-item">
            <Share />
            <span>分享实验技巧</span>
          </div>
          <div class="feature-item">
            <Connection />
            <span>连接科研社区</span>
          </div>
        </div>
      </div>

      <div class="auth-right">
        <div class="auth-box">
          <h2>欢迎回来</h2>
          <p class="subtitle">登录以继续分享你的科研之旅</p>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            class="auth-form"
            @keyup.enter="handleLogin"
          >
            <el-form-item prop="email">
              <el-input
                v-model="form.email"
                placeholder="邮箱"
                size="large"
                :prefix-icon="Message"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="密码"
                size="large"
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>

            <div class="form-options">
              <el-checkbox v-model="form.remember">记住我</el-checkbox>
              <a href="#" @click.prevent="forgotPassword">忘记密码？</a>
            </div>

            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loading"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form>

          <div class="divider">
            <span>或</span>
          </div>

          <div class="social-login">
            <el-button class="social-btn">
              <img src="/google.svg" alt="Google" />
              使用 Google 登录
            </el-button>
          </div>

          <p class="auth-link">
            还没有账号？
            <router-link to="/register">立即注册</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Message, Lock, Document, Share, Connection } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)

const form = reactive({
  email: '',
  password: '',
  remember: false,
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' },
  ],
}

const handleLogin = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await authApi.login({
      email: form.email,
      password: form.password,
    })
    
    userStore.setToken(res.token)
    userStore.setUserInfo(res.user)
    
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    ElMessage.error('登录失败，请检查邮箱和密码')
  } finally {
    loading.value = false
  }
}

const forgotPassword = () => {
  ElMessage.info('请联系管理员重置密码')
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.auth-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  max-width: 1000px;
  width: 100%;
  background: #fff;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.auth-left {
  background: linear-gradient(135deg, #ff2442 0%, #ff6b7a 100%);
  padding: 60px;
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.brand {
  margin-bottom: 60px;
}

.logo {
  width: 60px;
  height: 60px;
  margin-bottom: 20px;
}

.brand h1 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
}

.brand p {
  font-size: 16px;
  opacity: 0.9;
}

.features {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
}

.feature-item svg {
  font-size: 20px;
}

.auth-right {
  padding: 60px;
  display: flex;
  align-items: center;
}

.auth-box {
  width: 100%;
}

.auth-box h2 {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.subtitle {
  font-size: 14px;
  color: #999;
  margin-bottom: 32px;
}

.auth-form {
  margin-bottom: 24px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.form-options a {
  font-size: 14px;
  color: #ff2442;
  text-decoration: none;
}

.submit-btn {
  width: 100%;
  border-radius: 8px;
}

.divider {
  display: flex;
  align-items: center;
  margin: 24px 0;
  color: #999;
  font-size: 14px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #eee;
}

.divider span {
  padding: 0 16px;
}

.social-login {
  margin-bottom: 24px;
}

.social-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.social-btn img {
  width: 20px;
  height: 20px;
}

.auth-link {
  text-align: center;
  font-size: 14px;
  color: #666;
}

.auth-link a {
  color: #ff2442;
  text-decoration: none;
  font-weight: 500;
}

@media (max-width: 768px) {
  .auth-container {
    grid-template-columns: 1fr;
  }

  .auth-left {
    display: none;
  }

  .auth-right {
    padding: 40px 24px;
  }
}
</style>
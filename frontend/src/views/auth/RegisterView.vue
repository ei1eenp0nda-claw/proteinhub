<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-left">
        <div class="brand">
          <img src="/vite.svg" alt="ProteinHub" class="logo" />
          <h1>ProteinHub</h1>
          <p>加入我们的科研社区</p>
        </div>
      </div>

      <div class="auth-right">
        <div class="auth-box">
          <h2>创建账号</h2>
          <p class="subtitle">开启你的科研分享之旅</p>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            class="auth-form"
            @keyup.enter="handleRegister"
          >
            <el-form-item prop="nickname">
              <el-input
                v-model="form.nickname"
                placeholder="昵称"
                size="large"
                :prefix-icon="User"
                maxlength="20"
                show-word-limit
              />
            </el-form-item>

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

            <el-form-item prop="confirmPassword">
              <el-input
                v-model="form.confirmPassword"
                type="password"
                placeholder="确认密码"
                size="large"
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>

            <el-form-item prop="agreement">
              <el-checkbox v-model="form.agreement">
                我已阅读并同意
                <a href="#" @click.prevent="showTerms">用户协议</a>
                和
                <a href="#" @click.prevent="showPrivacy">隐私政策</a>
              </el-checkbox>
            </el-form-item>

            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loading"
              @click="handleRegister"
            >
              注册
            </el-button>
          </el-form>

          <p class="auth-link">
            已有账号？
            <router-link to="/login">立即登录</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Message, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)

const form = reactive({
  nickname: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreement: false,
})

const validatePass2 = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const validateAgreement = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请同意用户协议和隐私政策'))
  } else {
    callback()
  }
}

const rules = {
  nickname: [
    { required: true, message: '请输入昵称', trigger: 'blur' },
    { min: 2, max: 20, message: '昵称长度2-20个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validatePass2, trigger: 'blur' },
  ],
  agreement: [
    { validator: validateAgreement, trigger: 'change' },
  ],
}

const handleRegister = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await authApi.register({
      nickname: form.nickname,
      email: form.email,
      password: form.password,
    })
    
    userStore.setToken(res.token)
    userStore.setUserInfo(res.user)
    
    ElMessage.success('注册成功')
    router.push('/')
  } catch (error) {
    ElMessage.error('注册失败，请重试')
  } finally {
    loading.value = false
  }
}

const showTerms = () => {
  ElMessage.info('用户协议详情')
}

const showPrivacy = () => {
  ElMessage.info('隐私政策详情')
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
  text-align: center;
}

.logo {
  width: 80px;
  height: 80px;
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

.submit-btn {
  width: 100%;
  border-radius: 8px;
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
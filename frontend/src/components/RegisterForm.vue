<template>
  <div class="register-container">
    <div class="register-box">
      <h2>注册 ProteinHub</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label>用户名</label>
          <input 
            v-model="form.username" 
            type="text" 
            required
            placeholder="设置用户名"
          />
        </div>
        <div class="form-group">
          <label>邮箱</label>
          <input 
            v-model="form.email" 
            type="email" 
            required
            placeholder="your@email.com"
          />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input 
            v-model="form.password" 
            type="password" 
            required
            placeholder="至少8位，包含字母和数字"
          />
          <span class="hint">密码需至少8位，包含字母和数字</span>
        </div>
        <button type="submit" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="success">{{ success }}</p>
      </form>
      <p class="switch">
        已有账号？<a @click="$emit('switch')">立即登录</a>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const emit = defineEmits(['switch', 'register-success'])

const form = reactive({
  username: '',
  email: '',
  password: ''
})

const loading = ref(false)
const error = ref('')
const success = ref('')

const handleRegister = async () => {
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    })
    
    const data = await response.json()
    
    if (response.ok) {
      success.value = '注册成功！请登录'
      setTimeout(() => {
        emit('register-success')
        emit('switch')
      }, 1500)
    } else {
      error.value = data.error || '注册失败'
    }
  } catch (err) {
    error.value = '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f5f5f5;
}

.register-box {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 400px;
}

h2 {
  text-align: center;
  margin-bottom: 24px;
  color: #333;
}

.form-group {
  margin-bottom: 16px;
}

label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  color: #666;
}

input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
}

input:focus {
  outline: none;
  border-color: #409eff;
}

.hint {
  display: block;
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

button {
  width: 100%;
  padding: 12px;
  background: #67c23a;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  margin-top: 8px;
}

button:disabled {
  background: #b3e19d;
  cursor: not-allowed;
}

.error {
  color: #f56c6c;
  font-size: 14px;
  margin-top: 12px;
  text-align: center;
}

.success {
  color: #67c23a;
  font-size: 14px;
  margin-top: 12px;
  text-align: center;
}

.switch {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
}

.switch a {
  color: #409eff;
  cursor: pointer;
}
</style>

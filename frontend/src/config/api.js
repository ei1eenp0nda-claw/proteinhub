// API 配置 - 自动适配开发/生产环境
const isDevelopment = import.meta.env.DEV;

// 开发环境用本地后端，生产环境用 Render 后端
const API_BASE_URL = isDevelopment 
  ? 'http://localhost:5000'  // 开发环境
  : import.meta.env.VITE_API_BASE_URL || 'https://your-render-app.onrender.com';  // 生产环境

export default {
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
};
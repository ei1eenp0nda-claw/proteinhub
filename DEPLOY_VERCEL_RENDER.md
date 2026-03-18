# ProteinHub 部署指南 - Vercel + Render

## 概述
- **前端**: Vercel (Vue 3 SPA)
- **后端**: Render (Flask + SQLite)
- **成本**: $0 (免费额度)

---

## 步骤一：部署后端到 Render

### 1. 创建 Render 账号
1. 访问 https://render.com
2. 用 GitHub 账号登录

### 2. 创建 Web Service
1. 点击 **New → Web Service**
2. 选择你的 GitHub 仓库: `proteinhub`
3. 配置如下:

```
Name: proteinhub-api
Runtime: Python 3
Build Command: pip install -r backend/requirements.txt
Start Command: cd backend && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
Instance Type: Free
```

### 3. 添加环境变量
在 Render Dashboard → Environment 中添加:

```
SECRET_KEY=your-random-secret-key-here
RENDER=true
```

### 4. 部署
点击 **Create Web Service**，等待部署完成。

**注意**: 部署完成后 Render 会给你一个 URL，类似 `https://proteinhub-api.onrender.com`，记下来后面用。

---

## 步骤二：部署前端到 Vercel

### 1. 创建 Vercel 账号
1. 访问 https://vercel.com
2. 用 GitHub 账号登录

### 2. 创建项目
1. 点击 **Add New → Project**
2. 选择你的 GitHub 仓库: `proteinhub`
3. 配置如下:

```
Framework Preset: Vite
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
```

### 3. 添加环境变量
在 Vercel Dashboard → Settings → Environment Variables 中添加:

```
VITE_API_BASE_URL=https://your-render-app.onrender.com/api
```

**把上面的 URL 替换成你 Render 应用的实际地址**

### 4. 部署
点击 **Deploy**，等待部署完成。

---

## 步骤三：初始化数据

部署完成后，需要初始化蛋白数据：

```bash
# 调用初始化接口（用 curl 或浏览器访问）
curl -X POST https://your-render-app.onrender.com/api/init

# 检查健康状态
curl https://your-render-app.onrender.com/api/health
```

---

## ⚠️ 重要提示

### Render 免费版限制
1. **SQLite 数据不会持久化** - 每次部署或 15 分钟无访问后，数据会重置
2. **冷启动慢** - 首次访问可能需要 30-60 秒唤醒
3. **每月 750 小时运行时间** - 足够一个服务 7×24 运行

### 数据持久化方案
如果需要数据持久化，迁移到 Render PostgreSQL:
1. 在 Render Dashboard 创建 PostgreSQL 数据库 (免费)
2. 修改环境变量: `DATABASE_URL=postgresql://...`
3. 重新部署

---

## 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
python app.py

# 前端 (新终端)
cd frontend
npm install
npm run dev
```

---

## 文件变更说明

本次为部署做了以下修改:

1. **backend/models.py**: 添加 Render 环境检测，使用 `/tmp` 目录存放 SQLite
2. **backend/app.py**: SECRET_KEY 改为从环境变量读取
3. **backend/requirements.txt**: 添加 gunicorn
4. **backend/render.yaml**: Render Blueprint 配置
5. **frontend/vercel.json**: Vercel 部署配置
6. **frontend/src/config/api.js**: API 地址配置

---

## 故障排查

### 后端无法启动
- 检查 Render 日志: Dashboard → Logs
- 确认 `gunicorn` 在 requirements.txt 中
- 确认 `app:app` 导入正确

### 前端 API 请求失败
- 检查 Vercel 环境变量 `VITE_API_BASE_URL` 是否正确
- 确认 Render 后端 URL 可访问
- 浏览器 DevTools → Network 查看具体错误

### CORS 错误
- 后端已配置 `flask-cors`，应该没问题
- 如果仍报错，检查 Render 环境变量是否正确加载

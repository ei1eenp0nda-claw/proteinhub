# ProteinHub - 蛋白互作学术推荐平台

[![CI/CD](https://github.com/yourname/proteinhub/workflows/ProteinHub%20CI/CD/badge.svg)](https://github.com/yourname/proteinhub/actions)
[![codecov](https://codecov.io/gh/yourname/proteinhub/branch/main/graph/badge.svg)](https://codecov.io/gh/yourname/proteinhub)

## 🎯 项目简介

ProteinHub (PPI小红书) 是一个面向生物学研究者的学术推荐平台，帮助研究人员发现感兴趣的蛋白质和相关文献。基于 15 万对蛋白互作预测数据，结合现代推荐算法，提供个性化的学术内容推荐。

## ✨ 核心功能

### 1. 智能推荐系统
- **双塔召回模型**: 用户塔 + 物品塔，个性化蛋白推荐
- **冷启动策略**: 基于蛋白家族兴趣引导
- **实时 Feed**: 关注蛋白的最新研究动态

### 2. 蛋白数据中心
- **蛋白档案**: 每个蛋白独立主页，包含传记、文献、互作网络
- **15万互作数据**: 基于 Rosetta PPI 方法预测
- **PubMed 集成**: 自动抓取最新研究文献

### 3. 用户系统
- **JWT 认证**: 安全的注册/登录/令牌刷新
- **关注功能**: 关注感兴趣的蛋白，获取更新通知
- **个性化 Feed**: 基于关注历史的内容推荐

### 4. 高级搜索
- **全文搜索**: 蛋白名称、描述、家族多字段搜索
- **模糊匹配**: 支持拼写错误的智能搜索
- **自动补全**: 实时搜索建议

## 🚀 快速开始

### 使用 Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/yourname/proteinhub.git
cd proteinhub

# 启动服务
docker-compose up -d

# 访问
前端: http://localhost:5173
后端 API: http://localhost:5000
API 文档: http://localhost:5000/swagger
```

### 本地开发

**后端:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 设置环境变量
export DATABASE_URL=postgresql://user:pass@localhost/proteinhub
export JWT_SECRET_KEY=your-secret-key

# 运行
python app.py
```

**前端:**
```bash
cd frontend
npm install
npm run dev
```

## 🏗️ 系统架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Vue Frontend  │────▶│  Flask Backend  │────▶│   PostgreSQL    │
│   (Port 5173)   │     │   (Port 5000)   │     │   (Port 5432)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Redis Cache    │
                        │  (Optional)     │
                        └─────────────────┘
```

## 📊 技术栈

**后端:**
- Flask + SQLAlchemy
- PostgreSQL + 连接池
- JWT + bcrypt
- Pytest 测试
- SocketIO 实时通知

**前端:**
- Vue 3 + Vue Router
- 响应式设计
- 组件化架构

**部署:**
- Docker + Docker Compose
- GitHub Actions CI/CD
- Nginx 反向代理

**推荐算法:**
- 双塔召回模型
- 向量相似度检索
- 冷启动策略

## 📁 项目结构

```
proteinhub/
├── backend/
│   ├── app.py                 # Flask 主应用
│   ├── auth.py                # JWT 认证
│   ├── config.py              # 配置管理
│   ├── database.py            # 数据库连接
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── api_docs.py            # API 文档
│   ├── models/
│   │   └── user.py            # 用户模型
│   ├── routes/
│   │   ├── auth.py            # 认证路由
│   │   ├── follow.py          # 关注路由
│   │   ├── recommendation.py  # 推荐路由
│   │   ├── search.py          # 搜索路由
│   │   └── admin.py           # 管理后台
│   ├── services/
│   │   ├── protein_service.py # 蛋白服务
│   │   ├── feed_service.py    # Feed 服务
│   │   └── search_service.py  # 搜索服务
│   ├── crawler/
│   │   └── pubmed_crawler.py  # PubMed 爬虫
│   ├── recommendation/
│   │   └── dual_tower.py      # 双塔推荐
│   ├── utils/
│   │   ├── data_importer.py   # 数据导入
│   │   ├── cache.py           # 缓存层
│   │   └── performance.py     # 性能监控
│   ├── websocket/
│   │   └── notifications.py   # 实时通知
│   └── tests/
│       └── test_api.py        # 测试套件
├── frontend/
│   ├── src/
│   │   ├── components/        # 可复用组件
│   │   ├── views/             # 页面组件
│   │   └── router/            # 路由配置
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── .github/workflows/
│   └── ci.yml                 # CI/CD 配置
├── docker-compose.yml
└── README.md
```

## 🔌 API 文档

### 认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户

### 蛋白
- `GET /api/proteins` - 蛋白列表
- `GET /api/proteins/:id` - 蛋白详情
- `GET /api/proteins/:id/profile` - 蛋白主页

### Feed
- `GET /api/feed` - 推荐 Feed
- `POST /api/posts` - 创建帖子

### 推荐
- `GET /api/recommend/personalized` - 个性化推荐
- `GET /api/recommend/explore` - 探索推荐
- `POST /api/recommend/cold-start` - 冷启动推荐

### 关注
- `POST /api/proteins/:id/follow` - 关注蛋白
- `DELETE /api/proteins/:id/unfollow` - 取消关注
- `GET /api/user/followed-proteins` - 关注列表
- `GET /api/user/follow-feed` - 关注 Feed

### 搜索
- `GET /api/search?q=xxx` - 全局搜索
- `GET /api/search/suggestions?q=xxx` - 搜索建议
- `GET /api/search/proteins?q=xxx` - 蛋白搜索
- `GET /api/search/posts?q=xxx` - 帖子搜索

### 管理
- `GET /api/admin/stats` - 系统统计
- `POST /api/admin/import` - 数据导入
- `POST /api/admin/cache/clear` - 清除缓存

完整 API 文档见: http://localhost:5000/swagger

## 🧪 测试

```bash
# 运行测试
cd backend
pytest --cov=.

# 代码检查
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

## 📈 性能指标

- 响应时间: < 200ms (P95)
- 数据库查询: < 100ms
- 推荐计算: < 50ms
- 并发连接: 30+

## 🛣️ 路线图

- [x] 用户认证系统
- [x] 双塔推荐算法
- [x] PubMed 爬虫
- [x] Docker 部署
- [x] 高级搜索
- [x] 管理后台
- [ ] 实时通知 (WebSocket)
- [ ] 移动端适配
- [ ] 机器学习模型升级
- [ ] 分布式部署

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

MIT License

## 👨‍💻 作者

- **Kimi-Claw** - 项目架构 & 开发
- **苏航** - 产品负责人

---

⭐ 如果这个项目对你有帮助，请给一个 Star！

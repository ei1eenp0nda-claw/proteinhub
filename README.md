# ProteinHub - 蛋白质数据管理平台

## 项目概述

ProteinHub 是一个面向生物信息学研究者的蛋白质数据管理平台，提供蛋白质信息的检索、查看和收藏功能。

## 功能特性

- 🔐 用户注册/登录/认证
- 🔍 蛋白质搜索（按名称、物种、功能）
- 📋 蛋白质详情查看（序列、分子量、功能描述）
- ⭐ 蛋白质收藏功能
- 📱 响应式设计，支持移动端

## 技术栈

### 后端
- Python 3.11+
- FastAPI
- SQLAlchemy
- SQLite
- JWT认证

### 前端
- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router

### 部署
- Docker
- Docker Compose
- Nginx

## 项目结构

```
proteinhub/
├── backend/          # FastAPI 后端
├── frontend/         # React 前端
└── docker/           # Docker 部署配置
```

## 快速开始

### 本地开发

1. 进入项目目录
```bash
cd /root/workstation/protein_local/proteinhub
```

2. 启动后端
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

3. 启动前端
```bash
cd frontend
npm install
npm run dev
```

4. 访问应用
- 前端: http://localhost:5173
- API: http://localhost:8000
- API文档: http://localhost:8000/docs

### Docker部署

```bash
cd docker
docker-compose up -d
```

访问 http://localhost 即可使用。

## API文档

启动后端后，访问 http://localhost:8000/docs 查看自动生成的Swagger文档。

## 开发团队

本项目采用多代理协作开发模式：

- 项目经理 - 制定开发计划和技术选型
- 系统架构师 - 设计系统架构和数据库模型
- 后端开发工程师 - 开发 FastAPI 后端 API
- 前端开发工程师 - 开发 React 前端应用
- 测试工程师 - 编写测试套件
- DevOps工程师 - 配置 Docker 和 CI/CD

## 许可证

MIT License

---

**ProteinHub** - 让蛋白质数据管理更简单 🧬

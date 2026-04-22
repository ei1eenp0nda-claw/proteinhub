# ProteinHub Frontend

ProteinHub 前端应用 - 一个现代化的蛋白质信息管理平台。

## 技术栈

- **React 18** - 前端框架
- **TypeScript** - 类型安全的JavaScript
- **Vite** - 构建工具
- **Tailwind CSS** - 样式框架
- **React Router** - 路由管理
- **Axios** - HTTP客户端
- **Lucide React** - 图标库

## 功能特性

- 🔐 用户认证（登录/注册）
- 🔍 蛋白质搜索和筛选
- 📋 蛋白质列表展示
- 📄 蛋白质详情页
- ❤️ 收藏功能
- 👤 个人中心
- 📱 响应式设计

## 快速开始

### 安装依赖

```bash
cd proteinhub
npm install
```

### 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 启动开发服务器

```bash
npm run dev
```

应用将在 `http://localhost:3000` 运行。

### 构建生产版本

```bash
npm run build
```

构建后的文件将在 `dist` 目录中。

## 项目结构

```
src/
├── components/          # 组件
│   └── layout/         # 布局组件
│       ├── Layout.tsx
│       ├── Navbar.tsx
│       └── Footer.tsx
├── contexts/           # React Context
│   └── AuthContext.tsx
├── hooks/              # 自定义 Hooks
├── pages/              # 页面组件
│   ├── HomePage.tsx
│   ├── ProteinListPage.tsx
│   ├── ProteinDetailPage.tsx
│   ├── SearchPage.tsx
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   └── UserProfilePage.tsx
├── services/           # API 服务
│   ├── api.ts
│   ├── authService.ts
│   └── proteinService.ts
├── types/              # TypeScript 类型
│   └── index.ts
├── utils/              # 工具函数
├── App.tsx
├── main.tsx
└── index.css
```

## API 配置

后端 API 基础 URL: `http://localhost:8000/api/v1`

主要端点：

- `POST /auth/login` - 用户登录
- `POST /auth/register` - 用户注册
- `GET /users/me` - 获取当前用户信息
- `GET /proteins` - 获取蛋白质列表
- `GET /proteins/{id}` - 获取蛋白质详情
- `GET /proteins/search` - 搜索蛋白质
- `GET /favorites` - 获取用户收藏
- `POST /favorites` - 添加收藏
- `DELETE /favorites/{id}` - 删除收藏

## 开发指南

### 代码规范

- 使用 TypeScript 严格模式
- 组件使用函数式组件 + Hooks
- 使用 React.FC 类型定义组件
- 使用 Tailwind CSS 进行样式设计
- 遵循 ESLint 和 Prettier 配置

### 提交规范

- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或联系开发团队。

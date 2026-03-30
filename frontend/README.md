# ProteinHub Frontend

ProteinHub 生物医学笔记分享平台的前端项目，采用 Vue 3 + Vite + Element Plus 构建。

## 项目特点

- 🎨 **小红书风格卡片式浏览** - 瀑布流布局，沉浸式内容体验
- 📱 **响应式设计** - 完美适配 PC 和移动端
- 🚀 **Vue 3 + Composition API** - 现代化开发方式
- 🛠 **Element Plus UI** - 美观的组件库
- 📦 **Pinia 状态管理** - 简洁高效的状态管理
- 🔗 **Axios API 封装** - 统一的请求处理

## 功能模块

### 1. 首页/发现页
- 瀑布流卡片布局
- 分类筛选（研究进展、实验方法、文献解读、经验分享）
- 搜索栏
- 热门推荐

### 2. 笔记详情页
- 笔记内容展示（支持 Markdown）
- 图片轮播/画廊
- 点赞、收藏、评论功能
- 作者信息
- 相关推荐

### 3. 发布页
- 富文本编辑器（Markdown 支持）
- 图片上传（最多9张）
- 标签选择
- 封面设置
- 草稿保存

### 4. 用户中心
- 个人资料展示
- 我的笔记
- 我的收藏
- 账号设置

### 5. 管理后台
- 数据概览面板
- 内容审核
- 用户管理

## 技术栈

- **框架**: Vue 3.4+
- **构建工具**: Vite 5.0+
- **UI 组件库**: Element Plus 2.6+
- **状态管理**: Pinia 2.1+
- **路由**: Vue Router 4.3+
- **HTTP 客户端**: Axios 1.6+
- **Markdown 渲染**: Marked 12.0+

## 项目结构

```
src/
├── api/              # API 接口封装
│   ├── client.js     # Axios 实例配置
│   └── index.js      # API 接口定义
├── components/       # 公共组件
│   ├── layout/       # 布局组件
│   ├── note/         # 笔记相关组件
│   └── common/       # 通用组件
├── router/           # 路由配置
│   └── index.js
├── stores/           # Pinia 状态管理
│   ├── user.js       # 用户状态
│   └── app.js        # 应用状态
├── utils/            # 工具函数
├── views/            # 页面视图
│   ├── admin/        # 管理后台
│   ├── auth/         # 登录注册
│   ├── home/         # 首页/发现
│   ├── note/         # 笔记详情
│   ├── publish/      # 发布页
│   ├── search/       # 搜索页
│   └── user/         # 用户中心
├── App.vue
└── main.js
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发环境启动

```bash
npm run dev
```

默认启动在 http://localhost:3000

### 生产环境构建

```bash
npm run build
```

构建产物将输出到 `dist` 目录

### 预览生产构建

```bash
npm run preview
```

## 环境变量配置

在项目根目录创建 `.env` 文件：

```env
# API 基础地址
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 后端 API 对接

项目预设了以下 API 接口，需要与后端配合：

### 认证相关
- `POST /auth/login` - 登录
- `POST /auth/register` - 注册
- `GET /auth/me` - 获取当前用户信息
- `PUT /auth/profile` - 更新个人资料

### 笔记相关
- `GET /notes` - 获取笔记列表
- `GET /notes/:id` - 获取笔记详情
- `POST /notes` - 创建笔记
- `PUT /notes/:id` - 更新笔记
- `DELETE /notes/:id` - 删除笔记
- `POST /notes/:id/like` - 点赞
- `POST /notes/:id/favorite` - 收藏

### 用户相关
- `GET /users/:id` - 获取用户信息
- `GET /users/:id/notes` - 获取用户笔记
- `GET /users/me/favorites` - 获取我的收藏

### 搜索
- `GET /search` - 搜索

### 管理后台
- `GET /admin/stats` - 统计数据
- `GET /admin/notes/pending` - 待审核笔记
- `POST /admin/notes/:id/approve` - 通过笔记
- `POST /admin/notes/:id/reject` - 拒绝笔记
- `GET /admin/users` - 用户列表
- `PUT /admin/users/:id/status` - 更新用户状态

## 开发规范

1. **组件命名**: 使用 PascalCase，如 `NoteCard.vue`
2. **文件引用**: 使用 `@/` 别名指向 `src` 目录
3. **API 调用**: 统一使用 `src/api/index.js` 中封装的接口
4. **状态管理**: 用户状态使用 `useUserStore`，应用状态使用 `useAppStore`

## 响应式断点

- **移动端**: < 768px
- **平板**: 768px - 1024px
- **桌面**: > 1024px

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

MIT License
# ProteinHub 商业化改造 - Goal-Driven 项目规划

## 项目目标 (Goal)

将 ProteinHub 从现有原型升级为**可注册、可使用的商业级学术社交应用**，核心体验对标小红书：
- 流畅的 Feed 瀑布流浏览
- 完整的用户注册/登录/个人资料
- 社交互动（点赞、评论、收藏、关注）
- 内容发布与管理
- 移动端优先的响应式设计

## 成功标准 (Criteria for Success)

### 功能完整性 (必须全部达成)
- [ ] 用户系统：注册/登录/登出/密码重置/邮箱验证
- [ ] 个人资料：头像上传/简介编辑/关注列表
- [ ] Feed 流：瀑布流展示/无限滚动/推荐排序
- [ ] 社交功能：点赞/取消点赞/评论/收藏/关注用户
- [ ] 内容发布：创建笔记/上传图片/编辑/删除
- [ ] 搜索发现：全文搜索/标签筛选/热门推荐
- [ ] 通知系统：站内通知/红点提示
- [ ] 管理后台：内容审核/用户管理/数据统计

### 性能指标
- [ ] 首屏加载 < 2s
- [ ] Feed 滚动流畅，无卡顿
- [ ] API 响应 P95 < 200ms
- [ ] 支持 1000+ 并发用户

### 体验标准
- [ ] 移动端完美适配（iOS/Android）
- [ ] 微信内置浏览器可正常使用
- [ ] 支持 PWA 添加到主屏幕

## 技术架构现状

```
当前架构：
├── Backend: Flask + SQLAlchemy + JWT + SQLite
├── Frontend: Vue 3 + Element Plus + Vite
├── Data: 本地 JSON + Markdown 笔记
└── Deploy: Docker + Nginx

目标架构：
├── Backend: Flask + PostgreSQL + Redis + Celery
├── Frontend: Vue 3 + Tailwind + Vite + PWA
├── Storage: 阿里云OSS / AWS S3 (图片存储)
├── Search: Elasticsearch (全文搜索)
├── Queue: Redis + Celery (异步任务)
└── Deploy: Kubernetes / Render / Vercel
```

## 任务拆解与分工

### Phase 1: 核心用户系统 (Week 1)
**Subagent-1: 认证系统升级**
- 邮箱验证流程
- 密码重置功能
- JWT 刷新令牌机制
- 社交账号登录（微信/谷歌）

**Subagent-2: 用户资料系统**
- 头像上传（裁剪/压缩）
- 个人资料页设计
- 关注/粉丝列表
- 用户隐私设置

### Phase 2: Feed 流优化 (Week 1-2)
**Subagent-3: Feed 重构**
- 瀑布流性能优化（虚拟滚动）
- 推荐算法接入
- 下拉刷新/上拉加载
- 骨架屏加载状态

**Subagent-4: 内容发布**
- 富文本编辑器
- 图片上传（多图/拖拽）
- 标签系统
- 草稿箱功能

### Phase 3: 社交互动 (Week 2)
**Subagent-5: 互动系统**
- 点赞/取消点赞（防抖）
- 评论系统（嵌套回复）
- 收藏功能
- 分享功能

**Subagent-6: 通知系统**
- WebSocket 实时通知
- 通知中心 UI
- 红点提示
- 推送设置

### Phase 4: 搜索发现 (Week 2-3)
**Subagent-7: 搜索系统**
- 全文搜索（Elasticsearch）
- 搜索建议/历史
- 热门标签
- 发现页推荐

### Phase 5: 移动端适配 (Week 3)
**Subagent-8: 移动端优化**
- 响应式布局重构
- 触摸手势支持
- 底部导航栏
- PWA 配置

### Phase 6: 运维部署 (Week 3-4)
**Subagent-9: 后端优化**
- 数据库迁移 PostgreSQL
- Redis 缓存层
- API 限流/防刷
- 日志监控

**Subagent-10: 部署上线**
- CI/CD 完善
- 生产环境配置
- 域名/SSL
- 性能监控

## 依赖关系

```
Phase 1 (用户系统)
    ↓
Phase 2 (Feed + 发布)
    ↓
Phase 3 (社交互动)
    ↓
Phase 4 (搜索)
    ↓
Phase 5 (移动端)
    ↓
Phase 6 (部署)
```

## 风险与预案

| 风险 | 影响 | 预案 |
|-----|------|------|
| 图片存储成本高 | 中 | 先使用本地存储，后期迁移到OSS |
| 推荐算法效果差 | 中 | 先用简单排序（时间/热度），后期接入ML |
| 审核人力不足 | 高 | 接入阿里云内容安全API |
| 并发性能瓶颈 | 中 | 数据库读写分离 + CDN |

## 验收流程

每个 Phase 完成后：
1. Subagent 提交测试报告
2. Master 进行功能验收
3. 不符合 Criteria → 返回修改
4. 符合 Criteria → 进入下一阶段

## 当前状态

- [x] 基础架构搭建
- [x] 简单注册/登录
- [x] 基础 Feed 展示
- [x] 笔记数据准备

- [ ] 邮箱验证
- [ ] 图片上传
- [ ] 社交功能
- [ ] 移动端适配
- [ ] 生产部署

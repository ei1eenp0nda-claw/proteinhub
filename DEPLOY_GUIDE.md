# ProteinHub 生产部署指南

## 快速部署（推荐）

### 1. 购买云服务器
- **推荐**: Vultr / DigitalOcean / 阿里云
- **配置**: 1核 1GB 内存，Ubuntu 22.04
- **价格**: $5-10/月

### 2. 域名准备
- 购买域名（Namesilo / Cloudflare / 阿里云）
- 解析 A 记录到服务器 IP

### 3. 一键部署

```bash
# SSH 登录服务器
ssh root@your-server-ip

# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 克隆项目
git clone https://github.com/ei1eenp0nda-claw/proteinhub.git
cd proteinhub

# 配置域名
export DOMAIN=your-domain.com
sed -i "s/your-domain.com/$DOMAIN/g" nginx.prod.conf

# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 查看状态
docker-compose ps
```

### 4. 配置 HTTPS (SSL)

```bash
# 安装 certbot
docker run -it --rm \
  -v "$(pwd)/ssl:/etc/letsencrypt" \
  -v "$(pwd)/ssl-data:/data/letsencrypt" \
  certbot/certbot \
  certonly --standalone -d your-domain.com

# 重启 nginx
docker-compose restart nginx
```

### 5. 访问应用
- **前端**: https://your-domain.com
- **API**: https://your-domain.com/api/

---

## 详细部署选项

### 选项A: Docker Compose（推荐）
- ✅ 最简单
- ✅ 一键启动
- ✅ 自动重启
- ✅ 易于扩展

### 选项B: 手动部署
```bash
# 后端
pip install -r requirements.txt
python app.py

# 前端（单独窗口）
cd frontend
npm install
npm run build
npx serve dist
```

### 选项C: PM2 管理（生产级）
```bash
npm install -g pm2
pm2 start backend/app.py --name proteinhub-api
pm2 serve frontend/dist 80 --name proteinhub-web
```

---

## 成本对比

| 方案 | 月费用 | 适合场景 |
|------|--------|----------|
| Vultr 1核1G | $5 | 开发/测试 |
| 阿里云 1核1G | ¥30 | 国内用户 |
| AWS Free Tier | $0 | 第一年免费 |
| Railway/Render | $0-5 | 免运维 |

---

## 免费托管方案

### Render.com (推荐免费)
1. 注册 render.com
2. 连接 GitHub 仓库
3. 自动部署

### Railway.app
1. railway login
2. railway init
3. railway up

### Vercel (仅前端)
- 前端: Vercel
- 后端: Railway/Render

---

## 关键配置检查清单

- [ ] 服务器防火墙开放 80/443 端口
- [ ] 域名解析正确
- [ ] SSL 证书配置
- [ ] 后端 CORS 允许前端域名
- [ ] 数据库持久化
- [ ] 日志收集
- [ ] 监控告警

---

## 故障排查

```bash
# 查看日志
docker-compose logs -f backend
docker-compose logs -f nginx

# 重启服务
docker-compose restart

# 检查端口
netstat -tlnp | grep 5000
```

---

## 下一步

1. 选择云服务商
2. 购买域名
3. 运行部署脚本
4. 配置 HTTPS
5. 分享链接给他人

**最快路径**: Vultr $5/月 + Docker Compose = 10分钟上线

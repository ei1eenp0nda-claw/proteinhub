# ProteinHub 生产环境部署文档

## 📋 目录

1. [服务器环境要求](#服务器环境要求)
2. [部署步骤](#部署步骤)
3. [数据库初始化](#数据库初始化)
4. [SSL 证书配置](#ssl-证书配置)
5. [生产优化配置](#生产优化配置)
6. [监控与维护](#监控与维护)
7. [故障排查](#故障排查)

---

## 服务器环境要求

### 硬件配置建议

| 规模 | CPU | 内存 | 存储 | 带宽 |
|------|-----|------|------|------|
| 小型 (测试) | 2核 | 4GB | 50GB SSD | 5Mbps |
| 中型 (生产) | 4核 | 8GB | 100GB SSD | 10Mbps |
| 大型 (高并发) | 8核+ | 16GB+ | 200GB+ SSD | 50Mbps+ |

### 软件环境

- **操作系统**: Ubuntu 22.04 LTS / Debian 12 / CentOS 8
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Nginx**: 1.24+ (通过 Docker 部署)
- **PostgreSQL**: 15+ (通过 Docker 部署)
- **Redis**: 7+ (通过 Docker 部署)

### 域名准备

建议准备以下域名：

- **主站**: `proteinhub.example.com`
- **API 服务**: `api.proteinhub.example.com` (可选)
- **CDN/静态资源**: `cdn.proteinhub.example.com` (可选)

> 将 `example.com` 替换为您的实际域名

---

## 部署步骤

### 1. 服务器初始化

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要工具
sudo apt install -y curl wget git vim ufw fail2ban

# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 2. 配置防火墙

```bash
# 配置 UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# 检查状态
sudo ufw status verbose
```

### 3. 部署 ProteinHub

```bash
# 创建应用目录
mkdir -p /opt/proteinhub
cd /opt/proteinhub

# 克隆代码 (或上传代码)
git clone <your-repo-url> .

# 创建必要目录
mkdir -p {data,logs,nginx/ssl,scripts}

# 设置权限
chmod +x scripts/*.sh
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

**`.env` 示例：**

```env
# 数据库配置
POSTGRES_DB=proteinhub
POSTGRES_USER=proteinhub
POSTGRES_PASSWORD=your_secure_password_here

# 安全密钥 (使用 openssl rand -base64 32 生成)
SECRET_KEY=your-256-bit-secret-key-here
JWT_SECRET_KEY=your-different-jwt-secret-key-here

# CORS 配置
CORS_ORIGINS=https://proteinhub.example.com,https://www.proteinhub.example.com

# Gunicorn 配置
WORKERS=4
WORKER_TIMEOUT=120

# 日志级别
LOG_LEVEL=INFO

# 限流配置
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/minute
```

### 5. 启动服务

```bash
# 拉取镜像并构建
docker-compose pull
docker-compose build

# 启动服务 (后台运行)
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 6. 验证部署

```bash
# 健康检查
curl http://localhost/api/health

# 预期响应: {"status": "ok", "service": "proteinhub-api", ...}
```

---

## 数据库初始化

### 自动初始化

PostgreSQL 容器首次启动时会自动执行 `scripts/init-db.sql`：

```bash
# 创建初始化脚本
cat > scripts/init-db.sql << 'EOF'
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 用于全文搜索

-- 设置时区
SET TIMEZONE = 'Asia/Shanghai';

-- 创建初始数据 (可选)
-- INSERT INTO proteins (name, family, description) VALUES ...
EOF
```

### 手动初始化

```bash
# 进入数据库容器
docker-compose exec postgres psql -U proteinhub -d proteinhub

# 在容器内执行 SQL
\dt                    -- 查看表
\l                     -- 查看数据库
SELECT * FROM users;   -- 查看数据

# 退出
\q
```

### 数据备份

```bash
# 创建备份脚本
cat > scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/proteinhub/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
docker-compose exec -T postgres pg_dump -U proteinhub proteinhub | gzip > $BACKUP_DIR/proteinhub_$TIMESTAMP.sql.gz

# 备份上传的文件
tar czf $BACKUP_DIR/uploads_$TIMESTAMP.tar.gz ./data/uploads

# 保留最近 30 天的备份
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
EOF

chmod +x scripts/backup.sh

# 设置定时任务 (每天凌晨 2 点备份)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/proteinhub/scripts/backup.sh") | crontab -
```

---

## SSL 证书配置

### 方案一: Let's Encrypt (推荐)

```bash
# 安装 Certbot
sudo apt install -y certbot

# 获取证书 (使用 standalone 模式，需先停止 nginx)
sudo certbot certonly --standalone -d proteinhub.example.com -d www.proteinhub.example.com

# 复制证书到项目目录
sudo cp /etc/letsencrypt/live/proteinhub.example.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/proteinhub.example.com/privkey.pem nginx/ssl/
sudo chown -R $USER:$USER nginx/ssl/

# 设置自动续期
sudo certbot renew --dry-run

# 添加续期钩子 (自动重启 nginx)
echo '#!/bin/bash
cd /opt/proteinhub && docker-compose restart nginx' | sudo tee /etc/letsencrypt/renewal-hooks/deploy/proteinhub.sh
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/proteinhub.sh
```

### 方案二: 手动配置证书

```bash
# 将您的证书文件放入 nginx/ssl/ 目录
cp your_certificate.crt nginx/ssl/fullchain.pem
cp your_private.key nginx/ssl/privkey.pem

# 重启 nginx
docker-compose restart nginx
```

### 方案三: Cloudflare Origin Certificate

如果使用 Cloudflare，可以生成 15 年有效的 Origin Certificate：

1. 登录 Cloudflare Dashboard
2. SSL/TLS > Origin Server > Create Certificate
3. 下载证书和私钥，放入 `nginx/ssl/` 目录

---

## 生产优化配置

### 数据库连接池

已在 `config.py` 中配置：

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,           # 基础连接数
    'max_overflow': 20,        # 最大溢出连接
    'pool_timeout': 30,        # 获取连接超时时间
    'pool_recycle': 3600,      # 连接回收时间 (1小时)
    'pool_pre_ping': True,     # 连接前 ping 测试
}
```

### 日志配置

```bash
# 日志轮转配置
sudo tee /etc/logrotate.d/proteinhub << 'EOF'
/opt/proteinhub/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
    sharedscripts
    postrotate
        docker kill --signal="USR1" proteinhub-nginx
    endscript
}
EOF
```

### 健康检查端点

- **API 健康**: `GET /api/health`
- **Nginx 健康**: `GET /health`

### Redis 缓存优化

```conf
# redis.conf 附加配置
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

---

## 监控与维护

### 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f --tail=100

# 查看特定服务日志
docker-compose logs -f backend

# 重启服务
docker-compose restart backend

# 重新构建并启动
docker-compose up -d --build

# 停止所有服务
docker-compose down

# 停止并删除卷 (清空数据)
docker-compose down -v
```

### 性能监控

```bash
# 容器资源使用
docker stats

# 数据库连接数
docker-compose exec postgres psql -U proteinhub -c "SELECT count(*) FROM pg_stat_activity;"

# Redis 信息
docker-compose exec redis redis-cli info
```

### 更新部署

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建
docker-compose build backend

# 3. 滚动更新 (零停机)
docker-compose up -d backend

# 4. 验证新版本
curl http://localhost/api/health
```

---

## 故障排查

### 常见问题

#### 1. 服务无法启动

```bash
# 检查端口占用
sudo netstat -tlnp | grep 80
sudo netstat -tlnp | grep 443

# 检查配置文件语法
docker-compose config

# 查看详细错误日志
docker-compose logs --no-color 2>&1 | less
```

#### 2. 数据库连接失败

```bash
# 检查数据库容器状态
docker-compose ps postgres
docker-compose logs postgres

# 测试连接
docker-compose exec postgres pg_isready -U proteinhub
```

#### 3. 502 Bad Gateway

```bash
# 检查后端服务
docker-compose ps backend
docker-compose logs backend

# 检查 nginx 配置
nginx -t
```

#### 4. 内存不足

```bash
# 查看内存使用
free -h

# 添加 Swap (如果未配置)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 安全建议

1. **定期更新**: `sudo apt update && sudo apt upgrade`
2. **禁用 root 登录**: 编辑 `/etc/ssh/sshd_config`
3. **使用密钥认证**: 禁用密码登录
4. **配置 Fail2ban**: 防止暴力破解
5. **定期备份**: 数据库和上传文件

---

## 快速启动命令

```bash
# 完整部署流程
cd /opt/proteinhub
docker-compose pull
docker-compose up -d
sleep 5
curl http://localhost/api/health
```

## 联系支持

如有问题，请查看：
- GitHub Issues: [your-repo-url]/issues
- 系统日志: `docker-compose logs -f`
- 文档: [docs/](../)

---

*最后更新: 2025-03-30*

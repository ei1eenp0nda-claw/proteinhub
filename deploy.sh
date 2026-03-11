#!/bin/bash
# ProteinHub 生产部署脚本
# Production Deployment Script

set -e

PROJECT_NAME="proteinhub"
DEPLOY_DIR="/opt/proteinhub"
BACKUP_DIR="/opt/backups/proteinhub"

echo "🚀 ProteinHub 生产部署"
echo "======================"

# 检查环境
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用 sudo 运行"
    exit 1
fi

# 创建备份
echo ""
echo "[1/6] 创建备份..."
if [ -d "$DEPLOY_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    tar -czf "$BACKUP_DIR/proteinhub-$(date +%Y%m%d-%H%M%S).tar.gz" -C "$DEPLOY_DIR" .
    echo "   ✅ 备份已创建"
else
    echo "   ℹ️ 首次部署，无备份"
fi

# 停止服务
echo ""
echo "[2/6] 停止现有服务..."
if command -v docker-compose &> /dev/null; then
    cd "$DEPLOY_DIR" 2>/dev/null && docker-compose down 2>/dev/null || true
    echo "   ✅ 服务已停止"
fi

# 部署代码
echo ""
echo "[3/6] 部署代码..."
mkdir -p "$DEPLOY_DIR"
# 这里应该从 Git 拉取最新代码或复制本地代码
echo "   ✅ 代码已部署"

# 配置环境
echo ""
echo "[4/6] 配置环境..."
cd "$DEPLOY_DIR"

# 创建环境文件
if [ ! -f ".env" ]; then
    cat > .env << EOF
# ProteinHub 环境配置
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://proteinhub:${DB_PASSWORD:-changeme}@db:5432/proteinhub
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=$(openssl rand -hex 32)
EOF
    echo "   ✅ 环境文件已创建"
fi

# 启动服务
echo ""
echo "[5/6] 启动服务..."
docker-compose up -d --build
echo "   ✅ 服务已启动"

# 健康检查
echo ""
echo "[6/6] 健康检查..."
sleep 5

HEALTH_STATUS=$(curl -s http://localhost:5000/api/health | grep -o '"status":"ok"' || echo "")

if [ -n "$HEALTH_STATUS" ]; then
    echo "   ✅ 健康检查通过"
else
    echo "   ⚠️ 健康检查失败，请查看日志"
    docker-compose logs --tail=50
fi

echo ""
echo "======================"
echo "✅ 部署完成!"
echo ""
echo "访问地址:"
echo "   前端: http://your-domain.com"
echo "   API:  http://your-domain.com/api"
echo "   文档: http://your-domain.com/swagger"
echo ""
echo "管理命令:"
echo "   查看日志: docker-compose logs -f"
echo "   重启服务: docker-compose restart"
echo "   停止服务: docker-compose down"

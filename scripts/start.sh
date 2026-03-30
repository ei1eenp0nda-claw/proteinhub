#!/bin/bash
# ProteinHub 生产环境启动脚本
# Usage: ./scripts/start.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="/opt/proteinhub"
LOG_FILE="$PROJECT_DIR/logs/deploy.log"

# 日志函数
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a $LOG_FILE
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a $LOG_FILE
    exit 1
}

# 检查环境
check_environment() {
    log "检查环境..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        error "Docker 未安装"
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose 未安装"
    fi
    
    # 检查 .env 文件
    if [ ! -f ".env" ]; then
        warn ".env 文件不存在，使用默认配置"
    fi
    
    # 创建必要目录
    mkdir -p logs data/nginx uploads
    
    log "环境检查通过"
}

# 检查 SSL 证书
check_ssl() {
    if [ ! -f "nginx/ssl/fullchain.pem" ] || [ ! -f "nginx/ssl/privkey.pem" ]; then
        warn "SSL 证书不存在，将使用 HTTP 模式"
        warn "请按照 docs/deployment.md 配置 SSL 证书"
    else
        log "SSL 证书已配置"
    fi
}

# 启动服务
start_services() {
    log "启动 ProteinHub 服务..."
    
    # 拉取最新镜像
    docker-compose pull
    
    # 构建服务
    docker-compose build --no-cache
    
    # 启动服务
    docker-compose up -d
    
    # 等待服务就绪
    log "等待服务就绪..."
    sleep 10
    
    # 健康检查
    if curl -f http://localhost/api/health &> /dev/null; then
        log "✅ 服务启动成功！"
        log "网站地址: https://proteinhub.example.com"
        log "API 地址: https://proteinhub.example.com/api"
    else
        error "服务启动失败，请检查日志: docker-compose logs"
    fi
}

# 显示状态
show_status() {
    echo ""
    log "服务状态:"
    docker-compose ps
    echo ""
    log "容器资源使用:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.PIDs}}"
}

# 主函数
main() {
    log "========== ProteinHub 部署脚本 =========="
    
    check_environment
    check_ssl
    start_services
    show_status
    
    log "部署完成！"
}

# 执行
main "$@"

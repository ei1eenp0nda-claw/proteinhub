#!/bin/bash
# ProteinHub 服务管理脚本
# Usage: ./scripts/manage.sh [start|stop|restart|status|logs|backup|update]

set -e

# 配置
PROJECT_DIR="/opt/proteinhub"
BACKUP_DIR="/opt/proteinhub/backups"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# 检查目录
cd $PROJECT_DIR || error "无法进入项目目录 $PROJECT_DIR"

# 启动服务
do_start() {
    log "启动服务..."
    docker-compose up -d
    sleep 5
    docker-compose ps
}

# 停止服务
do_stop() {
    log "停止服务..."
    docker-compose down
}

# 重启服务
do_restart() {
    log "重启服务..."
    docker-compose restart
}

# 查看状态
do_status() {
    echo "服务状态:"
    docker-compose ps
    echo ""
    echo "资源使用:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.Status}}"
}

# 查看日志
do_logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker-compose logs -f --tail=100
    else
        docker-compose logs -f --tail=100 $service
    fi
}

# 备份数据
do_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    mkdir -p $BACKUP_DIR
    
    log "开始备份..."
    
    # 备份数据库
    log "备份数据库..."
    docker-compose exec -T postgres pg_dump -U proteinhub proteinhub | gzip > $BACKUP_DIR/proteinhub_$timestamp.sql.gz
    
    # 备份数据目录
    log "备份上传文件..."
    tar czf $BACKUP_DIR/uploads_$timestamp.tar.gz -C $PROJECT_DIR data/uploads 2>/dev/null || true
    
    # 备份配置
    log "备份配置文件..."
    tar czf $BACKUP_DIR/config_$timestamp.tar.gz -C $PROJECT_DIR .env nginx/docker-compose.yml
    
    # 清理旧备份 (保留30天)
    find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
    
    log "备份完成: $BACKUP_DIR/proteinhub_$timestamp.sql.gz"
}

# 更新服务
do_update() {
    log "更新服务..."
    
    # 备份
    do_backup
    
    # 拉取代码
    log "拉取最新代码..."
    git pull origin main
    
    # 重建并启动
    log "重新构建..."
    docker-compose build --no-cache
    
    log "启动新版本..."
    docker-compose up -d
    
    log "清理旧镜像..."
    docker image prune -f
    
    log "更新完成！"
}

# 数据库迁移
do_migrate() {
    log "执行数据库迁移..."
    docker-compose exec backend flask db upgrade
}

# 进入容器 shell
do_shell() {
    local service=$1
    service=${service:-backend}
    docker-compose exec $service /bin/sh
}

# 显示帮助
show_help() {
    cat << EOF
ProteinHub 管理脚本

用法: $0 <命令> [参数]

命令:
    start              启动所有服务
    stop               停止所有服务
    restart            重启服务
    status             查看服务状态
    logs [service]     查看日志 (可指定服务名)
    backup             备份数据库和配置
    update             更新到最新版本
    migrate            执行数据库迁移
    shell [service]    进入容器 shell (默认 backend)

示例:
    $0 start           # 启动服务
    $0 logs backend    # 查看后端日志
    $0 shell postgres  # 进入数据库容器

EOF
}

# 主逻辑
case "${1:-help}" in
    start)
        do_start
        ;;
    stop)
        do_stop
        ;;
    restart)
        do_restart
        ;;
    status)
        do_status
        ;;
    logs)
        do_logs $2
        ;;
    backup)
        do_backup
        ;;
    update)
        do_update
        ;;
    migrate)
        do_migrate
        ;;
    shell)
        do_shell $2
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        error "未知命令: $1\n运行 '$0 help' 查看帮助"
        ;;
esac

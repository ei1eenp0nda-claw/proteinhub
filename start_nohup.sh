#!/bin/bash
# ProteinHub 后台启动脚本

LOG_FILE="/tmp/proteinhub.log"
PID_FILE="/tmp/proteinhub.pid"

echo "🧬 启动 ProteinHub 后端服务..."
echo "================================"

cd /root/.openclaw/workspace/projects/proteinhub/backend

# 设置环境变量
export FLASK_ENV=production
export DATABASE_URL="sqlite:///proteinhub.db"

# 如果进程已在运行，先停止
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "⚠️  服务已在运行 (PID: $OLD_PID)，先停止..."
        kill "$OLD_PID"
        sleep 2
    fi
fi

# 启动服务
nohup python3 -c "
import sys
sys.path.insert(0, '.')

from app import app, db

# 创建数据库表
with app.app_context():
    db.create_all()
    print('✅ 数据库初始化完成')

# 运行服务 (关闭 debug 模式)
app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
" > "$LOG_FILE" 2>&1 &

# 保存 PID
echo $! > "$PID_FILE"
NEW_PID=$(cat "$PID_FILE")

echo ""
echo "🚀 服务已启动!"
echo "   PID: $NEW_PID"
echo "   日志: $LOG_FILE"
echo ""

# 等待服务启动
sleep 3

# 检查服务状态
if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✅ 服务运行正常!"
    echo "   访问地址: http://localhost:5000"
    echo "   健康检查: http://localhost:5000/api/health"
else
    echo "⚠️  服务可能尚未就绪，请稍后检查日志"
fi

echo ""
echo "📋 常用命令:"
echo "   查看日志: tail -f /tmp/proteinhub.log"
echo "   停止服务: kill \$(cat /tmp/proteinhub.pid)"

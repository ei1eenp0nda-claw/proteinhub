#!/bin/bash
# ProteinHub 快速启动脚本

echo "🧬 启动 ProteinHub 后端服务..."
echo "================================"

cd /root/.openclaw/workspace/projects/proteinhub/backend

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 设置环境变量
export FLASK_APP=app.py
export FLASK_ENV=development
export SECRET_KEY="dev-secret-key-$(date +%s)"
export DATABASE_URL="sqlite:///proteinhub.db"

# 启动服务
echo ""
echo "🚀 启动 Flask 服务..."
echo "   访问地址: http://localhost:5000"
echo "   API文档: http://localhost:5000/swagger"
echo "   按 Ctrl+C 停止"
echo ""

python3 -c "
import sys
sys.path.insert(0, '.')

from app import app, db

# 创建数据库表
with app.app_context():
    db.create_all()
    print('✅ 数据库初始化完成')

# 运行服务
app.run(host='0.0.0.0', port=5000, debug=True)
" 2>&1
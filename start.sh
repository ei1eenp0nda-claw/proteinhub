#!/bin/bash
# ProteinHub 快速启动脚本

echo "🚀 ProteinHub 启动脚本"
echo "======================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 请先安装 Python 3.11+"
    exit 1
fi

# 创建虚拟环境
echo ""
echo "📦 创建虚拟环境..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo ""
echo "📥 安装依赖..."
pip install -q Flask==3.0.0 Flask-SQLAlchemy==3.1.1 Flask-CORS==4.0.0 SQLAlchemy==2.0.23 PyJWT==2.8.0 python-dotenv==1.0.0 requests==2.31.0

# 使用 SQLite 开发模式
echo ""
echo "⚙️ 配置环境..."
export DATABASE_URL="sqlite:///proteinhub_dev.db"
export JWT_SECRET_KEY="dev-secret-key-$(date +%s)"
export FLASK_ENV="development"

# 初始化数据库
echo ""
echo "🗄️ 初始化数据库..."
python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('✅ 数据库表创建完成')
"

# 初始化示例数据
echo ""
echo "🧬 初始化示例数据..."
python3 -c "
import requests
import json

try:
    # 初始化蛋白数据
    response = requests.post('http://localhost:5000/api/init')
    if response.status_code == 200:
        print('✅ 示例数据初始化完成')
    else:
        print('⚠️ 数据初始化可能需要手动触发')
except:
    print('⚠️ 服务尚未启动，数据将在首次启动后初始化')
"

# 启动服务
echo ""
echo "🚀 启动 ProteinHub 后端服务..."
echo ""
echo "服务地址:"
echo "  - API: http://localhost:5000"
echo "  - 健康检查: http://localhost:5000/api/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo "======================"

python3 app.py

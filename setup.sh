#!/bin/bash
# ProteinHub 开发环境设置脚本
# Setup Development Environment

set -e

echo "🧬 ProteinHub 开发环境设置"
echo "=========================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要 Python 3.9+"
    exit 1
fi

echo ""
echo "[1/6] 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ 虚拟环境已创建"
else
    echo "   ℹ️ 虚拟环境已存在"
fi

# 激活虚拟环境
echo ""
echo "[2/6] 激活虚拟环境..."
source venv/bin/activate
echo "   ✅ 虚拟环境已激活"

# 升级 pip
echo ""
echo "[3/6] 升级 pip..."
pip install --upgrade pip -q
echo "   ✅ pip 已升级"

# 安装依赖
echo ""
echo "[4/6] 安装后端依赖..."
cd backend
pip install -r requirements.txt -q
echo "   ✅ 后端依赖已安装"

# 安装前端依赖
echo ""
echo "[5/6] 安装前端依赖..."
cd ../frontend
if command -v npm &> /dev/null; then
    npm install -q
    echo "   ✅ 前端依赖已安装"
else
    echo "   ⚠️ npm 未安装，跳过前端依赖"
fi

cd ..

# 创建必要目录
echo ""
echo "[6/6] 创建项目目录..."
mkdir -p backend/logs
mkdir -p backend/uploads
mkdir -p data/cache
echo "   ✅ 目录已创建"

echo ""
echo "=========================="
echo "✅ 开发环境设置完成!"
echo ""
echo "使用方式:"
echo "   1. source venv/bin/activate"
echo "   2. cd backend && python3 app.py"
echo "   3. cd frontend && npm run dev"
echo ""
echo "运行测试:"
echo "   cd backend && pytest tests/"
echo ""
echo "Docker 方式:"
echo "   docker-compose up -d"

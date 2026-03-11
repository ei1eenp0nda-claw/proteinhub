#!/usr/bin/env python3
"""
ProteinHub 快速启动脚本 - 使用SQLite
"""
import os
import sys

# 设置环境变量
os.environ['FLASK_APP'] = 'app.py'
os.environ['FLASK_ENV'] = 'development'
os.environ['SECRET_KEY'] = 'proteinhub-dev-secret-key'
os.environ['DATABASE_URL'] = 'sqlite:///proteinhub.db'
os.environ['JWT_SECRET_KEY'] = 'jwt-secret-for-dev-only'

# 添加到路径
sys.path.insert(0, '/root/.openclaw/workspace/projects/proteinhub/backend')

from app import app, db

# 创建数据库表
print("🧬 初始化 ProteinHub 数据库...")
with app.app_context():
    db.create_all()
    print("✅ 数据库表已创建")

print("\n🚀 启动 Flask 服务...")
print("   访问地址: http://0.0.0.0:5000")
print("   API文档: http://0.0.0.0:5000/swagger")
print("   内容生成测试: http://0.0.0.0:5000/api/content/test")
print("\n按 Ctrl+C 停止服务\n")

# 启动服务
app.run(host='0.0.0.0', port=5000, debug=True)
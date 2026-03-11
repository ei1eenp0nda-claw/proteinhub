# ProteinHub 部署指南

## 快速开始 (Docker - 推荐)

### 1. 使用 Docker Compose 一键启动

```bash
cd proteinhub

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

服务将运行在：
- 前端: http://localhost:5173
- 后端 API: http://localhost:5000
- API 文档: http://localhost:5000/swagger

### 2. 初始化数据

```bash
# 初始化示例蛋白数据
curl -X POST http://localhost:5000/api/init
```

---

## 手动部署

### 后端部署

**环境要求：**
- Python 3.11+
- PostgreSQL 15+ (或使用 SQLite 开发)

**步骤：**

```bash
cd backend

# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
export DATABASE_URL="sqlite:///proteinhub.db"  # 开发用 SQLite
export JWT_SECRET_KEY="your-secret-key-here"
export FLASK_ENV="development"

# 4. 初始化数据库
python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('数据库初始化完成')
"

# 5. 启动服务
python3 app.py
```

**生产环境配置：**

```bash
# 使用 PostgreSQL
export DATABASE_URL="postgresql://user:password@localhost:5432/proteinhub"
export JWT_SECRET_KEY="your-production-secret-key"
export FLASK_ENV="production"

# 可选: Redis 缓存
export REDIS_URL="redis://localhost:6379/0"
```

---

### 前端部署

**环境要求：**
- Node.js 20+
- npm 或 yarn

**步骤：**

```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 开发模式启动
npm run dev

# 3. 生产构建
npm run build
```

---

## 生产部署

### 使用 Docker

```bash
# 构建镜像
docker-compose -f docker-compose.yml build

# 生产模式启动
docker-compose -f docker-compose.prod.yml up -d
```

### 使用 Gunicorn + Nginx

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动 (4 工作进程)
gunicorn -w 4 -b 0.0.0.0:5000 "app:app"
```

Nginx 配置示例见 `frontend/nginx.conf`

---

## 验证部署

### 1. 健康检查

```bash
curl http://localhost:5000/api/health
```

预期输出：
```json
{"status": "ok", "service": "proteinhub-api", "version": "1.0.0"}
```

### 2. 初始化数据

```bash
curl -X POST http://localhost:5000/api/init
```

### 3. 测试用户注册

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com", "password": "password123"}'
```

---

## 数据导入

### 导入蛋白互作数据

```bash
# 准备 CSV 文件 (protein_interactions.csv)
# 格式: protein_a,protein_b,interaction_score

# 使用管理后台 API 导入
curl -X POST http://localhost:5000/api/admin/import \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"protein_a": "CIDEA", "protein_b": "PLIN1", "interaction_score": 0.85},
      {"protein_a": "PLIN2", "protein_b": "ATGL", "interaction_score": 0.72}
    ]
  }'
```

### 使用批量导入脚本

```bash
cd backend
python3 -c "
from app import app, db
from utils.data_importer import BatchDataLoader

loader = BatchDataLoader(app, db)
loader.generate_sample_data('/tmp/sample.csv', n_interactions=1000)
loader.load_protein_interactions('/tmp/sample.csv')
"
```

---

## 常见问题

### Q: 数据库连接失败
**A:** 检查 `DATABASE_URL` 环境变量，确保 PostgreSQL 已启动。

### Q: JWT 认证失败
**A:** 确保 `JWT_SECRET_KEY` 已设置，且前后端使用相同的密钥。

### Q: 跨域问题
**A:** 检查后端 `CORS_ORIGINS` 配置，确保包含前端域名。

### Q: 缓存不生效
**A:** 安装 Redis 并设置 `REDIS_URL` 环境变量。

---

## 监控与维护

### 查看日志

```bash
# Docker
docker-compose logs -f backend

# 手动部署
tail -f /var/log/proteinhub/app.log
```

### 性能监控

访问管理后台获取实时统计：
```bash
curl http://localhost:5000/api/admin/stats \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### 备份数据

```bash
# PostgreSQL 备份
docker-compose exec db pg_dump -U proteinhub proteinhub > backup.sql

# SQLite 备份
cp backend/proteinhub.db backup/proteinhub-$(date +%Y%m%d).db
```

---

## 开发模式快速启动

如果你只是想快速体验，使用以下最小配置：

```bash
cd proteinhub/backend

# 使用 SQLite，无需安装 PostgreSQL
pip install Flask Flask-SQLAlchemy Flask-CORS PyJWT

# 创建启动脚本
cat > quickstart.py << 'EOF'
import os
os.environ['DATABASE_URL'] = 'sqlite:///proteinhub.db'
os.environ['JWT_SECRET_KEY'] = 'dev-secret-key'

from app import app, db

with app.app_context():
    db.create_all()
    print('✅ 数据库初始化完成')

print('🚀 启动服务...')
app.run(debug=True, host='0.0.0.0', port=5000)
EOF

python3 quickstart.py
```

服务将在 http://localhost:5000 启动。

---

**有问题？** 查看 PROJECT_BOARD.md 或提交 Issue。

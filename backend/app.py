"""
ProteinHub Backend API
Flask + SQLAlchemy + JWT Authentication
"""
from flask import jsonify, request
from datetime import datetime, timedelta
import jwt
import re
from functools import wraps
import os

# 从models导入所有模型和db
from models import app, db, Protein, ProteinInteraction, Post, User, Note, Like, Favorite, Comment, Tag, note_tags

# ==================== 认证工具 ====================

def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """验证密码强度"""
    if len(password) < 8:
        return False, '密码长度至少为8位'
    if not re.search(r'[A-Za-z]', password):
        return False, '密码必须包含至少一个字母'
    if not re.search(r'\d', password):
        return False, '密码必须包含至少一个数字'
    return True, None

def create_access_token(user_id):
    """创建JWT访问令牌"""
    payload = {
        'user_id': user_id,
        'token_type': 'access',
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, 'proteinhub-secret-key', algorithm='HS256')

def create_refresh_token(user_id):
    """创建JWT刷新令牌"""
    payload = {
        'user_id': user_id,
        'token_type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, 'proteinhub-secret-key', algorithm='HS256')

def get_token_from_header():
    """从请求头提取Bearer令牌"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    return parts[1]

def require_auth(f):
    """装饰器：验证JWT令牌"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            return jsonify({'error': '缺少认证令牌'}), 401
        try:
            payload = jwt.decode(token, 'proteinhub-secret-key', algorithms=['HS256'])
            if payload.get('token_type') != 'access':
                return jsonify({'error': '无效的访问令牌'}), 401
            user_id = payload.get('user_id')
            current_user = User.query.get(user_id)
            if not current_user:
                return jsonify({'error': '用户不存在'}), 401
            if not current_user.is_active:
                return jsonify({'error': '账户已被禁用'}), 403
            return f(current_user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'error': '令牌已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '无效的令牌'}), 401
    return decorated_function


def mock_auth(f):
    """Mock认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request.user_id = 1
        return f(*args, **kwargs)
    return decorated_function


# ==================== 路由 ====================

@app.route('/')
def home():
    """首页"""
    return jsonify({
        'service': 'ProteinHub API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'notes': '/api/notes',
            'tags': '/api/tags'
        }
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'ok', 'service': 'proteinhub-api', 'version': '0.2.0'})


# ==================== 认证路由 ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'error': '用户名、邮箱和密码不能为空'}), 400
    
    if not validate_email(email):
        return jsonify({'error': '邮箱格式无效'}), 400
    
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已被使用'}), 409
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': '邮箱已被注册'}), 409
    
    try:
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify({'user_id': user.id, 'message': '注册成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '注册失败'}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': '邮箱和密码不能为空'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'error': '邮箱或密码错误'}), 401
    
    import bcrypt
    pwd = password.encode('utf-8') if isinstance(password, str) else password
    if not bcrypt.checkpw(pwd, user.password_hash.encode('utf-8')):
        return jsonify({'error': '邮箱或密码错误'}), 401
    
    if not user.is_active:
        return jsonify({'error': '账户已被禁用'}), 403
    
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(include_email=True)
    })


@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user(current_user):
    """获取当前用户信息"""
    return jsonify(current_user.to_dict(include_email=True))


# ==================== 蛋白相关路由 ====================

@app.route('/api/proteins', methods=['GET'])
def get_proteins():
    """获取蛋白列表"""
    family = request.args.get('family')
    query = Protein.query
    if family:
        query = query.filter_by(family=family)
    proteins = query.all()
    return jsonify([p.to_dict() for p in proteins])


@app.route('/api/proteins/<int:protein_id>', methods=['GET'])
def get_protein(protein_id):
    """获取单个蛋白详情"""
    protein = Protein.query.get_or_404(protein_id)
    return jsonify(protein.to_dict())


@app.route('/api/proteins/<int:protein_id>/profile', methods=['GET'])
def get_protein_profile(protein_id):
    """获取蛋白主页"""
    protein = Protein.query.get_or_404(protein_id)
    posts = Post.query.filter_by(protein_id=protein_id).order_by(Post.created_at.desc()).all()
    
    return jsonify({
        'protein': protein.to_dict(),
        'biography': {
            'title': f'{protein.name} 蛋白传记',
            'content': protein.description or f'{protein.name} 是 {protein.family} 家族的重要成员。'
        },
        'posts': [p.to_dict() for p in posts]
    })


@app.route('/api/feed', methods=['GET'])
def get_feed():
    """获取推荐Feed"""
    posts = Post.query.order_by(Post.created_at.desc()).limit(20).all()
    return jsonify([p.to_dict() for p in posts])


@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """获取单篇帖子详情"""
    post = Post.query.get_or_404(post_id)
    return jsonify(post.to_dict())


@app.route('/api/posts', methods=['POST'])
@require_auth
def create_post(current_user):
    """创建帖子"""
    data = request.json
    post = Post(
        protein_id=data['protein_id'],
        title=data['title'],
        summary=data.get('summary'),
        source_url=data.get('source_url'),
        source_title=data.get('source_title')
    )
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict()), 201


@app.route('/api/init', methods=['POST'])
def init_data():
    """初始化蛋白数据"""
    proteins = [
        {'name': 'CIDEA', 'family': 'CIDE', 'description': 'Cell Death-Inducing DFF45-like Effector A'},
        {'name': 'CIDEB', 'family': 'CIDE', 'description': 'Cell Death-Inducing DFF45-like Effector B'},
        {'name': 'CIDEC', 'family': 'CIDE', 'description': 'Cell Death-Inducing DFF45-like Effector C'},
        {'name': 'PLIN1', 'family': 'PLIN', 'description': 'Perilipin 1'},
        {'name': 'PLIN2', 'family': 'PLIN', 'description': 'Perilipin 2 (ADFP)'},
        {'name': 'PLIN3', 'family': 'PLIN', 'description': 'Perilipin 3 (TIP47)'},
        {'name': 'PLIN4', 'family': 'PLIN', 'description': 'Perilipin 4'},
        {'name': 'PLIN5', 'family': 'PLIN', 'description': 'Perilipin 5 (OXPAT)'},
    ]
    
    for p_data in proteins:
        if not Protein.query.filter_by(name=p_data['name']).first():
            protein = Protein(**p_data)
            db.session.add(protein)
    
    db.session.commit()
    return jsonify({'message': 'Data initialized', 'count': len(proteins)})


# ==================== 注册笔记和互动路由Blueprints ====================

if __name__ == '__main__':
    from routes.notes import notes_bp
    from routes.interactions import interactions_bp
    
    app.register_blueprint(notes_bp, url_prefix='/api')
    app.register_blueprint(interactions_bp, url_prefix='/api')
    
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='0.0.0.0', port=5000)
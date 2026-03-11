"""
ProteinHub Authentication Routes
认证相关API路由
"""
from flask import Blueprint, request, jsonify
from models.user import db, User
from auth import (
    validate_email, validate_password, AuthError,
    create_access_token, create_refresh_token, decode_token,
    require_auth
)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册
    
    请求体：
        {
            "username": "string",    # 用户名
            "email": "string",       # 邮箱地址
            "password": "string"     # 密码（至少8位，包含字母和数字）
        }
    
    成功响应：
        {
            "user_id": int,
            "message": "注册成功"
        }
    
    错误响应：
        {
            "error": "错误信息"
        }
    """
    data = request.get_json()
    
    # 验证必需字段
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    # 验证字段存在
    if not username:
        return jsonify({'error': '用户名不能为空'}), 400
    if not email:
        return jsonify({'error': '邮箱不能为空'}), 400
    if not password:
        return jsonify({'error': '密码不能为空'}), 400
    
    # 验证邮箱格式
    if not validate_email(email):
        return jsonify({'error': '邮箱格式无效'}), 400
    
    # 验证密码强度
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已被使用'}), 409
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=email).first():
        return jsonify({'error': '邮箱已被注册'}), 409
    
    try:
        # 创建新用户
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'user_id': user.id,
            'message': '注册成功'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '注册失败，请稍后重试'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    
    请求体：
        {
            "email": "string",       # 邮箱地址
            "password": "string"     # 密码
        }
    
    成功响应：
        {
            "access_token": "string",   # JWT访问令牌（24小时有效）
            "refresh_token": "string",  # JWT刷新令牌（7天有效）
            "user": {
                "id": int,
                "username": "string",
                "email": "string"
            }
        }
    
    错误响应：
        {
            "error": "错误信息"
        }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': '邮箱和密码不能为空'}), 400
    
    # 查找用户
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'error': '邮箱或密码错误'}), 401
    
    if not user.is_active:
        return jsonify({'error': '账户已被禁用'}), 403
    
    # 验证密码
    if not user.verify_password(password):
        return jsonify({'error': '邮箱或密码错误'}), 401
    
    # 生成令牌
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(include_email=True)
    })


@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    刷新访问令牌
    
    请求体：
        {
            "refresh_token": "string"  # 刷新令牌
        }
    
    成功响应：
        {
            "access_token": "string",   # 新的访问令牌
            "refresh_token": "string"   # 新的刷新令牌
        }
    """
    data = request.get_json()
    
    if not data or not data.get('refresh_token'):
        return jsonify({'error': '缺少刷新令牌'}), 400
    
    try:
        # 验证刷新令牌
        payload = decode_token(data['refresh_token'], token_type='refresh')
        user_id = payload.get('user_id')
        
        # 验证用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 401
        
        if not user.is_active:
            return jsonify({'error': '账户已被禁用'}), 403
        
        # 生成新令牌
        new_access_token = create_access_token(user.id)
        new_refresh_token = create_refresh_token(user.id)
        
        return jsonify({
            'access_token': new_access_token,
            'refresh_token': new_refresh_token
        })
        
    except AuthError as e:
        return jsonify({'error': e.message}), e.status_code
    except Exception:
        return jsonify({'error': '令牌刷新失败'}), 401


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user(current_user):
    """
    获取当前登录用户信息
    
    请求头：
        Authorization: Bearer <access_token>
    
    成功响应：
        {
            "id": int,
            "username": "string",
            "email": "string",
            "is_active": bool,
            "created_at": "ISO8601字符串"
        }
    """
    return jsonify(current_user.to_dict(include_email=True))


@auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password(current_user):
    """
    修改密码
    
    请求头：
        Authorization: Bearer <access_token>
    
    请求体：
        {
            "old_password": "string",  # 当前密码
            "new_password": "string"   # 新密码
        }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400
    
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    if not old_password or not new_password:
        return jsonify({'error': '当前密码和新密码不能为空'}), 400
    
    # 验证当前密码
    if not current_user.verify_password(old_password):
        return jsonify({'error': '当前密码错误'}), 401
    
    # 验证新密码强度
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    try:
        # 更新密码
        current_user.password_hash = current_user._hash_password(new_password)
        current_user.updated_at = __import__('datetime').datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': '密码修改成功'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '密码修改失败，请稍后重试'}), 500

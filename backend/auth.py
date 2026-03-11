"""
ProteinHub Authentication Module
用户认证和JWT处理
"""
import jwt
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app

# JWT配置
JWT_SECRET_KEY = 'proteinhub-secret-key-change-in-production'  # 生产环境需更改
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AuthError(Exception):
    """认证相关错误"""
    def __init__(self, message, status_code=401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def validate_email(email):
    """
    验证邮箱格式
    
    Args:
        email: 待验证的邮箱地址
        
    Returns:
        bool: 邮箱格式是否有效
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """
    验证密码强度
    
    要求：
    - 至少8位字符
    - 包含至少一个字母
    - 包含至少一个数字
    
    Args:
        password: 待验证的密码
        
    Returns:
        tuple: (是否有效, 错误信息)
    """
    if len(password) < 8:
        return False, '密码长度至少为8位'
    if not re.search(r'[A-Za-z]', password):
        return False, '密码必须包含至少一个字母'
    if not re.search(r'\d', password):
        return False, '密码必须包含至少一个数字'
    return True, None


def create_access_token(user_id):
    """
    创建JWT访问令牌
    
    Args:
        user_id: 用户ID
        
    Returns:
        str: JWT访问令牌
    """
    payload = {
        'user_id': user_id,
        'token_type': 'access',
        'exp': datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id):
    """
    创建JWT刷新令牌
    
    Args:
        user_id: 用户ID
        
    Returns:
        str: JWT刷新令牌
    """
    payload = {
        'user_id': user_id,
        'token_type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token, token_type='access'):
    """
    解码并验证JWT令牌
    
    Args:
        token: JWT令牌
        token_type: 期望的令牌类型（'access' 或 'refresh'）
        
    Returns:
        dict: 解码后的payload
        
    Raises:
        AuthError: 令牌无效或过期
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # 验证令牌类型
        if payload.get('token_type') != token_type:
            raise AuthError(f'无效的{token_type}令牌', 401)
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise AuthError('令牌已过期，请重新登录', 401)
    except jwt.InvalidTokenError:
        raise AuthError('无效的令牌', 401)


def get_token_from_header():
    """
    从请求头中提取Bearer令牌
    
    Returns:
        str: JWT令牌，如果未提供则返回None
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


def require_auth(f):
    """
    装饰器：验证JWT令牌，保护需要登录的路由
    
    使用示例：
        @app.route('/api/protected')
        @require_auth
        def protected_route(current_user):
            return jsonify({'message': f'Hello {current_user.username}'})
    
    Args:
        f: 被装饰的函数
        
    Returns:
        function: 包装后的函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        
        if not token:
            return jsonify({'error': '缺少认证令牌'}), 401
        
        try:
            payload = decode_token(token, token_type='access')
            user_id = payload.get('user_id')
            
            # 从数据库获取用户
            from models.user import User
            current_user = User.query.get(user_id)
            
            if not current_user:
                return jsonify({'error': '用户不存在'}), 401
            
            if not current_user.is_active:
                return jsonify({'error': '账户已被禁用'}), 403
            
            # 将当前用户传递给被装饰的函数
            return f(current_user, *args, **kwargs)
            
        except AuthError as e:
            return jsonify({'error': e.message}), e.status_code
        except Exception as e:
            return jsonify({'error': '认证失败'}), 401
    
    return decorated_function


def optional_auth(f):
    """
    装饰器：可选认证，如果提供了令牌则解析用户，否则current_user为None
    
    使用示例：
        @app.route('/api/content')
        @optional_auth
        def get_content(current_user):
            if current_user:
                return jsonify({'content': 'personalized'})
            return jsonify({'content': 'public'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        current_user = None
        
        if token:
            try:
                payload = decode_token(token, token_type='access')
                user_id = payload.get('user_id')
                from models.user import User
                current_user = User.query.get(user_id)
            except:
                pass  # 可选认证，解析失败不报错
        
        return f(current_user, *args, **kwargs)
    
    return decorated_function

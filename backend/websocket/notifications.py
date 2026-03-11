"""
ProteinHub WebSocket Notifications
实时通知系统

功能：
1. 用户关注/取消关注通知
2. 新帖子发布通知
3. 蛋白互作更新通知
"""
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
from functools import wraps

# 初始化 SocketIO
socketio = SocketIO(cors_allowed_origins="*")


def init_socketio(app):
    """初始化 WebSocket"""
    socketio.init_app(app)
    return socketio


def require_socket_auth(f):
    """WebSocket 认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求中获取 token
        token = request.args.get('token')
        if not token:
            emit('error', {'message': '未提供认证令牌'})
            return
        
        try:
            from auth import decode_token
            payload = decode_token(token)
            request.user_id = payload.get('user_id')
            return f(*args, **kwargs)
        except Exception as e:
            emit('error', {'message': '认证失败'})
            return
    
    return decorated_function


# ============ 事件处理 ============

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print(f'Client connected: {request.sid}')
    emit('connected', {'message': '连接成功', 'sid': request.sid})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print(f'Client disconnected: {request.sid}')


@socketio.on('join_user_room')
@require_socket_auth
def handle_join_user_room():
    """用户加入个人房间"""
    user_id = request.user_id
    room_name = f'user_{user_id}'
    join_room(room_name)
    emit('joined_room', {'room': room_name})


@socketio.on('join_protein_room')
def handle_join_protein_room(data):
    """加入蛋白房间"""
    protein_id = data.get('protein_id')
    if protein_id:
        room_name = f'protein_{protein_id}'
        join_room(room_name)
        emit('joined_room', {'room': room_name, 'protein_id': protein_id})


@socketio.on('leave_protein_room')
def handle_leave_protein_room(data):
    """离开蛋白房间"""
    protein_id = data.get('protein_id')
    if protein_id:
        room_name = f'protein_{protein_id}'
        leave_room(room_name)
        emit('left_room', {'room': room_name})


# ============ 通知发送函数 ============

def notify_user(user_id, event_type, data):
    """
    向特定用户发送通知
    
    Args:
        user_id: 用户ID
        event_type: 事件类型
        data: 通知数据
    """
    room_name = f'user_{user_id}'
    socketio.emit(event_type, data, room=room_name)


def notify_protein_followers(protein_id, event_type, data):
    """
    向蛋白关注者发送通知
    
    Args:
        protein_id: 蛋白ID
        event_type: 事件类型
        data: 通知数据
    """
    room_name = f'protein_{protein_id}'
    socketio.emit(event_type, data, room=room_name)


def broadcast_to_all(event_type, data):
    """广播给所有连接"""
    socketio.emit(event_type, data, broadcast=True)


# ============ 业务事件通知 ============

def notify_new_post(protein_id, post_data):
    """
    新帖子发布通知
    
    Args:
        protein_id: 蛋白ID
        post_data: 帖子数据
    """
    notify_protein_followers(protein_id, 'new_post', {
        'protein_id': protein_id,
        'post': post_data,
        'timestamp': __import__('datetime').datetime.utcnow().isoformat()
    })


def notify_protein_updated(protein_id, update_data):
    """
    蛋白信息更新通知
    
    Args:
        protein_id: 蛋白ID
        update_data: 更新数据
    """
    notify_protein_followers(protein_id, 'protein_updated', {
        'protein_id': protein_id,
        'changes': update_data
    })


def notify_interaction_added(protein_a_id, protein_b_id, score):
    """
    新增蛋白互作通知
    
    Args:
        protein_a_id: 蛋白A ID
        protein_b_id: 蛋白B ID
        score: 互作分数
    """
    # 通知两个蛋白的关注者
    data = {
        'interaction': {
            'protein_a_id': protein_a_id,
            'protein_b_id': protein_b_id,
            'score': score
        }
    }
    notify_protein_followers(protein_a_id, 'new_interaction', data)
    notify_protein_followers(protein_b_id, 'new_interaction', data)


def notify_followed_user_new_activity(user_id, activity_data):
    """
    关注的用户有新活动
    
    Args:
        user_id: 用户ID
        activity_data: 活动数据
    """
    # 这里可以实现关注用户功能
    pass


# ============ 系统通知 ============

def notify_system_message(user_id, message, level='info'):
    """
    发送系统消息
    
    Args:
        user_id: 用户ID (None 则广播)
        message: 消息内容
        level: 级别 (info, warning, error)
    """
    data = {
        'message': message,
        'level': level,
        'timestamp': __import__('datetime').datetime.utcnow().isoformat()
    }
    
    if user_id:
        notify_user(user_id, 'system_message', data)
    else:
        broadcast_to_all('system_message', data)


# ============ 实时统计 ============

def get_online_users_count():
    """获取在线用户数"""
    return len(socketio.server.manager.rooms.get('/', {}))


def emit_stats_update():
    """发送统计更新"""
    from utils.performance import get_monitor
    
    monitor = get_monitor()
    stats = monitor.get_stats()
    
    broadcast_to_all('stats_update', {
        'online_users': get_online_users_count(),
        'total_requests': stats.get('total_requests', 0),
        'avg_response_time': stats.get('avg_response_time', 0)
    })

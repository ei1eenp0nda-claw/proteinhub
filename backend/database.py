"""
ProteinHub Database Configuration
数据库连接配置和管理
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/proteinhub')
SQLALCHEMY_POOL_SIZE = int(os.getenv('SQLALCHEMY_POOL_SIZE', '10'))
SQLALCHEMY_MAX_OVERFLOW = int(os.getenv('SQLALCHEMY_MAX_OVERFLOW', '20'))
SQLALCHEMY_POOL_TIMEOUT = int(os.getenv('SQLALCHEMY_POOL_TIMEOUT', '30'))


def create_db_engine():
    """
    创建数据库引擎，配置连接池
    
    Returns:
        Engine: SQLAlchemy 引擎实例
    """
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=SQLALCHEMY_POOL_SIZE,
        max_overflow=SQLALCHEMY_MAX_OVERFLOW,
        pool_timeout=SQLALCHEMY_POOL_TIMEOUT,
        pool_pre_ping=True,  # 自动检测断开的连接
        pool_recycle=3600,   # 1小时后回收连接
        echo=False
    )
    return engine


def init_db(app, db):
    """
    初始化数据库
    
    Args:
        app: Flask 应用实例
        db: SQLAlchemy 实例
    """
    # 创建所有表
    with app.app_context():
        db.create_all()
        print("✅ Database tables created")


def check_db_connection(engine):
    """
    检查数据库连接是否正常
    
    Args:
        engine: SQLAlchemy 引擎
        
    Returns:
        tuple: (是否成功, 错误信息)
    """
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return True, None
    except Exception as e:
        return False, str(e)

"""
ProteinHub Cache Layer
缓存层实现

支持：
1. Redis 缓存
2. 内存缓存（备用）
3. 缓存装饰器
"""
import json
import hashlib
from functools import wraps
from datetime import datetime, timedelta
from typing import Any, Optional, Callable
import pickle


class CacheBackend:
    """缓存后端基类"""
    
    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError
    
    def set(self, key: str, value: Any, expire: int = 300):
        raise NotImplementedError
    
    def delete(self, key: str):
        raise NotImplementedError
    
    def clear(self):
        raise NotImplementedError


class MemoryCache(CacheBackend):
    """内存缓存（适用于开发和测试）"""
    
    def __init__(self):
        self._cache = {}
        self._expire = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            # 检查是否过期
            if key in self._expire:
                if datetime.now() > self._expire[key]:
                    del self._cache[key]
                    del self._expire[key]
                    return None
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any, expire: int = 300):
        self._cache[key] = value
        if expire > 0:
            self._expire[key] = datetime.now() + timedelta(seconds=expire)
    
    def delete(self, key: str):
        self._cache.pop(key, None)
        self._expire.pop(key, None)
    
    def clear(self):
        self._cache.clear()
        self._expire.clear()


class RedisCache(CacheBackend):
    """Redis 缓存（生产环境）"""
    
    def __init__(self, redis_client):
        self._redis = redis_client
    
    def get(self, key: str) -> Optional[Any]:
        try:
            data = self._redis.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: int = 300):
        try:
            data = pickle.dumps(value)
            self._redis.setex(key, expire, data)
        except Exception as e:
            print(f"Redis set error: {e}")
    
    def delete(self, key: str):
        try:
            self._redis.delete(key)
        except Exception as e:
            print(f"Redis delete error: {e}")
    
    def clear(self):
        try:
            self._redis.flushdb()
        except Exception as e:
            print(f"Redis clear error: {e}")


class Cache:
    """缓存管理器"""
    
    def __init__(self, backend: Optional[CacheBackend] = None):
        self._backend = backend or MemoryCache()
        self._default_expire = 300  # 默认5分钟
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [prefix]
        
        # 添加位置参数
        for arg in args:
            key_parts.append(str(arg))
        
        # 添加关键字参数（排序以确保一致性）
        for k in sorted(kwargs.keys()):
            key_parts.append(f"{k}={kwargs[k]}")
        
        key = ':'.join(key_parts)
        
        # 如果键太长，使用哈希
        if len(key) > 200:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            key = f"{prefix}:{key_hash}"
        
        return key
    
    def get(self, key: str) -> Optional[Any]:
        return self._backend.get(key)
    
    def set(self, key: str, value: Any, expire: Optional[int] = None):
        self._backend.set(key, value, expire or self._default_expire)
    
    def delete(self, key: str):
        self._backend.delete(key)
    
    def cached(self, prefix: str, expire: Optional[int] = None):
        """
        缓存装饰器
        
        用法：
            @cache.cached('protein_list', expire=60)
            def get_proteins(page=1, per_page=20):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = self._make_key(prefix, *args, **kwargs)
                
                # 尝试从缓存获取
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 存入缓存
                self.set(cache_key, result, expire)
                
                return result
            
            # 添加清除缓存的方法
            wrapper.cache_clear = lambda: self.delete(
                self._make_key(prefix)
            )
            
            return wrapper
        return decorator
    
    def invalidate_pattern(self, pattern: str):
        """清除匹配模式的缓存（仅Redis支持）"""
        if isinstance(self._backend, RedisCache):
            try:
                for key in self._backend._redis.scan_iter(match=pattern):
                    self._backend.delete(key)
            except Exception as e:
                print(f"Cache invalidate error: {e}")


# 全局缓存实例
_cache_instance = None

def init_cache(redis_url: Optional[str] = None):
    """初始化缓存"""
    global _cache_instance
    
    if redis_url:
        try:
            import redis
            client = redis.from_url(redis_url)
            backend = RedisCache(client)
            print("✅ Redis 缓存已启用")
        except Exception as e:
            print(f"⚠️ Redis 连接失败，使用内存缓存: {e}")
            backend = MemoryCache()
    else:
        backend = MemoryCache()
        print("✅ 内存缓存已启用")
    
    _cache_instance = Cache(backend)
    return _cache_instance

def get_cache() -> Cache:
    """获取缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = Cache(MemoryCache())
    return _cache_instance


# 常用缓存装饰器
def cache_protein_detail(expire: int = 300):
    """缓存蛋白详情"""
    return get_cache().cached('protein_detail', expire)

def cache_protein_list(expire: int = 60):
    """缓存蛋白列表"""
    return get_cache().cached('protein_list', expire)

def cache_feed(expire: int = 30):
    """缓存 Feed"""
    return get_cache().cached('feed', expire)

def cache_recommendations(expire: int = 300):
    """缓存推荐结果"""
    return get_cache().cached('recommendations', expire)


# 缓存清除工具
def invalidate_protein_cache(protein_id: int):
    """清除蛋白相关缓存"""
    cache = get_cache()
    cache.delete(f'protein_detail:{protein_id}')
    cache.invalidate_pattern('protein_list:*')

def invalidate_feed_cache():
    """清除 Feed 缓存"""
    get_cache().invalidate_pattern('feed:*')

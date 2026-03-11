"""
ProteinHub Performance Monitor
性能监控工具
"""
import time
import functools
from datetime import datetime
from typing import Dict, List, Optional, Callable
from collections import defaultdict
import json


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.slow_queries = []
        self.request_count = 0
        self.error_count = 0
    
    def record_request(self, endpoint: str, duration: float, status_code: int):
        """记录请求"""
        self.request_count += 1
        
        self.metrics['requests'].append({
            'endpoint': endpoint,
            'duration': duration,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat()
        })
        
        # 记录慢查询（超过500ms）
        if duration > 0.5:
            self.slow_queries.append({
                'endpoint': endpoint,
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            })
        
        # 记录错误
        if status_code >= 400:
            self.error_count += 1
    
    def record_db_query(self, query: str, duration: float):
        """记录数据库查询"""
        self.metrics['db_queries'].append({
            'query': query[:200],  # 截断长查询
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        })
        
        # 记录慢查询（超过100ms）
        if duration > 0.1:
            self.slow_queries.append({
                'query': query[:200],
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            })
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        if not self.metrics['requests']:
            return {
                'total_requests': 0,
                'error_rate': 0,
                'avg_response_time': 0,
                'slow_queries': 0
            }
        
        requests = self.metrics['requests'][-1000:]  # 最近1000个请求
        durations = [r['duration'] for r in requests]
        
        return {
            'total_requests': self.request_count,
            'recent_requests': len(requests),
            'error_count': self.error_count,
            'error_rate': self.error_count / max(self.request_count, 1),
            'avg_response_time': sum(durations) / len(durations),
            'max_response_time': max(durations),
            'min_response_time': min(durations),
            'slow_queries': len(self.slow_queries),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """获取慢查询列表"""
        return sorted(
            self.slow_queries,
            key=lambda x: x['duration'],
            reverse=True
        )[:limit]
    
    def clear(self):
        """清除数据"""
        self.metrics.clear()
        self.slow_queries.clear()
        self.request_count = 0
        self.error_count = 0


# 全局监控实例
_monitor = PerformanceMonitor()

def get_monitor() -> PerformanceMonitor:
    """获取监控实例"""
    return _monitor


# 性能监控装饰器
def monitor_performance(endpoint_name: Optional[str] = None):
    """
    性能监控装饰器
    
    用法：
        @monitor_performance('get_protein')
        def get_protein(protein_id):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            
            try:
                result = func(*args, **kwargs)
                status_code = 200
                return result
            except Exception as e:
                status_code = 500
                raise
            finally:
                duration = time.time() - start
                endpoint = endpoint_name or func.__name__
                get_monitor().record_request(endpoint, duration, status_code)
        
        return wrapper
    return decorator


def profile_db_query(query_func: Callable) -> Callable:
    """数据库查询性能分析装饰器"""
    @functools.wraps(query_func)
    def wrapper(*args, **kwargs):
        start = time.time()
        
        # 获取查询语句（如果可能）
        query_str = str(args[0]) if args else 'unknown'
        
        result = query_func(*args, **kwargs)
        
        duration = time.time() - start
        get_monitor().record_db_query(query_str, duration)
        
        return result
    
    return wrapper


# Flask 中间件
class PerformanceMiddleware:
    """Flask 性能监控中间件"""
    
    def __init__(self, app):
        self.app = app
        
        @app.after_request
        def after_request(response):
            # 这里可以记录请求时间
            return response
    
    def record(self, endpoint: str, duration: float, status_code: int):
        get_monitor().record_request(endpoint, duration, status_code)


# 性能报告生成
def generate_performance_report() -> str:
    """生成性能报告"""
    monitor = get_monitor()
    stats = monitor.get_stats()
    slow_queries = monitor.get_slow_queries(5)
    
    report = f"""
# ProteinHub 性能报告
生成时间: {stats['timestamp']}

## 请求统计
- 总请求数: {stats['total_requests']}
- 近期请求: {stats['recent_requests']}
- 错误数: {stats['error_count']}
- 错误率: {stats['error_rate']:.2%}

## 响应时间
- 平均: {stats['avg_response_time']*1000:.2f}ms
- 最大: {stats['max_response_time']*1000:.2f}ms
- 最小: {stats['min_response_time']*1000:.2f}ms

## 慢查询
数量: {stats['slow_queries']}

Top 5:
"""
    
    for i, sq in enumerate(slow_queries, 1):
        report += f"\n{i}. {sq.get('endpoint', sq.get('query', 'unknown'))[:50]}\n"
        report += f"   耗时: {sq['duration']*1000:.2f}ms\n"
    
    return report

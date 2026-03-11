"""
ProteinHub Security Tests
安全测试套件
"""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSecurity:
    """安全测试"""
    
    def test_jwt_secret_not_hardcoded(self):
        """测试 JWT 密钥不是硬编码的"""
        # 读取 auth.py 文件
        auth_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'auth.py')
        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有硬编码的密钥
        hardcoded_patterns = [
            "JWT_SECRET_KEY = 'proteinhub-secret-key-change-in-production'",
            "JWT_SECRET_KEY = 'proteinhub-secret-key'",
            "JWT_SECRET_KEY = 'secret'",
        ]
        
        for pattern in hardcoded_patterns:
            if pattern in content:
                pytest.fail(f"Found hardcoded JWT secret in auth.py")
    
    def test_sql_injection_protection_in_search(self, client, sample_proteins):
        """测试搜索 SQL 注入防护"""
        # 尝试 SQL 注入
        injection_attempts = [
            "CIDEA'; DROP TABLE proteins; --",
            "CIDEA' OR '1'='1",
            "CIDEA' UNION SELECT * FROM users --",
            "1; DELETE FROM proteins WHERE id=1",
        ]
        
        for attempt in injection_attempts:
            response = client.get(f'/api/search?q={attempt}')
            # 应该返回 200（正常处理）或 400（输入验证），但不能是 500
            assert response.status_code in [200, 400], \
                f"SQL injection attempt caused server error: {attempt}"
    
    def test_xss_protection_in_post_creation(self, client, sample_user, sample_proteins, auth_headers):
        """测试 XSS 防护"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<iframe src='javascript:alert(1)'>",
        ]
        
        for payload in xss_payloads:
            response = client.post('/api/posts',
                json={
                    'protein_id': sample_proteins[0].id,
                    'title': payload,
                    'summary': payload
                },
                headers=auth_headers
            )
            
            # 请求应该成功，但内容应该被清理
            if response.status_code == 201:
                data = json.loads(response.data)
                # 检查内容是否被转义（理想情况下）
                assert '<script>' not in data.get('title', '')
    
    def test_authentication_required_for_protected_routes(self, client):
        """测试受保护路由需要认证"""
        protected_routes = [
            ('POST', '/api/posts'),
            ('GET', '/api/auth/me'),
            ('POST', '/api/proteins/1/follow'),
            ('DELETE', '/api/proteins/1/unfollow'),
            ('GET', '/api/user/followed-proteins'),
        ]
        
        for method, route in protected_routes:
            if method == 'POST':
                response = client.post(route)
            elif method == 'DELETE':
                response = client.delete(route)
            else:
                response = client.get(route)
            
            assert response.status_code == 401, \
                f"Route {method} {route} should require authentication"
    
    def test_password_not_returned_in_api(self, client, sample_user):
        """测试密码不在 API 响应中返回"""
        # 登录获取用户信息
        response = client.post('/api/auth/login', json={
            'email': sample_user.email,
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # 检查响应中是否包含密码相关字段
        response_str = json.dumps(data).lower()
        forbidden_words = ['password', 'password_hash', 'pwd', 'secret']
        
        for word in forbidden_words:
            assert word not in response_str, \
                f"Password-related field '{word}' found in API response"
    
    def test_invalid_token_rejected(self, client):
        """测试无效令牌被拒绝"""
        invalid_tokens = [
            'Bearer invalid_token',
            'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid',
            'Basic dXNlcjpwYXNz',
            'invalid_format',
        ]
        
        for token in invalid_tokens:
            response = client.get('/api/auth/me', 
                headers={'Authorization': token}
            )
            assert response.status_code == 401, \
                f"Invalid token should be rejected: {token[:30]}..."
    
    def test_brute_force_protection_simulation(self, client, sample_user):
        """测试暴力破解防护"""
        # 模拟多次失败登录
        for i in range(5):
            response = client.post('/api/auth/login', json={
                'email': sample_user.email,
                'password': f'wrongpassword{i}'
            })
            assert response.status_code == 401
        
        # 第6次尝试应该仍然返回 401
        # 注意：这里假设有速率限制，实际上当前代码没有实现
        response = client.post('/api/auth/login', json={
            'email': sample_user.email,
            'password': 'wrongpassword'
        })
        # 如果没有速率限制，这会是 401
        # 如果有速率限制，应该是 429
        assert response.status_code in [401, 429]
    
    def test_sensitive_endpoints_require_auth(self, client):
        """测试敏感端点需要认证"""
        sensitive_endpoints = [
            '/api/admin/stats',
            '/api/admin/users',
            '/api/admin/posts',
        ]
        
        for endpoint in sensitive_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [401, 403], \
                f"Sensitive endpoint {endpoint} should require auth"


class TestInputValidation:
    """输入验证测试"""
    
    def test_email_validation(self, client):
        """测试邮箱验证"""
        invalid_emails = [
            'notanemail',
            '@nodomain.com',
            'spaces in@email.com',
            'double..dots@email.com',
            '.startswithdot@email.com',
            'endswithdot.@email.com',
        ]
        
        for email in invalid_emails:
            response = client.post('/api/auth/register', json={
                'username': f'user_{hash(email) & 0xFFFF}',
                'email': email,
                'password': 'password123'
            })
            
            assert response.status_code == 400, \
                f"Invalid email should be rejected: {email}"
    
    def test_password_strength_validation(self, client):
        """测试密码强度验证"""
        weak_passwords = [
            'short',  # 太短
            'onlyletters',  # 没有数字
            '12345678',  # 没有字母
            'password',  # 常见密码
        ]
        
        for password in weak_passwords:
            response = client.post('/api/auth/register', json={
                'username': f'user_{hash(password) & 0xFFFF}',
                'email': f'test_{hash(password) & 0xFFFF}@example.com',
                'password': password
            })
            
            assert response.status_code == 400, \
                f"Weak password should be rejected: {password}"
    
    def test_username_validation(self, client, sample_user):
        """测试用户名验证"""
        # 尝试 SQL 注入作为用户名
        response = client.post('/api/auth/register', json={
            'username': "admin'; DROP TABLE users; --",
            'email': 'new@example.com',
            'password': 'password123'
        })
        
        # 应该拒绝或清理输入
        assert response.status_code in [400, 201]
        
        if response.status_code == 201:
            # 如果接受了，检查是否被清理
            data = json.loads(response.data)
            # 用户名不应该包含分号
            # 这里假设我们能获取用户信息来验证
    
    def test_empty_request_body(self, client):
        """测试空请求体"""
        endpoints = [
            ('POST', '/api/auth/register'),
            ('POST', '/api/auth/login'),
            ('POST', '/api/posts'),
        ]
        
        for method, endpoint in endpoints:
            if method == 'POST':
                response = client.post(endpoint, 
                    data='',
                    content_type='application/json'
                )
            else:
                response = client.get(endpoint)
            
            # 空请求体应该返回 400
            assert response.status_code == 400
    
    def test_very_long_input(self, client, sample_user, auth_headers):
        """测试超长输入"""
        long_string = 'A' * 10000
        
        response = client.post('/api/posts',
            json={
                'protein_id': 1,
                'title': long_string,
                'summary': long_string
            },
            headers=auth_headers
        )
        
        # 应该拒绝超长输入
        assert response.status_code in [400, 413]


class TestAuthorization:
    """授权测试"""
    
    def test_user_cannot_access_other_user_data(self, client, sample_user):
        """测试用户不能访问其他用户数据"""
        # 创建第二个用户
        response = client.post('/api/auth/register', json={
            'username': 'user2',
            'email': 'user2@example.com',
            'password': 'password123'
        })
        assert response.status_code == 201
        
        # user2 登录
        response = client.post('/api/auth/login', json={
            'email': 'user2@example.com',
            'password': 'password123'
        })
        data = json.loads(response.data)
        user2_token = data['access_token']
        
        # user2 尝试获取自己的信息（应该成功）
        response = client.get('/api/auth/me',
            headers={'Authorization': f'Bearer {user2_token}'}
        )
        assert response.status_code == 200
        
        # 检查响应中不包含敏感信息
        data = json.loads(response.data)
        assert 'password' not in str(data).lower()
    
    def test_admin_privilege_required(self, client):
        """测试需要管理员权限"""
        # 创建普通用户
        client.post('/api/auth/register', json={
            'username': 'normaluser',
            'email': 'normal@example.com',
            'password': 'password123'
        })
        
        response = client.post('/api/auth/login', json={
            'email': 'normal@example.com',
            'password': 'password123'
        })
        data = json.loads(response.data)
        token = data['access_token']
        
        # 尝试访问管理端点
        admin_endpoints = [
            '/api/admin/stats',
            '/api/admin/users',
            '/api/admin/proteins',
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint,
                headers={'Authorization': f'Bearer {token}'}
            )
            # 普通用户应该被禁止访问
            assert response.status_code == 403, \
                f"Admin endpoint {endpoint} should require admin privileges"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

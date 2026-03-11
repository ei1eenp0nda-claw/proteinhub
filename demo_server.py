#!/usr/bin/env python3
"""
ProteinHub 独立演示服务器
无需额外依赖，使用Python标准库
"""

import http.server
import socketserver
import json
import urllib.parse
from datetime import datetime
import sys
sys.path.insert(0, '/root/.openclaw/workspace/projects/proteinhub/backend')

# 导入内容生成器
try:
    from crawler.content_generator_v2 import ContentGenerator
    from crawler.pubmed_crawler import PubMedCrawler
    GENERATOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 内容生成器加载失败: {e}")
    GENERATOR_AVAILABLE = False

PORT = 5000

class ProteinHubHandler(http.server.BaseHTTPRequestHandler):
    """自定义请求处理器"""
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self._serve_home()
        elif path == '/api/health':
            self._serve_health()
        elif path == '/api/content/test':
            self._serve_content_test()
        elif path.startswith('/swagger'):
            self._serve_swagger()
        else:
            self._serve_404()
    
    def do_POST(self):
        """处理 POST 请求"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/content/generate':
            self._handle_generate_content()
        elif path == '/api/content/preview':
            self._handle_preview_content()
        else:
            self._serve_404()
    
    def _serve_home(self):
        """首页"""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ProteinHub API</title>
    <style>
        body { font-family: -apple-system, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .method { color: #fff; background: #409eff; padding: 2px 8px; border-radius: 3px; font-size: 12px; }
        .get { background: #67c23a; }
        .post { background: #e6a23c; }
        code { background: #f0f0f0; padding: 2px 5px; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>🧬 ProteinHub API Server</h1>
    <p>科研文献 → 小红书风格内容生成服务</p>
    
    <h2>可用端点</h2>
    <div class="endpoint">
        <span class="method get">GET</span> <code>/api/health</code> - 健康检查
    </div>
    <div class="endpoint">
        <span class="method get">GET</span> <code>/api/content/test</code> - 生成测试内容
    </div>
    <div class="endpoint">
        <span class="method post">POST</span> <code>/api/content/generate</code> - 生成小红书笔记
        <br>Body: {"protein_name": "CIDEA"}
    </div>
    <div class="endpoint">
        <span class="method post">POST</span> <code>/api/content/preview</code> - 预览生成效果
        <br>Body: {"protein_name": "CIDEA", "article": {...}}
    </div>
    
    <h2>前端访问</h2>
    <p>前端地址: <a href="http://localhost:5173">http://localhost:5173</a> (需要单独启动)</p>
    
    <h2>测试生成</h2>
    <button onclick="testGenerate()">测试生成 CIDEA 内容</button>
    <pre id="result"></pre>
    
    <script>
        async function testGenerate() {
            const res = await fetch('/api/content/test');
            const data = await res.json();
            document.getElementById('result').textContent = JSON.stringify(data, null, 2);
        }
    </script>
</body>
</html>"""
        self._send_html(html)
    
    def _serve_health(self):
        """健康检查"""
        self._send_json({'status': 'ok', 'timestamp': datetime.now().isoformat()})
    
    def _serve_content_test(self):
        """测试内容生成"""
        if not GENERATOR_AVAILABLE:
            self._send_json({
                'error': '内容生成器不可用',
                'suggestion': '请安装依赖: pip install flask sqlalchemy requests'
            }, 503)
            return
        
        try:
            generator = ContentGenerator()
            
            # 模拟文献数据
            article = {
                'title': 'The rhythmic coupling of Egr-1 and Cidea regulates age-related metabolic dysfunction',
                'abstract': 'Study reveals mechanism...',
                'authors': ['Wu J', 'Smith A'],
                'journal': 'Nature Communications',
                'pub_date': '2023-03',
                'pmid': '36964140'
            }
            
            post = generator.generate_xiaohongshu_post(article, 'CIDEA')
            
            self._send_json({
                'success': True,
                'data': post,
                'note': '这是模拟数据，实际使用时会搜索PubMed'
            })
        except Exception as e:
            self._send_json({'error': str(e)}, 500)
    
    def _handle_generate_content(self):
        """处理内容生成请求"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(post_data)
            protein_name = data.get('protein_name', 'CIDEA')
            
            if not GENERATOR_AVAILABLE:
                # 返回模拟数据
                self._send_json({
                    'success': True,
                    'data': {
                        'title': f'🔬 {protein_name}研究新突破！',
                        'content': f'姐妹们！今天挖到一篇关于{protein_name}的研究 📑\\n\\n【{protein_name}是干嘛的】\\n简单说就是个重要蛋白，这次发现了新功能。\\n\\n【核心发现】\\n这次搞清楚了它的作用机制。\\n\\n【原文信息】\\n发表于权威期刊',
                        'tags': [protein_name, '科研干货', '文献解读'],
                        'word_count': 150,
                        'reading_time': 1
                    },
                    'note': '演示模式：实际部署时会连接PubMed获取真实文献'
                })
                return
            
            # 实际生成
            generator = ContentGenerator()
            # TODO: 搜索PubMed获取真实文献
            
            self._send_json({
                'success': True,
                'data': {
                    'title': f'🔬 {protein_name}内容生成成功',
                    'note': '完整功能需要安装依赖并配置PubMed API'
                }
            })
            
        except json.JSONDecodeError:
            self._send_json({'error': 'Invalid JSON'}, 400)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)
    
    def _handle_preview_content(self):
        """处理预览请求"""
        self._handle_generate_content()
    
    def _serve_swagger(self):
        """API文档"""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>ProteinHub API Docs</title>
    <meta charset="UTF-8">
</head>
<body>
    <h1>ProteinHub API 文档</h1>
    <h2>内容生成 API</h2>
    <h3>POST /api/content/generate</h3>
    <p>根据蛋白名称生成小红书风格笔记</p>
    <pre>
Request:
{
    "protein_name": "CIDEA"
}

Response:
{
    "success": true,
    "data": {
        "title": "🔬 CIDEA研究新突破！",
        "content": "...",
        "tags": ["CIDEA", "科研干货"],
        "word_count": 500,
        "reading_time": 2
    }
}
    </pre>
</body>
</html>"""
        self._send_html(html)
    
    def _serve_404(self):
        """404页面"""
        self._send_json({'error': 'Not found', 'path': self.path}, 404)
    
    def _send_json(self, data, status=200):
        """发送JSON响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def _send_html(self, html, status=200):
        """发送HTML响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


def run_server():
    """运行服务器"""
    with socketserver.TCPServer(("", PORT), ProteinHubHandler) as httpd:
        print(f"""
🧬 ProteinHub 演示服务器已启动！
================================
🌐 访问地址: http://localhost:{PORT}
📚 API文档: http://localhost:{PORT}/swagger
🧪 测试端点: http://localhost:{PORT}/api/content/test

💡 提示:
   - 这是独立演示版本，无需安装Flask等依赖
   - 完整功能请使用: python app.py (需要安装requirements.txt)
   - 前端需要单独启动: cd frontend && npm run dev

按 Ctrl+C 停止服务
================================
        """)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✅ 服务器已停止")


if __name__ == "__main__":
    run_server()

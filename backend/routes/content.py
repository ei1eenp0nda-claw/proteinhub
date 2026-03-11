"""
ProteinHub Content Generation API
内容生成 API 路由

自动搜索文献 → LLM生成小红书笔记
"""
from flask import Blueprint, request, jsonify
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.pubmed_crawler import PubMedCrawler
from crawler.content_generator import ContentGenerator, ContentPipeline
from auth import require_auth

content_bp = Blueprint('content', __name__, url_prefix='/api/content')

# 初始化爬虫和生成器
crawler = PubMedCrawler()
generator = ContentGenerator()
pipeline = ContentPipeline(crawler, generator)


@content_bp.route('/generate', methods=['POST'])
@require_auth
def generate_content(current_user):
    """
    为蛋白生成小红书风格内容
    
    请求体:
    {
        "protein_name": "CIDEA",
        "use_llm": false  // 是否使用LLM（可选，默认false）
    }
    
    响应:
    {
        "title": "🔬 CIDEA研究新突破！...",
        "content": "正文内容...",
        "tags": ["CIDEA", "脂滴研究", ...],
        "summary": "一句话总结",
        "key_points": ["关键点1", ...],
        "reading_time": 2,
        "source": {
            "title": "原文标题",
            "journal": "Nature Cell Biology",
            "pmid": "12345678",
            "url": "..."
        }
    }
    """
    data = request.get_json()
    
    if not data or not data.get('protein_name'):
        return jsonify({'error': '请提供蛋白名称'}), 400
    
    protein_name = data.get('protein_name')
    use_llm = data.get('use_llm', False)
    
    try:
        print(f"🎯 为用户 {current_user.username} 生成 {protein_name} 的内容")
        
        # 生成内容
        post = pipeline.generate_post_for_protein(protein_name)
        
        if not post:
            return jsonify({
                'error': f'未找到 {protein_name} 的相关文献',
                'suggestion': '请检查蛋白名称是否正确，或稍后再试'
            }), 404
        
        return jsonify({
            'success': True,
            'data': post,
            'protein_name': protein_name,
            'generated_at': __import__('datetime').datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"❌ 内容生成失败: {e}")
        return jsonify({'error': f'内容生成失败: {str(e)}'}), 500


@content_bp.route('/generate-batch', methods=['POST'])
@require_auth
def generate_batch_content(current_user):
    """
    批量生成内容
    
    请求体:
    {
        "protein_names": ["CIDEA", "PLIN1", "ATGL"]
    }
    
    响应:
    {
        "generated": 3,
        "failed": 0,
        "posts": [...]
    }
    """
    data = request.get_json()
    
    if not data or not data.get('protein_names'):
        return jsonify({'error': '请提供蛋白名称列表'}), 400
    
    protein_names = data.get('protein_names')
    
    if len(protein_names) > 10:
        return jsonify({'error': '一次最多生成10个蛋白的内容'}), 400
    
    try:
        print(f"🎯 批量生成 {len(protein_names)} 个蛋白的内容")
        
        posts = pipeline.batch_generate(protein_names)
        
        return jsonify({
            'success': True,
            'generated': len(posts),
            'failed': len(protein_names) - len(posts),
            'posts': posts
        })
        
    except Exception as e:
        print(f"❌ 批量生成失败: {e}")
        return jsonify({'error': f'批量生成失败: {str(e)}'}), 500


@content_bp.route('/tags/suggest', methods=['GET'])
def suggest_tags():
    """
    根据关键词推荐标签
    
    Query参数:
        q: 搜索关键词
        
    响应:
    {
        "tags": ["CIDEA", "脂滴研究", "脂质代谢", ...]
    }
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'tags': []})
    
    # 基于关键词生成推荐标签
    suggested_tags = []
    
    # 蛋白相关
    if 'cide' in query.lower():
        suggested_tags.extend(['CIDE', 'CIDEA', 'CIDEB'])
    if 'plin' in query.lower():
        suggested_tags.extend(['PLIN', 'PLIN1', 'PLIN2', '脂滴蛋白'])
    
    # 研究领域
    if any(word in query.lower() for word in ['lipid', 'fat', 'droplet']):
        suggested_tags.extend(['脂滴研究', '脂质代谢', '脂肪代谢'])
    if any(word in query.lower() for word in ['cancer', 'tumor']):
        suggested_tags.extend(['癌症研究', '肿瘤学', '肿瘤代谢'])
    if any(word in query.lower() for word in ['interaction', 'binding']):
        suggested_tags.extend(['蛋白互作', '分子机制', 'PPI'])
    
    # 通用标签
    suggested_tags.extend(['科研干货', '文献解读', '学术分享', '生物医学'])
    
    return jsonify({
        'query': query,
        'tags': suggested_tags[:10]  # 限制返回数量
    })


@content_bp.route('/preview', methods=['POST'])
def preview_content():
    """
    预览内容（无需登录）
    
    请求体:
    {
        "article": {
            "title": "论文标题",
            "abstract": "摘要",
            "journal": "期刊"
        },
        "protein_name": "CIDEA"
    }
    """
    data = request.get_json()
    
    if not data or not data.get('article') or not data.get('protein_name'):
        return jsonify({'error': '请提供文章信息和蛋白名称'}), 400
    
    article = data.get('article')
    protein_name = data.get('protein_name')
    
    try:
        # 生成预览
        post = generator.generate_xiaohongshu_post(article, protein_name)
        
        return jsonify({
            'success': True,
            'preview': post
        })
        
    except Exception as e:
        print(f"❌ 预览生成失败: {e}")
        return jsonify({'error': f'预览生成失败: {str(e)}'}), 500


# 初始化时加载生成器
print("✅ 内容生成 API 已加载")

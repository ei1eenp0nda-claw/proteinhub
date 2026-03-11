"""
Flask-RESTX API Documentation for ProteinHub
自动生成 Swagger API 文档
"""
from flask import Flask
from flask_restx import Api, Resource, fields

app = Flask(__name__)
api = Api(app, version='1.0', title='ProteinHub API',
         description='ProteinHub REST API 文档')

# 命名空间
auth_ns = api.namespace('api/auth', description='认证相关')
protein_ns = api.namespace('api/proteins', description='蛋白相关')
feed_ns = api.namespace('api', description='Feed相关')
rec_ns = api.namespace('api/recommend', description='推荐相关')
follow_ns = api.namespace('api', description='关注相关')

# 数据模型
user_model = api.model('User', {
    'id': fields.Integer(description='用户ID'),
    'username': fields.String(description='用户名'),
    'email': fields.String(description='邮箱'),
    'is_active': fields.Boolean(description='是否激活'),
    'created_at': fields.String(description='创建时间')
})

protein_model = api.model('Protein', {
    'id': fields.Integer(description='蛋白ID'),
    'name': fields.String(description='蛋白名称'),
    'family': fields.String(description='蛋白家族'),
    'uniprot_id': fields.String(description='UniProt ID'),
    'description': fields.String(description='描述')
})

post_model = api.model('Post', {
    'id': fields.Integer(description='帖子ID'),
    'protein_id': fields.Integer(description='蛋白ID'),
    'protein_name': fields.String(description='蛋白名称'),
    'title': fields.String(description='标题'),
    'summary': fields.String(description='摘要'),
    'source_url': fields.String(description='来源链接'),
    'created_at': fields.String(description='创建时间')
})

# Auth 路由
@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(api.model('RegisterInput', {
        'username': fields.String(required=True, description='用户名'),
        'email': fields.String(required=True, description='邮箱'),
        'password': fields.String(required=True, description='密码')
    }))
    @auth_ns.marshal_with(api.model('RegisterOutput', {
        'user_id': fields.Integer(),
        'message': fields.String()
    }))
    def post(self):
        """用户注册"""
        pass

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(api.model('LoginInput', {
        'email': fields.String(required=True, description='邮箱'),
        'password': fields.String(required=True, description='密码')
    }))
    @auth_ns.marshal_with(api.model('LoginOutput', {
        'access_token': fields.String(),
        'refresh_token': fields.String(),
        'user': fields.Nested(user_model)
    }))
    def post(self):
        """用户登录"""
        pass

@auth_ns.route('/me')
class Me(Resource):
    @auth_ns.marshal_with(user_model)
    def get(self):
        """获取当前用户信息"""
        pass

# Protein 路由
@protein_ns.route('/')
class ProteinList(Resource):
    @protein_ns.marshal_list_with(protein_model)
    def get(self):
        """获取蛋白列表"""
        pass

@protein_ns.route('/<int:protein_id>')
class ProteinDetail(Resource):
    @protein_ns.marshal_with(protein_model)
    def get(self, protein_id):
        """获取蛋白详情"""
        pass

@protein_ns.route('/<int:protein_id>/profile')
class ProteinProfile(Resource):
    def get(self, protein_id):
        """获取蛋白主页"""
        pass

# Feed 路由
@feed_ns.route('/feed')
class Feed(Resource):
    @feed_ns.marshal_list_with(post_model)
    def get(self):
        """获取推荐Feed"""
        pass

# 推荐路由
@rec_ns.route('/personalized')
class PersonalizedRecommend(Resource):
    def get(self):
        """个性化推荐"""
        pass

@rec_ns.route('/cold-start')
class ColdStartRecommend(Resource):
    def post(self):
        """冷启动推荐"""
        pass

@rec_ns.route('/explore')
class ExploreRecommend(Resource):
    def get(self):
        """探索推荐"""
        pass

if __name__ == '__main__':
    app.run(debug=True)

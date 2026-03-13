"""
初始化测试数据脚本
用于创建测试用户、标签和笔记
"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/projects/proteinhub/backend')

from app import app, db, User, Tag, Note
import json
from datetime import datetime, timedelta
import random

def init_test_data():
    """初始化测试数据"""
    with app.app_context():
        # 创建表
        db.create_all()
        
        print("开始初始化测试数据...")
        
        # 1. 创建测试用户
        test_users = [
            {'username': '科研达人', 'email': 'test1@example.com', 'password': 'Test1234'},
            {'username': '蛋白研究者', 'email': 'test2@example.com', 'password': 'Test1234'},
            {'username': '生物学霸', 'email': 'test3@example.com', 'password': 'Test1234'},
        ]
        
        users = []
        for user_data in test_users:
            user = User.query.filter_by(email=user_data['email']).first()
            if not user:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password']
                )
                db.session.add(user)
                print(f"  创建用户: {user_data['username']}")
            users.append(user)
        
        db.session.commit()
        print(f"✓ 用户创建完成，共 {len(users)} 个用户")
        
        # 2. 创建标签
        test_tags = [
            {'name': 'CIDE', 'description': 'CIDE家族蛋白'},
            {'name': 'PLIN', 'description': '脂滴包被蛋白家族'},
            {'name': '代谢', 'description': '代谢相关研究'},
            {'name': '脂滴', 'description': '脂滴生物学'},
            {'name': '肥胖', 'description': '肥胖与代谢疾病'},
            {'name': '糖尿病', 'description': '糖尿病研究'},
            {'name': '文献解读', 'description': '文献阅读笔记'},
            {'name': '实验技巧', 'description': '实验方法分享'},
        ]
        
        tags = []
        for tag_data in test_tags:
            tag = Tag.query.filter_by(name=tag_data['name']).first()
            if not tag:
                tag = Tag(name=tag_data['name'], description=tag_data['description'])
                db.session.add(tag)
                print(f"  创建标签: {tag_data['name']}")
            tags.append(tag)
        
        db.session.commit()
        print(f"✓ 标签创建完成，共 {len(tags)} 个标签")
        
        # 3. 创建测试笔记
        test_notes = [
            {
                'title': '🔬 CIDEA蛋白最新研究进展',
                'content': '''
今天读了篇关于CIDEA的Nature Communications文章，来分享一下～

📌 研究亮点：
• CIDEA与Egr-1形成节律性耦合调控
• 在衰老相关的代谢功能障碍中起关键作用
• 可能成为治疗代谢疾病的新靶点

💡 我的理解：
CIDEA不仅仅是细胞死亡诱导因子，在脂滴代谢中也发挥重要作用。这项研究揭示了它昼夜节律调控的新机制！

📊 实验方法：
使用了CRISPR筛选和小鼠模型验证，数据很扎实。

#CIDE #代谢 #脂滴 #文献解读
                ''',
                'paper_title': 'The rhythmic coupling of Egr-1 and Cidea regulates age-related metabolic dysfunction',
                'paper_journal': 'Nature Communications',
                'paper_pub_date': '2023-03',
                'paper_pmid': '36964140',
                'tags': ['CIDE', '代谢', '脂滴', '文献解读']
            },
            {
                'title': '🧬 PLIN蛋白家族全面解析',
                'content': '''
脂滴包被蛋白(PLIN)家族是脂滴研究的核心，今天来系统梳理一下：

🔹 PLIN1：主要在脂肪组织中表达，调控脂滴分解
🔹 PLIN2(ADRP)：广泛表达，脂滴形成的标志物
🔹 PLIN3(TIP47)：参与脂滴运输
🔹 PLIN4：与肥胖密切相关
🔹 PLIN5(OXPAT)：在氧化组织中高表达

📖 关键发现：
不同PLIN成员在不同组织中发挥特异性功能，理解它们有助于开发针对性的代谢疾病治疗策略。

✨ 实验提示：
PLIN2是最常用的脂滴标记物，免疫荧光效果很好！

#PLIN #脂滴 #肥胖 #实验技巧
                ''',
                'paper_title': 'Perilipin proteins and their roles in lipid metabolism',
                'paper_journal': 'Progress in Lipid Research',
                'paper_pub_date': '2022-08',
                'paper_pmid': '35973321',
                'tags': ['PLIN', '脂滴', '肥胖', '实验技巧']
            },
            {
                'title': '💊 CIDEC在糖尿病中的作用机制',
                'content': '''
最新研究揭示了CIDEC在胰岛素抵抗中的新角色：

🎯 核心发现：
1. CIDEC表达在糖尿病小鼠中显著上调
2. 敲低CIDEC可改善胰岛素敏感性
3. 通过调控脂滴-线粒体接触发挥作用

🔬 机制解析：
CIDEC促进脂滴与线粒体的物理接触，影响脂肪酸氧化效率。在糖尿病状态下，这种调控失衡导致脂质积累。

💊 临床意义：
CIDEC可能成为2型糖尿病治疗的潜在靶点。

欢迎交流讨论！有相关问题可以在评论区留言～

#CIDE #糖尿病 #代谢 #肥胖
                ''',
                'paper_title': 'CIDEC regulates insulin sensitivity through lipid droplet-mitochondria interaction',
                'paper_journal': 'Diabetes',
                'paper_pub_date': '2023-11',
                'paper_pmid': '37856712',
                'tags': ['CIDE', '糖尿病', '代谢', '肥胖']
            },
            {
                'title': '📚 脂滴生物学研究进展（2023年度回顾）',
                'content': '''
2023年是脂滴生物学的大年，整理了本年度的重要突破：

🏆 Top 5 重要发现：

1️⃣ 脂滴与内质网的动态接触调控
   • Nature Cell Biology
   • 揭示了新的脂滴生成机制

2️⃣ 脂滴在免疫反应中的作用
   • Science Immunology
   • 巨噬细胞脂滴参与炎症调控

3️⃣ CIDE家族蛋白的结构解析
   • Cell Metabolism
   • 冷冻电镜揭示分子机制

4️⃣ 脂滴与线粒体对话新机制
   • EMBO Journal
   • 代谢重编程的关键节点

5️⃣ 脂滴标记物开发
   • Nature Methods
   • 新型荧光探针

📝 个人感想：
脂滴从被忽视的细胞器逐渐成为代谢研究的核心，未来可期！

#脂滴 #代谢 #文献解读 #2023回顾
                ''',
                'paper_title': 'Annual review of lipid droplet biology 2023',
                'paper_journal': 'Trends in Cell Biology',
                'paper_pub_date': '2023-12',
                'paper_pmid': '38056789',
                'tags': ['脂滴', '代谢', '文献解读']
            },
            {
                'title': '⚗️ 脂滴染色实验protocol分享',
                'content': '''
分享一个我常用的脂滴染色protocol，成功率很高！

🧪 材料：
• BODIPY 493/503 或 Oil Red O
• PBS缓冲液
• 4%多聚甲醛
• DAPI染核

📋 步骤：
1. 细胞爬片，培养至合适密度
2. PBS洗2次
3. 4%多聚甲醛固定15min
4. PBS洗3次，每次5min
5. BODIPY工作液室温孵育30min（避光）
6. PBS洗3次
7. DAPI染核5min
8. PBS洗后封片

💡 关键提示：
✓ BODIPY储液浓度1mg/mL，工作液1:1000
✓ 全程避光操作
✓ 洗涤要充分，减少背景
✓ 建议设置不加染料的阴性对照

🖼️ 预期结果：
脂滴呈绿色荧光，清晰圆形结构，分布在胞质中

有问题欢迎交流！

#实验技巧 #脂滴 #PLIN
                ''',
                'paper_title': 'Protocol for lipid droplet staining in cultured cells',
                'paper_journal': 'Methods in Molecular Biology',
                'paper_pub_date': '2023-06',
                'paper_pmid': '37289123',
                'tags': ['实验技巧', '脂滴', 'PLIN']
            },
            {
                'title': '🎯 CIDEB调控肝脏脂质代谢新机制',
                'content': '''
刚刚在线的Cell Metabolism文章，CIDEB研究又添重磅证据：

🔍 研究背景：
CIDEB是CIDE家族中主要在肝脏表达的成员，但其具体功能仍不完全清楚。

📊 主要结果：
• 肝脏特异性敲除CIDEB减少脂肪变性
• CIDEB通过与ApoB互作影响VLDL组装
• 在NAFLD患者肝脏中CIDEB表达升高

🧬 机制创新点：
首次揭示了CIDEB在VLDL分泌中的分子伴侣功能，为NAFLD治疗提供新思路。

📈 数据质量：
使用了多组学整合分析（转录组+蛋白组+脂质组），数据非常扎实。

值得仔细阅读！

#CIDE #代谢 #肥胖 #文献解读
                ''',
                'paper_title': 'CIDEB regulates hepatic lipid metabolism through VLDL assembly',
                'paper_journal': 'Cell Metabolism',
                'paper_pub_date': '2024-01',
                'paper_pmid': '38123456',
                'tags': ['CIDE', '代谢', '肥胖', '文献解读']
            }
        ]
        
        notes_created = 0
        for i, note_data in enumerate(test_notes):
            # 随机分配给不同用户
            author = users[i % len(users)]
            
            # 生成预览
            content = note_data['content'].strip()
            preview = content[:200] + '...' if len(content) > 200 else content
            
            # 创建笔记
            note = Note(
                author_id=author.id,
                title=note_data['title'],
                content=content,
                preview=preview,
                paper_title=note_data.get('paper_title'),
                paper_authors=json.dumps(['Author A', 'Author B']),
                paper_journal=note_data.get('paper_journal'),
                paper_pub_date=note_data.get('paper_pub_date'),
                paper_pmid=note_data.get('paper_pmid'),
                is_public=True,
                view_count=random.randint(100, 5000),
                like_count=random.randint(10, 500),
                favorite_count=random.randint(5, 200),
                comment_count=random.randint(0, 50),
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            
            # 添加标签
            for tag_name in note_data.get('tags', []):
                tag = Tag.query.filter_by(name=tag_name).first()
                if tag:
                    note.tags.append(tag)
            
            db.session.add(note)
            notes_created += 1
            print(f"  创建笔记: {note_data['title'][:30]}...")
        
        db.session.commit()
        print(f"✓ 笔记创建完成，共 {notes_created} 篇笔记")
        
        print("\n" + "="*50)
        print("测试数据初始化完成！")
        print("="*50)
        print(f"\n可用API端点：")
        print(f"  • GET  /api/notes/feed      - 笔记Feed流")
        print(f"  • GET  /api/notes/<id>      - 笔记详情")
        print(f"  • GET  /api/notes/<id>/related  - 相关笔记")
        print(f"  • POST /api/notes/<id>/like     - 点赞/取消点赞")
        print(f"  • POST /api/notes/<id>/favorite - 收藏/取消收藏")
        print(f"  • GET  /api/notes/<id>/comments - 评论列表")
        print(f"  • POST /api/notes/<id>/comments - 发表评论")
        print(f"  • GET  /api/tags            - 热门标签")
        print(f"  • GET  /api/tags/<tag>/notes    - 标签笔记列表")

if __name__ == '__main__':
    init_test_data()

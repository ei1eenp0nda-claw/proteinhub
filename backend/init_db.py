from models import app, db, User, Note, Like, Favorite, Comment

with app.app_context():
    db.create_all()
    print("数据库表创建成功！")
    
    # 创建测试用户
    if not User.query.filter_by(username='test_user').first():
        user = User(username='test_user', email='test@example.com', password='test123456')
        db.session.add(user)
        db.session.commit()
        print("测试用户创建成功！")
    
    # 创建第二个测试用户
    if not User.query.filter_by(username='demo_user').first():
        user2 = User(username='demo_user', email='demo@example.com', password='demo123456')
        db.session.add(user2)
        db.session.commit()
        print("演示用户创建成功！")
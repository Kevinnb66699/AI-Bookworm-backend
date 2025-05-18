from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # 检查是否已存在超级管理员
    admin = User.query.filter_by(email='admin@aibookworm.com').first()
    
    if not admin:
        # 创建超级管理员
        admin = User(
            username='admin',
            email='admin@aibookworm.com',
            password_hash=generate_password_hash('admin123', method='pbkdf2:sha256')
        )
        db.session.add(admin)
        db.session.commit()
        print("超级管理员已创建！")
        print("用户名: admin")
        print("邮箱: admin@aibookworm.com")
        print("密码: admin123")
    else:
        print("超级管理员已存在！") 
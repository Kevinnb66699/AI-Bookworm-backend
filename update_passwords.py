from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # 获取所有用户
    users = User.query.all()
    
    # 更新每个用户的密码
    for user in users:
        user.password_hash = generate_password_hash('password123', method='pbkdf2:sha256')
    
    # 提交更改
    db.session.commit()
    
    print("所有用户的密码已更新为 'password123'") 
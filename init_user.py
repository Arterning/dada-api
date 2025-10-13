import os
from flask import Flask
from dotenv import load_dotenv
from models import db, User

# 创建Flask应用的最小配置
class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///dada.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# 初始化应用
load_dotenv()
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# 添加测试用户
def create_test_user():
    with app.app_context():
        # 检查用户是否已存在
        existing_user = User.query.filter_by(username='testuser').first()
        if existing_user:
            print("测试用户 'testuser' 已存在")
            return
        
        # 创建新用户
        test_user = User(username='test', nickname='测试用户')
        test_user.set_password('123456')
        
        # 添加到数据库
        db.session.add(test_user)
        db.session.commit()
        
        print(f"测试用户已创建成功！\n用户名: test\n密码: 123456\n用户ID: {test_user.id}")

if __name__ == "__main__":
    create_test_user()
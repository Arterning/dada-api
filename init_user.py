import os
import argparse
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

# 添加用户
def create_user(username, password):
    with app.app_context():
        # 检查用户是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"用户 '{username}' 已存在")
            return
        
        # 创建新用户
        new_user = User(username=username, nickname=username)
        new_user.set_password(password)
        
        # 添加到数据库
        db.session.add(new_user)
        db.session.commit()
        
        print(f"用户已创建成功！\n用户名: {username}\n密码: {password}\n用户ID: {new_user.id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="创建新用户")
    parser.add_argument("username", help="用户名")
    parser.add_argument("password", help="密码")
    args = parser.parse_args()
    create_user(args.username, args.password)
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# 创建Flask应用的最小配置
class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///dada.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# 初始化数据库
load_dotenv()
db = SQLAlchemy()

# 定义用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    nickname = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 关系：一个用户有多个服装
    clothes = db.relationship('Clothing', backref='owner', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

# 定义服装模型
class Clothing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), nullable=False)
    purchase_date = db.Column(db.Date, nullable=True)
    price = db.Column(db.Float, nullable=True)
    wear_count = db.Column(db.Integer, default=0)
    washing_method = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=True, default='良好')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # 外键：服装属于哪个用户
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# 创建Flask应用并初始化数据库
from flask import Flask
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
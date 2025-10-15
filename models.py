from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# 初始化数据库实例
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
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 定义服装模型
class Clothing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), nullable=False)
    purchase_date = db.Column(db.Date, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=True)
    wear_count = db.Column(db.Integer, default=0)
    washing_method = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=True, default='良好')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # 外键：服装属于哪个用户
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class OutfitClothing(db.Model):
    __tablename__ = 'outfit_clothing'  # 显式指定表名
    id = db.Column(db.Integer, primary_key=True)
    outfit_id = db.Column(db.Integer, db.ForeignKey('outfit.id'), nullable=False)
    clothing_id = db.Column(db.Integer, db.ForeignKey('clothing.id'), nullable=False)
    clothing_image = db.Column(db.String(255), nullable=True)
    # 坐标
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    # 旋转角度
    angle = db.Column(db.Float, nullable=False, default=0)
    # 缩放比例
    scale = db.Column(db.Float, nullable=False, default=1)
    
    # 确保一个服装在一个穿搭中只能出现一次
    __table_args__ = (
        db.UniqueConstraint('outfit_id', 'clothing_id', name='_outfit_clothing_uc'),
    )

# 定义穿搭模型
class Outfit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # 关系：一个穿搭有多个服装
    clothes = db.relationship('Clothing', secondary='outfit_clothing', backref='outfits', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 定义当天穿搭和服装的关联表
daily_outfit_clothing = db.Table('daily_outfit_clothing',
    db.Column('daily_outfit_id', db.Integer, db.ForeignKey('daily_outfit.id'), primary_key=True),
    db.Column('clothing_id', db.Integer, db.ForeignKey('clothing.id'), primary_key=True)
)

# 定义当天穿搭模型
class DailyOutfit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    todays_clothes = db.Column(db.Text, nullable=True)  # 用户自己输入的当天穿的衣服描述
    temperature = db.Column(db.String(50), nullable=True)  # 当天气温
    weather = db.Column(db.String(50), nullable=True)  # 当天天气
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系：关联到具体的服装
    clothes = db.relationship('Clothing', secondary=daily_outfit_clothing, backref='daily_outfits', lazy=True)
    
    # 确保一个用户在同一天只有一条穿搭记录
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='_user_date_uc'),
    )



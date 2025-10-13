import os
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import uuid
import jwt
from dotenv import load_dotenv
from models import db, User, Clothing

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///dada.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 配置JWT
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-secret-key')
JWT_EXPIRATION = 24 * 60 * 60  # 24小时

# 初始化数据库
db.init_app(app)

# 创建数据库表
with app.app_context():
    db.create_all()

# 生成JWT令牌
def generate_token(user_id):
    token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=7) # Token expires in 7 days
    }, JWT_SECRET_KEY, algorithm="HS256")
    return token

# 验证JWT令牌
def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# 装饰器：需要登录
def token_required(f):
    def decorator(*args, **kwargs):
        token = None
        
        # 从请求头获取令牌
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': '令牌格式错误'}), 401
        
        if not token:
            return jsonify({'message': '缺少令牌'}), 401
        
        user_id = verify_token(token)
        if not user_id:
            return jsonify({'message': '无效或过期的令牌'}), 401
        
        # 查找用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': '用户不存在'}), 401
        
        # 将用户添加到请求上下文中
        request.user = user
        return f(*args, **kwargs)
    
    decorator.__name__ = f.__name__
    return decorator

# 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 验证输入
    if not data or not 'username' in data or not 'password' in data:
        return jsonify({'message': '缺少用户名或密码'}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': '用户名已存在'}), 400
    
    # 创建新用户
    user = User(username=data['username'])
    user.set_password(data['password'])
    if 'nickname' in data:
        user.nickname = data['nickname']
    
    # 添加到数据库
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': '注册成功'}), 201

# 用户登录
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 验证输入
    if not data or not 'username' in data or not 'password' in data:
        return jsonify({'message': '缺少用户名或密码'}), 400
    
    # 查找用户
    user = User.query.filter_by(username=data['username']).first()
    
    # 验证密码
    if user and user.check_password(data['password']):
        token = generate_token(user.id)
        return jsonify({
            'token': token,
            'user_id': user.id,
            'username': user.username,
            'nickname': user.nickname
        }), 200
    
    return jsonify({'message': '用户名或密码错误'}), 401

# 获取当前用户信息
@app.route('/api/user', methods=['GET'])
@token_required
def get_user():
    user = request.user
    return jsonify({
        'id': user.id,
        'username': user.username,
        'nickname': user.nickname,
        'created_at': user.created_at.isoformat()
    }), 200

# 更新用户信息
@app.route('/api/user', methods=['PUT'])
@token_required
def update_user():
    user = request.user
    data = request.get_json()
    
    # 更新昵称
    if 'nickname' in data:
        user.nickname = data['nickname']
    
    # 更新密码
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    
    # 保存更改
    db.session.commit()
    
    return jsonify({'message': '用户信息更新成功'}), 200

# 服装API

# 添加服装
@app.route('/api/clothes', methods=['POST'])
@token_required
def add_clothing():
    user = request.user
    data = request.get_json()
    
    # 验证必要字段
    if not data or not 'name' in data or not 'category' in data:
        return jsonify({'message': '缺少名称或分类'}), 400
    
    # 创建新服装
    clothing = Clothing(
        name=data['name'],
        category=data['category'],
        user_id=user.id
    )
    
    # 设置可选字段
    if 'image_url' in data:
        clothing.image_url = data['image_url']
    if 'purchase_date' in data:
        try:
            clothing.purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': '购买日期格式错误，应为YYYY-MM-DD'}), 400
    if 'price' in data:
        clothing.price = data['price']
    if 'wear_count' in data:
        clothing.wear_count = data['wear_count']
    if 'washing_method' in data:
        clothing.washing_method = data['washing_method']
    if 'status' in data:
        clothing.status = data['status']
    
    # 添加到数据库
    db.session.add(clothing)
    db.session.commit()
    
    # 返回创建的服装信息
    return jsonify({
        'id': clothing.id,
        'name': clothing.name,
        'image_url': clothing.image_url,
        'category': clothing.category,
        'purchase_date': clothing.purchase_date.isoformat() if clothing.purchase_date else None,
        'price': clothing.price,
        'wear_count': clothing.wear_count,
        'washing_method': clothing.washing_method,
        'status': clothing.status,
        'created_at': clothing.created_at.isoformat()
    }), 201

# 获取所有服装
@app.route('/api/clothes', methods=['GET'])
@token_required
def get_clothes():
    user = request.user
    clothes = Clothing.query.filter_by(user_id=user.id).all()
    
    # 转换为JSON格式
    result = []
    for item in clothes:
        result.append({
            'id': item.id,
            'name': item.name,
            'image_url': item.image_url,
            'category': item.category,
            'purchase_date': item.purchase_date.isoformat() if item.purchase_date else None,
            'price': item.price,
            'wear_count': item.wear_count,
            'washing_method': item.washing_method,
            'status': item.status,
            'created_at': item.created_at.isoformat()
        })
    
    return jsonify(result), 200

# 获取单个服装
@app.route('/api/clothes/<int:clothing_id>', methods=['GET'])
@token_required
def get_clothing(clothing_id):
    user = request.user
    clothing = Clothing.query.filter_by(id=clothing_id, user_id=user.id).first()
    
    if not clothing:
        return jsonify({'message': '服装不存在'}), 404
    
    return jsonify({
        'id': clothing.id,
        'name': clothing.name,
        'image_url': clothing.image_url,
        'category': clothing.category,
        'purchase_date': clothing.purchase_date.isoformat() if clothing.purchase_date else None,
        'price': clothing.price,
        'wear_count': clothing.wear_count,
        'washing_method': clothing.washing_method,
        'status': clothing.status,
        'created_at': clothing.created_at.isoformat(),
        'updated_at': clothing.updated_at.isoformat()
    }), 200

# 更新服装
@app.route('/api/clothes/<int:clothing_id>', methods=['PUT'])
@token_required
def update_clothing(clothing_id):
    user = request.user
    clothing = Clothing.query.filter_by(id=clothing_id, user_id=user.id).first()
    
    if not clothing:
        return jsonify({'message': '服装不存在'}), 404
    
    data = request.get_json()
    
    # 更新字段
    if 'name' in data:
        clothing.name = data['name']
    if 'image_url' in data:
        clothing.image_url = data['image_url']
    if 'category' in data:
        clothing.category = data['category']
    if 'purchase_date' in data:
        try:
            clothing.purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': '购买日期格式错误，应为YYYY-MM-DD'}), 400
    if 'price' in data:
        clothing.price = data['price']
    if 'wear_count' in data:
        clothing.wear_count = data['wear_count']
    if 'washing_method' in data:
        clothing.washing_method = data['washing_method']
    if 'status' in data:
        clothing.status = data['status']
    
    # 保存更改
    db.session.commit()
    
    return jsonify({'message': '服装信息更新成功'}), 200

# 删除服装
@app.route('/api/clothes/<int:clothing_id>', methods=['DELETE'])
@token_required
def delete_clothing(clothing_id):
    user = request.user
    clothing = Clothing.query.filter_by(id=clothing_id, user_id=user.id).first()
    
    if not clothing:
        return jsonify({'message': '服装不存在'}), 404
    
    # 删除服装
    db.session.delete(clothing)
    db.session.commit()
    
    return jsonify({'message': '服装已删除'}), 200


# Get the absolute path of the directory where the script is located
basedir = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
@token_required
def upload_file():
    """Upload a file and return its URL"""
    user = request.user
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        # Sanitize filename and make it unique
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + '_' + filename
        
        # Save the file
        file.save(os.path.join(UPLOAD_FOLDER, unique_filename))
        
        # 确定使用的协议（HTTP或HTTPS）
        # 首先检查X-Forwarded-Proto头，这是代理服务器传递的原始协议
        protocol = request.headers.get('X-Forwarded-Proto', 'http')
        
        # 构建URL时使用正确的协议
        host_with_protocol = protocol + '://' + request.host
        file_url = host_with_protocol + '/uploads/' + unique_filename
        
        return jsonify({'url': file_url})
    else:
        return jsonify({'error': 'File type not allowed'}), 400

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# 增加穿着次数
@app.route('/api/clothes/<int:clothing_id>/wear', methods=['POST'])
@token_required
def wear_clothing(clothing_id):
    user = request.user
    clothing = Clothing.query.filter_by(id=clothing_id, user_id=user.id).first()
    
    if not clothing:
        return jsonify({'message': '服装不存在'}), 404
    
    # 增加穿着次数
    clothing.wear_count += 1
    db.session.commit()
    
    return jsonify({'message': '穿着次数已更新', 'wear_count': clothing.wear_count}), 200

# 主函数
def main():
    app.run(debug=True)

# 运行应用
if __name__ == "__main__":
    main()

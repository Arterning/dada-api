import jwt
from flask import request, jsonify
from datetime import datetime, timedelta, timezone
from models import User
import os

# 从环境变量获取JWT密钥，如果没有则使用默认值
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-secret-key')
JWT_EXPIRATION = 24 * 60 * 60  # 24小时

# 生成JWT令牌
def generate_token(user_id):
    token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=7)  # Token expires in 7 days
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
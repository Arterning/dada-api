from flask import Blueprint, request, jsonify
from models import db, DailyOutfit, Clothing
from auth import token_required
from datetime import datetime

daily_outfit_bp = Blueprint('daily_outfit', __name__)

# 添加当天穿搭
@daily_outfit_bp.route('/api/daily-outfits', methods=['POST'])
@token_required
def add_daily_outfit():
    user = request.user
    data = request.get_json()
    
    # 验证必要字段
    if not data or not 'date' in data:
        return jsonify({'message': '缺少日期'}), 400
    
    # 解析日期
    try:
        outfit_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': '日期格式错误，应为YYYY-MM-DD'}), 400
    
    # 检查是否已存在当天的穿搭记录
    existing_outfit = DailyOutfit.query.filter_by(
        user_id=user.id, 
        date=outfit_date
    ).first()
    
    if existing_outfit:
        return jsonify({'message': '当天的穿搭记录已存在'}), 400
    
    # 创建新的当天穿搭记录
    daily_outfit = DailyOutfit(
        user_id=user.id,
        date=outfit_date
    )
    
    # 设置可选字段
    if 'todays_clothes' in data:
        daily_outfit.todays_clothes = data['todays_clothes']
    if 'temperature' in data:
        daily_outfit.temperature = data['temperature']
    if 'weather' in data:
        daily_outfit.weather = data['weather']
    
    # 添加关联的服装
    if 'clothing_ids' in data and data['clothing_ids']:
        for clothing_id in data['clothing_ids']:
            clothing = Clothing.query.filter_by(id=clothing_id, user_id=user.id).first()
            if clothing:
                daily_outfit.clothes.append(clothing)
    
    # 保存到数据库
    db.session.add(daily_outfit)
    db.session.commit()
    
    # 返回创建的记录
    return jsonify({
        'id': daily_outfit.id,
        'date': daily_outfit.date.isoformat(),
        'todays_clothes': daily_outfit.todays_clothes,
        'temperature': daily_outfit.temperature,
        'weather': daily_outfit.weather,
        'clothing_ids': [clothing.id for clothing in daily_outfit.clothes],
        'created_at': daily_outfit.created_at.isoformat(),
        'updated_at': daily_outfit.updated_at.isoformat()
    }), 201

# 获取当天穿搭记录
@daily_outfit_bp.route('/api/daily-outfits', methods=['GET'])
@token_required
def get_daily_outfits():
    user = request.user
    
    # 获取查询参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 构建查询
    query = DailyOutfit.query.filter_by(user_id=user.id)
    
    # 添加日期范围过滤
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(DailyOutfit.date >= start)
        except ValueError:
            return jsonify({'message': '开始日期格式错误，应为YYYY-MM-DD'}), 400
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(DailyOutfit.date <= end)
        except ValueError:
            return jsonify({'message': '结束日期格式错误，应为YYYY-MM-DD'}), 400
    
    # 获取结果
    outfits = query.order_by(DailyOutfit.date.desc()).all()
    
    # 转换为JSON格式
    result = []
    for outfit in outfits:
        result.append({
            'id': outfit.id,
            'date': outfit.date.isoformat(),
            'todays_clothes': outfit.todays_clothes,
            'temperature': outfit.temperature,
            'weather': outfit.weather,
            'clothing_ids': [clothing.id for clothing in outfit.clothes],
            'created_at': outfit.created_at.isoformat(),
            'updated_at': outfit.updated_at.isoformat()
        })
    
    return jsonify(result), 200

# 获取单个当天穿搭记录
@daily_outfit_bp.route('/api/daily-outfits/<int:outfit_id>', methods=['GET'])
@token_required
def get_daily_outfit(outfit_id):
    user = request.user
    outfit = DailyOutfit.query.filter_by(id=outfit_id, user_id=user.id).first()
    
    if not outfit:
        return jsonify({'message': '穿搭记录不存在'}), 404
    
    return jsonify({
        'id': outfit.id,
        'date': outfit.date.isoformat(),
        'todays_clothes': outfit.todays_clothes,
        'temperature': outfit.temperature,
        'weather': outfit.weather,
        'clothes': [{
            'id': clothing.id,
            'name': clothing.name,
            'image_url': clothing.image_url,
            'category': clothing.category
        } for clothing in outfit.clothes],
        'created_at': outfit.created_at.isoformat(),
        'updated_at': outfit.updated_at.isoformat()
    }), 200

# 更新当天穿搭记录
@daily_outfit_bp.route('/api/daily-outfits/<int:outfit_id>', methods=['PUT'])
@token_required
def update_daily_outfit(outfit_id):
    user = request.user
    outfit = DailyOutfit.query.filter_by(id=outfit_id, user_id=user.id).first()
    
    if not outfit:
        return jsonify({'message': '穿搭记录不存在'}), 404
    
    data = request.get_json()
    
    # 更新字段
    if 'date' in data:
        try:
            new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            # 检查新日期是否已存在
            existing = DailyOutfit.query.filter_by(
                user_id=user.id, 
                date=new_date
            ).filter(DailyOutfit.id != outfit_id).first()
            if existing:
                return jsonify({'message': '该日期的穿搭记录已存在'}), 400
            outfit.date = new_date
        except ValueError:
            return jsonify({'message': '日期格式错误，应为YYYY-MM-DD'}), 400
    
    if 'todays_clothes' in data:
        outfit.todays_clothes = data['todays_clothes']
    if 'temperature' in data:
        outfit.temperature = data['temperature']
    if 'weather' in data:
        outfit.weather = data['weather']
    
    # 更新关联的服装
    if 'clothing_ids' in data:
        outfit.clothes = []
        if data['clothing_ids']:
            for clothing_id in data['clothing_ids']:
                clothing = Clothing.query.filter_by(id=clothing_id, user_id=user.id).first()
                if clothing:
                    outfit.clothes.append(clothing)
    
    # 保存更改
    db.session.commit()
    
    return jsonify({
        'id': outfit.id,
        'date': outfit.date.isoformat(),
        'todays_clothes': outfit.todays_clothes,
        'temperature': outfit.temperature,
        'weather': outfit.weather,
        'clothing_ids': [clothing.id for clothing in outfit.clothes],
        'updated_at': outfit.updated_at.isoformat()
    }), 200
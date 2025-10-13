from flask import Blueprint, request, jsonify
from models import db, Outfit, OutfitClothing, Clothing
from auth import token_required
from datetime import datetime

# 创建Blueprint用于组织Outfit相关的API路由
outfit_bp = Blueprint('outfit', __name__)

@outfit_bp.route('/api/outfits', methods=['POST'])
@token_required
def add_outfit():
    """添加新穿搭"""
    user = request.user
    data = request.get_json()
    
    # 验证必要字段
    if not data or not 'name' in data:
        return jsonify({'message': '缺少穿搭名称'}), 400
    
    # 创建新穿搭
    outfit = Outfit(
        name=data['name'],
        user_id=user.id
    )
    
    # 设置可选字段
    if 'image_url' in data:
        outfit.image_url = data['image_url']
    
    # 添加到数据库
    db.session.add(outfit)
    db.session.flush()  # 获取outfit.id但不提交事务
    
    # 处理穿搭中的服装
    if 'clothes' in data and isinstance(data['clothes'], list):
        for clothing_item in data['clothes']:
            clothing_id = clothing_item.get('clothing_id')
            if not clothing_id:
                continue
            
            # 检查服装是否属于当前用户
            clothing = Clothing.query.filter_by(id=clothing_id, user_id=user.id).first()
            if not clothing:
                continue
            
            # 创建穿搭-服装关联
            outfit_clothing = OutfitClothing(
                outfit_id=outfit.id,
                clothing_id=clothing_id,
                clothing_image=clothing.image_url,
                x=clothing_item.get('x', 0.0),
                y=clothing_item.get('y', 0.0),
                angle=clothing_item.get('angle', 0.0),
                scale=clothing_item.get('scale', 1.0)
            )
            db.session.add(outfit_clothing)
    
    # 提交事务
    db.session.commit()
    
    # 返回创建的穿搭信息
    return jsonify({
        'id': outfit.id,
        'name': outfit.name,
        'image_url': outfit.image_url,
        'clothes': get_outfit_clothes(outfit.id)
    }), 201

@outfit_bp.route('/api/outfits', methods=['GET'])
@token_required
def get_outfits():
    """获取当前用户的所有穿搭"""
    user = request.user
    outfits = Outfit.query.filter_by(user_id=user.id).all()
    
    # 转换为JSON格式
    result = []
    for outfit in outfits:
        result.append({
            'id': outfit.id,
            'name': outfit.name,
            'image_url': outfit.image_url,
            'clothes': get_outfit_clothes(outfit.id)
        })
    
    return jsonify(result), 200

@outfit_bp.route('/api/outfits/<int:outfit_id>', methods=['GET'])
@token_required
def get_outfit(outfit_id):
    """获取单个穿搭详情"""
    user = request.user
    outfit = Outfit.query.filter_by(id=outfit_id, user_id=user.id).first()
    
    if not outfit:
        return jsonify({'message': '穿搭不存在'}), 404
    
    return jsonify({
        'id': outfit.id,
        'name': outfit.name,
        'image_url': outfit.image_url,
        'clothes': get_outfit_clothes(outfit.id)
    }), 200

@outfit_bp.route('/api/outfits/<int:outfit_id>', methods=['PUT'])
@token_required
def update_outfit(outfit_id):
    """更新穿搭信息"""
    user = request.user
    outfit = Outfit.query.filter_by(id=outfit_id, user_id=user.id).first()
    
    if not outfit:
        return jsonify({'message': '穿搭不存在'}), 404
    
    data = request.get_json()
    
    # 更新字段
    if 'name' in data:
        outfit.name = data['name']
    if 'image_url' in data:
        outfit.image_url = data['image_url']
    
    # 处理穿搭中的服装（先删除旧的关联，再添加新的关联）
    if 'clothes' in data and isinstance(data['clothes'], list):
        # 删除旧的关联
        OutfitClothing.query.filter_by(outfit_id=outfit_id).delete()
        
        # 添加新的关联
        for clothing_item in data['clothes']:
            clothing_id = clothing_item.get('clothing_id')
            if not clothing_id:
                continue
            
            # 检查服装是否属于当前用户
            clothing = Clothing.query.filter_by(id=clothing_id, user_id=user.id).first()
            if not clothing:
                continue
            
            # 创建穿搭-服装关联
            outfit_clothing = OutfitClothing(
                outfit_id=outfit.id,
                clothing_id=clothing_id,
                clothing_image=clothing.image_url,
                x=clothing_item.get('x', 0.0),
                y=clothing_item.get('y', 0.0),
                angle=clothing_item.get('angle', 0.0),
                scale=clothing_item.get('scale', 1.0)
            )
            db.session.add(outfit_clothing)
    
    # 保存更改
    db.session.commit()
    
    return jsonify({
        'message': '穿搭信息更新成功',
        'id': outfit.id,
        'name': outfit.name,
        'image_url': outfit.image_url,
        'clothes': get_outfit_clothes(outfit.id)
    }), 200

@outfit_bp.route('/api/outfits/<int:outfit_id>', methods=['DELETE'])
@token_required
def delete_outfit(outfit_id):
    """删除穿搭"""
    user = request.user
    outfit = Outfit.query.filter_by(id=outfit_id, user_id=user.id).first()
    
    if not outfit:
        return jsonify({'message': '穿搭不存在'}), 404
    
    # 删除相关的穿搭-服装关联
    OutfitClothing.query.filter_by(outfit_id=outfit_id).delete()
    
    # 删除穿搭
    db.session.delete(outfit)
    db.session.commit()
    
    return jsonify({'message': '穿搭已删除'}), 200

@outfit_bp.route('/api/outfits/<int:outfit_id>/clothes', methods=['POST'])
@token_required
def add_clothing_to_outfit(outfit_id):
    """向穿搭中添加服装"""
    user = request.user
    outfit = Outfit.query.filter_by(id=outfit_id, user_id=user.id).first()
    
    if not outfit:
        return jsonify({'message': '穿搭不存在'}), 404
    
    data = request.get_json()
    clothing_id = data.get('clothing_id')
    
    if not clothing_id:
        return jsonify({'message': '缺少服装ID'}), 400
    
    # 检查服装是否属于当前用户
    clothing = Clothing.query.filter_by(id=clothing_id, user_id=user.id).first()
    if not clothing:
        return jsonify({'message': '服装不存在或不属于当前用户'}), 404
    
    # 检查该服装是否已经在穿搭中
    existing_association = OutfitClothing.query.filter_by(
        outfit_id=outfit_id,
        clothing_id=clothing_id
    ).first()
    
    if existing_association:
        return jsonify({'message': '该服装已经在穿搭中'}), 400
    
    # 创建穿搭-服装关联
    outfit_clothing = OutfitClothing(
        outfit_id=outfit.id,
        clothing_id=clothing_id,
        clothing_image=clothing.image_url,
        x=data.get('x', 0.0),
        y=data.get('y', 0.0),
        angle=data.get('angle', 0.0),
        scale=data.get('scale', 1.0)
    )
    
    db.session.add(outfit_clothing)
    db.session.commit()
    
    return jsonify({
        'message': '服装已添加到穿搭',
        'clothes': get_outfit_clothes(outfit_id)
    }), 200

@outfit_bp.route('/api/outfits/<int:outfit_id>/clothes/<int:clothing_id>', methods=['DELETE'])
@token_required
def remove_clothing_from_outfit(outfit_id, clothing_id):
    """从穿搭中移除服装"""
    user = request.user
    outfit = Outfit.query.filter_by(id=outfit_id, user_id=user.id).first()
    
    if not outfit:
        return jsonify({'message': '穿搭不存在'}), 404
    
    # 检查该服装是否在穿搭中
    association = OutfitClothing.query.filter_by(
        outfit_id=outfit_id,
        clothing_id=clothing_id
    ).first()
    
    if not association:
        return jsonify({'message': '该服装不在穿搭中'}), 404
    
    # 删除关联
    db.session.delete(association)
    db.session.commit()
    
    return jsonify({
        'message': '服装已从穿搭中移除',
        'clothes': get_outfit_clothes(outfit_id)
    }), 200

# 辅助函数：获取穿搭中的服装列表
def get_outfit_clothes(outfit_id):
    """获取指定穿搭中的所有服装及其在穿搭中的属性"""
    associations = OutfitClothing.query.filter_by(outfit_id=outfit_id).all()
    clothes = []
    
    for assoc in associations:
        clothing = Clothing.query.get(assoc.clothing_id)
        if clothing:
            clothes.append({
                'clothing_id': clothing.id,
                'name': clothing.name,
                'image_url': assoc.clothing_image or clothing.image_url,
                'category': clothing.category,
                'x': assoc.x,
                'y': assoc.y,
                'angle': assoc.angle,
                'scale': assoc.scale
            })
    
    return clothes
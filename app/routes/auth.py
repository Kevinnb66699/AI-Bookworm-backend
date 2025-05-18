from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..models import User
from .. import db
import jwt
from datetime import datetime, timedelta
import os

bp = Blueprint('auth', __name__)

@bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    new_user = User(username=username, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    # 生成邮箱验证令牌
    verification_token = create_access_token(
        identity=new_user.id,
        additional_claims={'type': 'email_verification'},
        expires_delta=timedelta(hours=24)
    )
    
    # TODO: 发送验证邮件
    
    return jsonify({'message': 'User registered successfully'}), 201

@bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 检查请求数据
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': '邮箱和密码是必需的'}), 400
        
    # 打印登录请求数据（不包含密码）
    print('Login request data:', {'email': data['email']})
    
    # 查找用户
    user = User.query.filter_by(email=data['email']).first()
    print('Found user:', bool(user))
    
    if user and user.check_password(data['password']):
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # 生成访问令牌，确保user.id转换为字符串
        access_token = create_access_token(identity=str(user.id))
        print('Login successful for user:', user.username)
        
        return jsonify({
            'token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 200
    
    return jsonify({'error': '邮箱或密码错误'}), 401

@bp.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    # 在实际应用中，您可能想要将令牌加入黑名单
    return jsonify({'message': 'Successfully logged out'}), 200

@bp.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user:
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email
        }), 200
    return jsonify({'error': 'User not found'}), 404

@bp.route('/update_profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    data = request.get_json()
    
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already in use'}), 400
        user.email = data['email']
        
    db.session.commit()
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email
    }), 200

@bp.route('/change_password', methods=['POST'])
@jwt_required()
def change_password():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Missing required fields'}), 400
        
    if not user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect'}), 401
        
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200

@bp.route('/forgot_password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
        
    user = User.query.filter_by(email=email).first()
    
    if user:
        # 生成密码重置令牌
        reset_token = create_access_token(
            identity=user.id,
            additional_claims={'type': 'password_reset'},
            expires_delta=timedelta(hours=1)
        )
        
        # TODO: 发送重置密码邮件
        
        return jsonify({'message': 'Password reset instructions sent to email'}), 200
        
    return jsonify({'message': 'If the email exists, reset instructions will be sent'}), 200

@bp.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not token or not new_password:
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=['HS256'])
        if payload.get('type') != 'password_reset':
            return jsonify({'error': 'Invalid token type'}), 400
            
        user = User.query.get(payload['sub'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'message': 'Password reset successfully'}), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401 
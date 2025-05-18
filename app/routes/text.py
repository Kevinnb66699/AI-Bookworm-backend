from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Text, Course
from .. import db
from datetime import datetime

bp = Blueprint('text', __name__)

@bp.route('/api/courses/<int:course_id>/texts', methods=['GET'])
@jwt_required()
def get_texts(course_id):
    try:
        current_user_id = int(get_jwt_identity())
        
        # 验证课程是否属于当前用户
        course = Course.query.get_or_404(course_id)
        if course.creator_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        texts = Text.query.filter_by(course_id=course_id).all()
        return jsonify([text.to_dict() for text in texts]), 200
    except Exception as e:
        print(f"Error in get_texts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/courses/<int:course_id>/texts', methods=['POST'])
@jwt_required()
def create_text(course_id):
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({'error': '课文内容是必需的'}), 400
            
        # 验证课程是否属于当前用户
        course = Course.query.get_or_404(course_id)
        if course.creator_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        text = Text(
            title=data.get('title', ''),
            content=data['content'],
            translation=data.get('translation', ''),
            course_id=course_id
        )
        
        db.session.add(text)
        db.session.commit()
        
        return jsonify(text.to_dict()), 201
    except Exception as e:
        print(f"Error in create_text: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/texts/<int:text_id>', methods=['PUT'])
@jwt_required()
def update_text(text_id):
    try:
        current_user_id = int(get_jwt_identity())
        text = Text.query.get_or_404(text_id)
        
        # 验证课文所属课程是否属于当前用户
        if text.course.creator_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        data = request.get_json()
        
        if 'title' in data:
            text.title = data['title']
        if 'content' in data:
            text.content = data['content']
        if 'translation' in data:
            text.translation = data['translation']
            
        db.session.commit()
        return jsonify(text.to_dict()), 200
    except Exception as e:
        print(f"Error in update_text: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/texts/<int:text_id>', methods=['DELETE'])
@jwt_required()
def delete_text(text_id):
    try:
        current_user_id = int(get_jwt_identity())
        text = Text.query.get_or_404(text_id)
        
        # 验证课文所属课程是否属于当前用户
        if text.course.creator_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        db.session.delete(text)
        db.session.commit()
        return '', 204
    except Exception as e:
        print(f"Error in delete_text: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 
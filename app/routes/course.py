from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Course, Word, Text
from .. import db
from datetime import datetime

bp = Blueprint('course', __name__)

@bp.route('/api/courses', methods=['GET'])
@jwt_required()
def get_courses():
    try:
        # 获取用户ID并转换为整数
        current_user_id = int(get_jwt_identity())
        courses = Course.query.filter_by(creator_id=current_user_id).all()
        return jsonify([course.to_dict() for course in courses]), 200
    except Exception as e:
        print(f"Error in get_courses: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/courses/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course(course_id):
    try:
        current_user_id = int(get_jwt_identity())
        course = Course.query.get_or_404(course_id)
        
        # 验证课程是否属于当前用户
        if course.creator_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        return jsonify(course.to_dict()), 200
    except Exception as e:
        print(f"Error in get_course: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/courses', methods=['POST'])
@jwt_required()
def create_course():
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': '课程名称是必需的'}), 400
            
        course = Course(
            name=data['name'],
            description=data.get('description', ''),
            creator_id=current_user_id
        )
        
        db.session.add(course)
        db.session.commit()
        
        return jsonify(course.to_dict()), 201
    except Exception as e:
        print(f"Error in create_course: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/courses/<int:course_id>', methods=['PUT'])
@jwt_required()
def update_course(course_id):
    try:
        current_user_id = int(get_jwt_identity())
        course = Course.query.get_or_404(course_id)
        
        # 验证课程是否属于当前用户
        if course.creator_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if 'name' in data:
            course.name = data['name']
        if 'description' in data:
            course.description = data['description']
        
        db.session.commit()
        return jsonify(course.to_dict()), 200
    except Exception as e:
        print(f"Error in update_course: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/courses/<int:course_id>', methods=['DELETE'])
@jwt_required()
def delete_course(course_id):
    try:
        current_user_id = int(get_jwt_identity())
        course = Course.query.get_or_404(course_id)
        
        # 验证课程是否属于当前用户
        if course.creator_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        db.session.delete(course)
        db.session.commit()
        return '', 204
    except Exception as e:
        print(f"Error in delete_course: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:course_id>/stats', methods=['GET'])
@jwt_required()
def get_course_stats(course_id):
    """获取课程的学习统计信息"""
    current_user_id = get_jwt_identity()
    course = Course.query.get_or_404(course_id)
    
    # 验证课程是否属于当前用户
    if course.creator_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # 获取单词统计
    total_words = Word.query.filter_by(course_id=course_id).count()
    mastered_words = Word.query.filter_by(
        course_id=course_id,
        repetitions__gte=5,
        ease_factor__gte=2.5
    ).count()
    
    # 获取课文统计
    total_texts = Text.query.filter_by(course_id=course_id).count()
    mastered_texts = Text.query.filter_by(
        course_id=course_id,
        repetitions__gte=3,
        ease_factor__gte=2.5
    ).count()
    
    # 获取最近7天的学习记录
    recent_reviews = Review.query.join(Word).filter(
        Word.course_id == course_id,
        Review.user_id == current_user_id,
        Review.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    return jsonify({
        'total_words': total_words,
        'mastered_words': mastered_words,
        'total_texts': total_texts,
        'mastered_texts': mastered_texts,
        'recent_reviews': recent_reviews,
        'mastery_rate': {
            'words': round(mastered_words / total_words * 100, 1) if total_words > 0 else 0,
            'texts': round(mastered_texts / total_texts * 100, 1) if total_texts > 0 else 0
        }
    }), 200 
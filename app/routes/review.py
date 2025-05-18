from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.review_plan import ReviewPlan
from app.models.word_practice import WordPractice
from app import db
from datetime import datetime

bp = Blueprint('review', __name__, url_prefix='/api/review')

@bp.route('/plans', methods=['GET'])
@jwt_required()
def get_review_plans():
    user_id = get_jwt_identity()
    plans = ReviewPlan.query.filter_by(user_id=user_id).all()
    return jsonify([plan.to_dict() for plan in plans])

@bp.route('/stats', methods=['GET'])
@jwt_required()
def get_review_stats():
    user_id = get_jwt_identity()
    total = ReviewPlan.query.filter_by(user_id=user_id).count()
    completed = ReviewPlan.query.filter_by(user_id=user_id, status='completed').count()
    pending = total - completed
    return jsonify({
        'total': total,
        'completed': completed,
        'pending': pending
    })

@bp.route('/<int:plan_id>/start', methods=['POST'])
@jwt_required()
def start_review(plan_id):
    user_id = get_jwt_identity()
    plan = ReviewPlan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
    return jsonify(plan.to_dict())

@bp.route('/<int:plan_id>/complete', methods=['POST'])
@jwt_required()
def complete_review(plan_id):
    user_id = get_jwt_identity()
    plan = ReviewPlan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
    
    data = request.get_json()
    is_correct = data.get('isCorrect', False)
    
    # 更新复习计划状态
    plan.status = 'completed'
    plan.last_review_time = datetime.utcnow()
    
    # 更新单词练习记录
    practice = WordPractice(
        user_id=user_id,
        word_id=plan.word_id,
        is_correct=is_correct,
        review_time=datetime.utcnow()
    )
    db.session.add(practice)
    db.session.commit()
    
    return jsonify({'message': '复习完成'}) 
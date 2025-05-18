from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Reminder
from app import db
from datetime import datetime

bp = Blueprint('reminder', __name__, url_prefix='/api/reminders')

@bp.route('/course/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course_reminders(course_id):
    try:
        user_id = get_jwt_identity()
        reminders = Reminder.query.filter_by(
            user_id=user_id,
            course_id=course_id
        ).all()
        return jsonify([reminder.to_dict() for reminder in reminders]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/', methods=['POST'])
@jwt_required()
def create_reminder():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        reminder = Reminder(
            user_id=user_id,
            course_id=data['course_id'],
            type=data['type'],
            item_id=data['item_id'],
            next_review_date=datetime.strptime(data['next_review_date'], '%Y-%m-%d').date()
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        return jsonify(reminder.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:reminder_id>', methods=['PUT'])
@jwt_required()
def update_reminder(reminder_id):
    try:
        user_id = get_jwt_identity()
        reminder = Reminder.query.filter_by(
            id=reminder_id,
            user_id=user_id
        ).first_or_404()
        
        data = request.get_json()
        if 'next_review_date' in data:
            reminder.next_review_date = datetime.strptime(data['next_review_date'], '%Y-%m-%d').date()
        if 'review_count' in data:
            reminder.review_count = data['review_count']
            
        db.session.commit()
        return jsonify(reminder.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:reminder_id>', methods=['DELETE'])
@jwt_required()
def delete_reminder(reminder_id):
    try:
        user_id = get_jwt_identity()
        reminder = Reminder.query.filter_by(
            id=reminder_id,
            user_id=user_id
        ).first_or_404()
        
        db.session.delete(reminder)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 
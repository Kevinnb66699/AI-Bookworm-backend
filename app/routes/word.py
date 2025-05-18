from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Word, Course, Review, WordPractice, PracticeProgress
from .. import db
from datetime import datetime, timedelta
import random
from ..utils.auth import login_required
from ..models.review_plan import ReviewPlan

bp = Blueprint('word', __name__)

@bp.route('/api/words', methods=['GET'])
@jwt_required()
def get_words():
    try:
        current_user_id = int(get_jwt_identity())
        course_id = request.args.get('course_id', type=int)
        
        if not course_id:
            return jsonify({'error': '课程ID是必需的'}), 400
            
        # 验证课程是否属于当前用户
        course = Course.query.get_or_404(course_id)
        if course.creator_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        words = Word.query.filter_by(course_id=course_id).all()
        return jsonify([word.to_dict() for word in words]), 200
    except Exception as e:
        print(f"Error in get_words: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/words', methods=['POST'])
@jwt_required()
def create_word():
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    
    required_fields = ['word', 'meanings', 'course_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必填字段：{field}'}), 400
    
    course = Course.query.get(data['course_id'])
    if not course:
        return jsonify({'error': '课程不存在'}), 404
    
    if course.creator_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # 确保meanings是一个列表
        meanings = data['meanings']
        if not isinstance(meanings, list):
            return jsonify({'error': 'meanings必须是列表类型'}), 400
        
        # 过滤掉空的释义
        meanings = [m.strip() for m in meanings if m.strip()]
        if not meanings:
            return jsonify({'error': '至少需要一个有效的释义'}), 400
        
        word = Word(
            word=data['word'],
            meanings=meanings,
            pronunciation=data.get('pronunciation'),
            example=data.get('example'),
            course_id=data['course_id']
        )
        
        db.session.add(word)
        db.session.commit()
        return jsonify(word.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"创建单词失败: {str(e)}")  # 添加错误日志
        return jsonify({'error': f'创建单词失败: {str(e)}'}), 500

@bp.route('/api/words/<int:id>', methods=['PUT'])
@jwt_required()
def update_word(id):
    current_user_id = int(get_jwt_identity())
    word = Word.query.get_or_404(id)
    
    if word.course.creator_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    
    try:
        if 'word' in data:
            word.word = data['word']
        if 'meanings' in data:
            word.meanings = data['meanings']
        if 'pronunciation' in data:
            word.pronunciation = data['pronunciation']
        if 'example' in data:
            word.example = data['example']
        
        db.session.commit()
        return jsonify(word.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '更新单词失败'}), 500

@bp.route('/api/words/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_word(id):
    current_user_id = int(get_jwt_identity())
    word = Word.query.get_or_404(id)
    
    if word.course.creator_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        db.session.delete(word)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除单词失败'}), 500

@bp.route('/review', methods=['GET'])
@jwt_required()
def get_review_words():
    """获取需要复习的单词"""
    current_user_id = get_jwt_identity()
    course_id = request.args.get('course_id', type=int)
    
    query = Word.query.filter(
        Word.next_review <= datetime.utcnow()
    )
    
    if course_id:
        query = query.filter_by(course_id=course_id)
    
    words = query.all()
    return jsonify([word.to_dict() for word in words]), 200

@bp.route('/<int:word_id>/review', methods=['POST'])
@jwt_required()
def review_word(word_id):
    """提交单词复习结果"""
    current_user_id = get_jwt_identity()
    word = Word.query.get_or_404(word_id)
    data = request.get_json()
    
    quality = data.get('quality')
    if quality is None or not 0 <= quality <= 5:
        return jsonify({'error': 'Quality must be between 0 and 5'}), 400
    
    # 更新SM-2算法参数
    word.update_sm2(quality)
    
    # 记录复习历史
    review = Review(
        user_id=current_user_id,
        word_id=word_id,
        quality=quality
    )
    db.session.add(review)
    db.session.commit()
    
    return jsonify(word.to_dict()), 200

@bp.route('/practice', methods=['GET'])
@jwt_required()
def get_practice_words():
    """获取用于练习的单词"""
    current_user_id = get_jwt_identity()
    course_id = request.args.get('course_id', type=int)
    
    query = Word.query
    
    if course_id:
        query = query.filter_by(course_id=course_id)
    
    # 随机获取10个单词用于练习
    words = query.order_by(db.func.random()).limit(10).all()
    return jsonify([word.to_dict() for word in words]), 200

@bp.route('/api/courses/<int:course_id>/words', methods=['GET'])
@jwt_required()
def get_words_in_course(course_id):
    current_user_id = int(get_jwt_identity())
    course = Course.query.get_or_404(course_id)
    if course.creator_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    words = Word.query.filter_by(course_id=course_id).all()
    return jsonify([word.to_dict() for word in words]), 200

@bp.route('/api/courses/<int:course_id>/words/practice', methods=['GET'])
@jwt_required()
def get_word_practice(course_id):
    current_user_id = int(get_jwt_identity())
    course = Course.query.get_or_404(course_id)
    if course.creator_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # 获取所有单词
    words = Word.query.filter_by(course_id=course_id).all()
    if not words:
        return jsonify({'error': '该课程没有单词可供练习'}), 404
    
    # 获取当前用户已练习的单词ID列表
    practiced_word_ids = [wp.word_id for wp in WordPractice.query.filter_by(user_id=current_user_id).all()]
    
    # 过滤出未练习的单词
    available_words = [word for word in words if word.id not in practiced_word_ids]
    
    if not available_words:
        # 如果所有单词都已练习过，返回统计信息
        stats = Word.get_practice_stats(course_id, current_user_id)
        return jsonify({
            'status': 'completed',
            'message': '所有单词都已练习完成',
            'stats': stats
        }), 200
    
    # 随机选择一个未练习的单词
    word = random.choice(available_words)
    return jsonify(word.to_dict())

def calculate_next_review_time(consecutive_correct: int) -> datetime:
    """根据连续正确次数计算下次复习时间"""
    intervals = {
        0: timedelta(hours=4),    # 4小时后
        1: timedelta(days=1),     # 1天后
        2: timedelta(days=2),     # 2天后
        3: timedelta(days=4),     # 4天后
        4: timedelta(days=7),     # 1周后
        5: timedelta(days=15),    # 2周后
    }
    interval = intervals.get(consecutive_correct, timedelta(days=30))  # 默认30天
    return datetime.utcnow() + interval

@bp.route('/api/words/<int:word_id>/practice', methods=['POST'])
@jwt_required()
def submit_word_practice(word_id):
    current_user_id = int(get_jwt_identity())
    word = Word.query.get_or_404(word_id)
    
    data = request.get_json()
    if not data or 'answer' not in data:
        return jsonify({'error': '缺少答案'}), 400
    
    answer = data['answer'].strip().lower()
    is_english_to_chinese = data.get('is_english_to_chinese', True)
    
    if is_english_to_chinese:
        meanings_to_check = word.meanings
        correct_answer = word.meanings[0] if word.meanings else ''
    else:
        meanings_to_check = [word.word.lower()]
        correct_answer = word.word
    
    is_correct = any(
        answer == meaning.strip().lower() or
        answer in meaning.strip().lower() or
        meaning.strip().lower() in answer
        for meaning in meanings_to_check
    )
    
    try:
        # 更新练习进度
        progress = PracticeProgress.query.filter_by(
            user_id=current_user_id,
            course_id=word.course_id
        ).first()
        
        if not progress:
            progress = PracticeProgress(
                user_id=current_user_id,
                course_id=word.course_id,
                practiced_words=0,
                correct_count=0,
                accuracy=0
            )
            db.session.add(progress)
        
        progress.practiced_words += 1
        if is_correct:
            progress.correct_count += 1
        progress.accuracy = (progress.correct_count / progress.practiced_words * 100) if progress.practiced_words > 0 else 0
        
        # 更新或创建复习计划
        review_plan = ReviewPlan.query.filter_by(
            user_id=current_user_id,
            word_id=word_id,
            course_id=word.course_id
        ).first()
        
        if not review_plan:
            review_plan = ReviewPlan(
                user_id=current_user_id,
                word_id=word_id,
                course_id=word.course_id,
                next_review_time=datetime.utcnow()
            )
            db.session.add(review_plan)
        
        review_plan.last_practice_time = datetime.utcnow()
        review_plan.review_count += 1
        
        if is_correct:
            review_plan.consecutive_correct += 1
            if review_plan.consecutive_correct >= 6:  # 连续正确6次认为已掌握
                review_plan.is_mastered = True
        else:
            review_plan.consecutive_correct = 0
        
        review_plan.next_review_time = calculate_next_review_time(review_plan.consecutive_correct)
        
        practice = WordPractice(
            user_id=current_user_id,
            word_id=word_id,
            course_id=word.course_id,
            is_correct=is_correct
        )
        db.session.add(practice)
        
        db.session.commit()
        
        return jsonify({
            'is_correct': is_correct,
            'correct_meaning': correct_answer,
            'progress': progress.to_dict(),
            'review_plan': review_plan.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '保存练习记录失败'}), 500

@bp.route('/api/courses/<int:course_id>/words/practice/result', methods=['GET'])
@jwt_required()
def get_practice_result(course_id):
    current_user_id = int(get_jwt_identity())
    course = Course.query.get_or_404(course_id)
    if course.creator_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # 获取当前用户在该课程中的所有练习记录
    practices = WordPractice.query.join(Word).filter(
        Word.course_id == course_id,
        WordPractice.user_id == current_user_id
    ).all()
    
    if not practices:
        return jsonify({
            'total_words': 0,
            'correct_count': 0,
            'accuracy': 0
        })
    
    correct_count = sum(1 for p in practices if p.is_correct)
    total_words = len(practices)
    accuracy = (correct_count / total_words) * 100
    
    return jsonify({
        'total_words': total_words,
        'correct_count': correct_count,
        'accuracy': accuracy
    })

@bp.route('/api/courses/<int:course_id>/words/practice/progress', methods=['GET'])
@jwt_required()
def get_practice_progress(course_id):
    current_user_id = int(get_jwt_identity())
    
    # 获取课程中的单词总数
    total_words = Word.query.filter_by(course_id=course_id).count()
    
    # 获取当前用户的练习记录
    practiced_words = WordPractice.query.filter_by(
        user_id=current_user_id,
        word_id=Word.id
    ).join(Word).filter(
        Word.course_id == course_id
    ).count()
    
    # 获取当前用户的正确答题数
    correct_count = WordPractice.query.filter_by(
        user_id=current_user_id,
        is_correct=True,
        word_id=Word.id
    ).join(Word).filter(
        Word.course_id == course_id
    ).count()
    
    # 计算正确率
    accuracy = (correct_count / practiced_words * 100) if practiced_words > 0 else 0
    
    return jsonify({
        'total_words': total_words,
        'practiced_words': practiced_words,
        'correct_count': correct_count,
        'accuracy': accuracy
    })

@bp.route('/api/courses/<int:course_id>/words/practice/reset', methods=['POST'])
@jwt_required()
def reset_practice_progress(course_id):
    """重置用户在指定课程中的练习进度"""
    current_user_id = int(get_jwt_identity())
    review_incorrect = request.json.get('review_incorrect', False)

    # 检查用户是否有权限访问该课程
    course = Course.query.get_or_404(course_id)
    if course.creator_id != current_user_id:
        return jsonify({'message': '无权访问此课程'}), 403

    try:
        # 获取用户在该课程中的所有练习记录
        practice_records = WordPractice.query.join(Word).filter(
            Word.course_id == course_id,
            WordPractice.user_id == current_user_id
        ).all()
        
        if review_incorrect:
            # 只重置错误单词的练习记录
            incorrect_word_ids = [record.word_id for record in practice_records if not record.is_correct]
            for record in practice_records:
                if record.word_id in incorrect_word_ids:
                    db.session.delete(record)
        else:
            # 重置所有练习记录
            for record in practice_records:
                db.session.delete(record)

        # 重置进度统计
        progress = PracticeProgress.query.filter_by(
            user_id=current_user_id,
            course_id=course_id
        ).first()
        
        if progress:
            progress.practiced_words = 0
            progress.correct_count = 0
            progress.accuracy = 0
        else:
            # 如果进度记录不存在，创建一个新的
            progress = PracticeProgress(
                user_id=current_user_id,
                course_id=course_id,
                practiced_words=0,
                correct_count=0,
                accuracy=0
            )
            db.session.add(progress)

        db.session.commit()
        return jsonify({'message': '练习进度已重置'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"重置进度失败: {str(e)}")
        return jsonify({'error': '重置进度失败'}), 500

@bp.route('/api/words/review-plans', methods=['GET'])
@jwt_required()
def get_review_plans():
    current_user_id = get_jwt_identity()
    
    try:
        # 获取当前需要复习的单词
        now = datetime.utcnow()
        review_plans = ReviewPlan.query.filter(
            ReviewPlan.user_id == current_user_id,
            ReviewPlan.next_review_time <= now,
            ReviewPlan.is_mastered == False
        ).all()
        
        # 获取每个单词的详细信息
        review_data = []
        for plan in review_plans:
            word = Word.query.get(plan.word_id)
            if word:
                review_data.append({
                    'plan': plan.to_dict(),
                    'word': word.to_dict(),
                    'course': word.course.to_dict() if word.course else None
                })
        
        return jsonify({
            'review_plans': review_data,
            'total_count': len(review_data)
        })
    except Exception as e:
        print(f"获取复习计划失败: {str(e)}")  # 添加错误日志
        return jsonify({'error': '获取复习计划失败'}), 500 
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Course, Word
from .. import db
import csv
import io
from datetime import datetime

bp = Blueprint('import_export', __name__, url_prefix='/import_export')

@bp.route('/export/words', methods=['GET'])
@jwt_required()
def export_words():
    """导出单词为CSV文件"""
    current_user_id = get_jwt_identity()
    course_id = request.args.get('course_id', type=int)
    
    if not course_id:
        return jsonify({'error': 'Course ID is required'}), 400
        
    # 验证课程是否属于当前用户
    course = Course.query.get_or_404(course_id)
    if course.creator_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # 获取课程中的所有单词
    words = Word.query.filter_by(course_id=course_id).all()
    
    # 创建CSV文件
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['word', 'meaning', 'example', 'pronunciation'])
    
    for word in words:
        writer.writerow([
            word.word,
            word.meaning,
            word.example or '',
            word.pronunciation or ''
        ])
    
    # 准备文件下载
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'words_{course.name}_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@bp.route('/import/words', methods=['POST'])
@jwt_required()
def import_words():
    """从CSV文件导入单词"""
    current_user_id = get_jwt_identity()
    course_id = request.form.get('course_id', type=int)
    
    if not course_id:
        return jsonify({'error': 'Course ID is required'}), 400
        
    # 验证课程是否属于当前用户
    course = Course.query.get_or_404(course_id)
    if course.creator_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    try:
        # 读取CSV文件
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported_count = 0
        for row in csv_reader:
            word = Word(
                word=row['word'],
                meaning=row['meaning'],
                example=row.get('example', ''),
                pronunciation=row.get('pronunciation', ''),
                course_id=course_id
            )
            db.session.add(word)
            imported_count += 1
        
        db.session.commit()
        return jsonify({
            'message': f'Successfully imported {imported_count} words',
            'imported_count': imported_count
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error importing words: {str(e)}'}), 400

@bp.route('/template/words', methods=['GET'])
@jwt_required()
def get_word_template():
    """获取单词导入模板"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['word', 'meaning', 'example', 'pronunciation'])
    writer.writerow(['hello', '你好', 'Hello, world!', 'həˈləʊ'])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='word_template.csv'
    ) 
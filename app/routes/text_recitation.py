from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.text_recitation import TextRecitation
from app.services.ocr_service import ocr_service
from app.services.recitation_service import calculate_similarity
from app.services.speech_service import speech_service
from app import db
import tempfile
import os
import logging
import wave
from app.models.practice import Practice

logger = logging.getLogger(__name__)

bp = Blueprint('text_recitation', __name__)

def is_valid_wav_file(file_path):
    """检查文件是否为有效的WAV格式"""
    try:
        with wave.open(file_path, 'rb') as wf:
            # 检查基本参数
            if wf.getnchannels() != 1:
                return False, "音频必须是单声道"
            if wf.getsampwidth() != 2:
                return False, "采样宽度必须是16位"
            if wf.getcomptype() != "NONE":
                return False, "必须是PCM编码"
            return True, None
    except wave.Error as e:
        return False, f"不是有效的WAV文件: {str(e)}"
    except Exception as e:
        return False, f"检查WAV文件时出错: {str(e)}"

@bp.route('/api/text-recitation', methods=['POST'])
@jwt_required()
def create_text_recitation():
    try:
        if 'image' not in request.files:
            return jsonify({'error': '没有上传图片'}), 400
            
        image = request.files['image']
        user_id = get_jwt_identity()
        
        # 识别文字
        content = ocr_service.recognize_text(image)
        
        # 保存到数据库
        text_recitation = TextRecitation(
            user_id=user_id,
            content=content
        )
        db.session.add(text_recitation)
        db.session.commit()
        
        return jsonify(text_recitation.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/text-recitation', methods=['GET'])
@jwt_required()
def get_text_recitations():
    try:
        user_id = get_jwt_identity()
        texts = TextRecitation.query.filter_by(user_id=user_id).order_by(TextRecitation.create_time.desc()).all()
        return jsonify([text.to_dict() for text in texts]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/text-recitation/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_text_recitation(id):
    try:
        user_id = get_jwt_identity()
        text = TextRecitation.query.filter_by(id=id, user_id=user_id).first()
        
        if not text:
            return jsonify({'error': '课文不存在'}), 404
            
        db.session.delete(text)
        db.session.commit()
        
        return jsonify({'message': '删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/text-recitation/<int:id>', methods=['PUT'])
@jwt_required()
def update_text_recitation(id):
    try:
        user_id = get_jwt_identity()
        text = TextRecitation.query.filter_by(id=id, user_id=user_id).first()
        
        if not text:
            return jsonify({'error': '课文不存在'}), 404
            
        content = request.json.get('content')
        if not content:
            return jsonify({'error': '内容不能为空'}), 400
            
        text.content = content
        db.session.commit()
        
        return jsonify(text.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/text-recitation/<int:id>/recite', methods=['POST'])
@jwt_required()
def recite_text(id):
    try:
        logger.info(f"开始处理朗诵请求，ID: {id}")
        
        # 获取用户ID
        user_id = get_jwt_identity()
        logger.info(f"用户ID: {user_id}")
        
        # 查询文本
        text = TextRecitation.query.filter_by(id=id, user_id=user_id).first()
        if not text:
            logger.error(f"未找到ID为 {id} 的文本朗诵记录")
            return jsonify({'error': '课文不存在'}), 404
            
        # 检查音频文件
        if 'audio' not in request.files:
            logger.error("请求中没有音频文件")
            return jsonify({'error': '没有上传音频'}), 400
            
        audio_file = request.files['audio']
        logger.info(f"收到音频文件: {audio_file.filename}")
        
        # 检查文件扩展名
        if not audio_file.filename.lower().endswith('.wav'):
            logger.error("文件不是WAV格式")
            return jsonify({'error': '请上传WAV格式的音频文件'}), 400
        
        # 保存临时音频文件
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, 'temp.wav')
        audio_file.save(temp_path)
        logger.info(f"音频文件已保存到: {temp_path}")
        
        # 验证WAV文件
        is_valid, error_msg = is_valid_wav_file(temp_path)
        if not is_valid:
            logger.error(f"音频文件验证失败: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        try:
            # 使用本地Vosk模型进行语音识别
            logger.info("开始语音识别...")
            recited_text = speech_service.recognize(temp_path)
            logger.info(f"识别结果: {recited_text}")
            
            # 计算相似度和评分
            similarity = calculate_similarity(text.content, recited_text)
            score = int(similarity * 100)
            logger.info(f"相似度: {similarity}, 得分: {score}")
            
            return jsonify({
                'recited_text': recited_text,
                'original_text': text.content,
                'score': score,
                'similarity': similarity
            }), 200
        except Exception as e:
            logger.error(f"语音识别或评分过程中发生错误: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            logger.info("临时文件已清理")
        
    except Exception as e:
        logger.error(f"处理朗诵请求时发生错误: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp.route('/api/text-recitation/<int:id>/scores', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_recitation_scores(id):
    """获取课文背诵的成绩历史"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        text = TextRecitation.query.filter_by(id=id, user_id=user_id).first()
        
        if not text:
            return jsonify({'error': '课文不存在'}), 404
            
        # 获取所有背诵记录
        practices = Practice.query.filter_by(
            user_id=user_id,
            text_id=id,
            practice_type='text_recitation'
        ).order_by(Practice.created_at.desc()).all()
        
        if not practices:
            return jsonify({
                'current_score': None,
                'best_score': None,
                'history': []
            })
            
        # 获取当前成绩和最好成绩
        current_score = practices[0].score if practices else None
        best_score = max(p.score for p in practices)
        
        # 格式化历史记录
        history = [{
            'score': p.score,
            'date': p.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for p in practices]
        
        return jsonify({
            'current_score': current_score,
            'best_score': best_score,
            'history': history
        })
    except Exception as e:
        logger.error(f"获取背诵成绩历史失败: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500 
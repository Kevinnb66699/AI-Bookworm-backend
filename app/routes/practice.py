from flask import Blueprint, request, jsonify
from ..models import Word  # 假设有一个Word模型存储单词和含义
from .. import db

bp = Blueprint('practice', __name__, url_prefix='/practice')

@bp.route('/word', methods=['POST'])
def word_practice():
    data = request.get_json()
    word_id = data.get('word_id')
    user_input = data.get('user_input')

    word = Word.query.get(word_id)
    if not word:
        return jsonify({'error': 'Word not found'}), 404

    is_correct = word.text.lower() == user_input.lower()
    return jsonify({
        'is_correct': is_correct,
        'correct_word': word.text if not is_correct else None
    })

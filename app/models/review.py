from datetime import datetime
from app import db

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    quality = db.Column(db.Integer, nullable=False)  # 0-5的复习质量评分
    
    # 关联到单词或课文（二选一）
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'))
    text_id = db.Column(db.Integer, db.ForeignKey('texts.id'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'quality': self.quality,
            'word_id': self.word_id,
            'text_id': self.text_id
        } 
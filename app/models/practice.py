from datetime import datetime
from app import db

class Practice(db.Model):
    __tablename__ = 'practices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    practice_type = db.Column(db.String(20), nullable=False)  # 'word', 'text_fill', 'text_full'
    score = db.Column(db.Float, nullable=False)  # 0-100的得分
    mistakes = db.Column(db.JSON)  # 记录错误详情
    
    # 关联到课文（用于课文填空和完整默写）
    text_id = db.Column(db.Integer, db.ForeignKey('texts.id'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'practice_type': self.practice_type,
            'score': self.score,
            'mistakes': self.mistakes,
            'text_id': self.text_id
        } 
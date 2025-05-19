from datetime import datetime, timedelta
from app import db
import json

class Word(db.Model):
    __tablename__ = 'words'
    
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    meanings = db.Column(db.JSON, nullable=False)  # 存储多个释义的JSON数组
    example = db.Column(db.Text)
    pronunciation = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # SM-2算法相关字段
    ease_factor = db.Column(db.Float, default=2.5)
    interval = db.Column(db.Integer, default=0)  # 下次复习间隔（天）
    repetitions = db.Column(db.Integer, default=0)  # 复习次数
    next_review = db.Column(db.DateTime)  # 下次复习时间
    
    # 关联
    reviews = db.relationship('Review', backref='word', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'word': self.word,
            'meanings': self.meanings,
            'example': self.example,
            'pronunciation': self.pronunciation,
            'course_id': self.course_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'ease_factor': self.ease_factor,
            'interval': self.interval,
            'repetitions': self.repetitions,
            'next_review': self.next_review.isoformat() if self.next_review else None
        }
        
    def update_sm2(self, quality):
        """更新SM-2算法参数
        quality: 0-5的整数，表示复习质量
        """
        if quality < 3:  # 如果复习效果不好，重置间隔
            self.interval = 0
            self.repetitions = 0
        else:
            if self.repetitions == 0:
                self.interval = 1
            elif self.repetitions == 1:
                self.interval = 6
            else:
                self.interval = int(self.interval * self.ease_factor)
            
            self.ease_factor = max(1.3, self.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
            self.repetitions += 1
            
        self.next_review = datetime.utcnow() + timedelta(days=self.interval)

    @classmethod
    def get_practice_stats(cls, course_id, user_id):
        """获取练习统计信息"""
        from .word_practice import WordPractice
        practices = WordPractice.query.filter_by(user_id=user_id).all()
        if not practices:
            return {
                'total_words': 0,
                'correct_count': 0,
                'accuracy': 0
            }   
        
        correct_count = sum(1 for p in practices if p.is_correct)
        total_words = len(practices)
        accuracy = (correct_count / total_words) * 100
        
        return {
            'total_words': total_words,
            'correct_count': correct_count,
            'accuracy': accuracy
        } 
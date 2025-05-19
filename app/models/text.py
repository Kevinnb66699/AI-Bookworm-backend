from datetime import datetime, timedelta
from app import db

class Text(db.Model):
    __tablename__ = 'texts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    translation = db.Column(db.Text)
    difficulty = db.Column(db.Integer, default=1)  # 1-5的难度等级
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # SM-2算法相关字段
    ease_factor = db.Column(db.Float, default=2.5)
    interval = db.Column(db.Integer, default=0)  # 下次复习间隔（天）
    repetitions = db.Column(db.Integer, default=0)  # 复习次数
    next_review = db.Column(db.DateTime)  # 下次复习时间
    
    # 关联
    reviews = db.relationship('Review', backref='text', lazy=True)
    practices = db.relationship('Practice', backref='text', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'translation': self.translation,
            'difficulty': self.difficulty,
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
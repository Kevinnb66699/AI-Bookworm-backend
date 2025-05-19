from .. import db
from datetime import datetime

class PracticeProgress(db.Model):
    __tablename__ = 'practice_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    practiced_words = db.Column(db.Integer, default=0)
    correct_count = db.Column(db.Integer, default=0)
    accuracy = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'practiced_words': self.practiced_words,
            'correct_count': self.correct_count,
            'accuracy': self.accuracy,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 
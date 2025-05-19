from app import db
from datetime import datetime

class Reminder(db.Model):
    __tablename__ = 'reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'word' or 'text'
    item_id = db.Column(db.Integer, nullable=False)  # word_id or text_id
    next_review_date = db.Column(db.Date, nullable=False)
    review_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'type': self.type,
            'item_id': self.item_id,
            'next_review_date': self.next_review_date.strftime('%Y-%m-%d'),
            'review_count': self.review_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } 
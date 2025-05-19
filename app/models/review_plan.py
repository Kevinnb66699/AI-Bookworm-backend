from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Boolean, String
from sqlalchemy.orm import relationship
from .. import db

class ReviewPlan(db.Model):
    __tablename__ = 'review_plans'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    word_id = Column(Integer, ForeignKey('words.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    status = Column(String(20), default='pending')
    next_review_time = Column(DateTime, nullable=False)
    last_review_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    review_count = Column(Integer, default=0)  # 复习次数
    consecutive_correct = Column(Integer, default=0)  # 连续正确次数
    is_mastered = Column(Boolean, default=False)  # 是否已掌握

    # 关系
    user = relationship("User", backref="review_plans")
    word = relationship("Word", backref="review_plans")
    course = relationship("Course", backref="review_plans")

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'word_id': self.word_id,
            'course_id': self.course_id,
            'status': self.status,
            'nextReviewTime': self.next_review_time.isoformat(),
            'lastReviewTime': self.last_review_time.isoformat() if self.last_review_time else None,
            'createdAt': self.created_at.isoformat(),
            'review_count': self.review_count,
            'consecutive_correct': self.consecutive_correct,
            'is_mastered': self.is_mastered
        } 
from .auth import bp as auth_bp
from .practice import bp as practice_bp
from .word import bp as word_bp
from .course import bp as course_bp
from .import_export import bp as import_export_bp
from .reminder import bp as reminder_bp
# 其他路由导入

__all__ = ['auth_bp', 'practice_bp', 'word_bp', 'course_bp', 'import_export_bp', 'reminder_bp'] 
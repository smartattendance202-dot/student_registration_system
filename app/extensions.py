# -*- coding: utf-8 -*-
"""
إضافات Flask
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
# تم إزالة المجدولة - البيانات محفوظة دائماً

# إنشاء كائنات الإضافات
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"],  # زيادة الحدود لتحميل الصور
    storage_uri="memory://"  # تخزين صريح في الذاكرة للتطوير لتفادي التحذير
)
# لا توجد مجدولة في نظام تسجيل البيانات

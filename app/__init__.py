# -*- coding: utf-8 -*-
"""
تطبيق نظام تسجيل الطلاب
"""

import os
from flask import Flask
from app.extensions import db, migrate, login_manager, csrf, limiter
from app.config import Config


def create_app(config_class=Config):
    """إنشاء وتكوين تطبيق Flask"""
    print('[create_app] start')
    app = Flask(__name__)
    print('[create_app] Flask created')
    app.config.from_object(config_class)
    print('[create_app] config loaded')

    # تهيئة الإضافات
    db.init_app(app)
    print('[create_app] db.init_app')
    migrate.init_app(app, db)
    print('[create_app] migrate.init_app')
    login_manager.init_app(app)
    print('[create_app] login_manager.init_app')
    csrf.init_app(app)
    print('[create_app] csrf.init_app')
    limiter.init_app(app)
    print('[create_app] limiter.init_app')

    # تكوين Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة.'
    login_manager.login_message_category = 'info'
    print('[create_app] login configured')

    # تسجيل Blueprints
    from app.auth.routes import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    print('[create_app] auth blueprint')

    from app.student.routes import bp as student_bp
    app.register_blueprint(student_bp, url_prefix='/student')
    print('[create_app] student blueprint')



    # الصفحة الرئيسية
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    print('[create_app] main blueprint')

    # لا توجد مجدولة في نظام تسجيل البيانات - البيانات محفوظة دائماً
    print('[create_app] نظام تسجيل بيانات بدون مجدولة')

    # إنشاء مجلدات الرفع
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(os.path.join(upload_folder, 'applications'), exist_ok=True)
    print('[create_app] upload folders ready')

    # تنظيف دوري للحسابات غير المؤكدة (عند بدء التطبيق)
    with app.app_context():
        try:
            from app.models import User
            deleted_count = User.delete_unverified_users()
            if deleted_count > 0:
                print(f'🧹 تم حذف {deleted_count} حساب غير مؤكد منتهي الصلاحية عند بدء التطبيق')
        except Exception as e:
            print(f'❌ خطأ في تنظيف الحسابات عند بدء التطبيق: {str(e)}')

    print('[create_app] done')
    return app


# استيراد النماذج لضمان إنشاء الجداول
from app import models

# -*- coding: utf-8 -*-
"""
إعدادات التطبيق
"""

import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'))


class Config:
    """إعدادات التطبيق الأساسية"""
    
    # إعدادات Flask الأساسية
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # إعدادات قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        'mysql+pymysql://root:password@localhost/student_registration_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # إعدادات رفع الملفات
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 5242880))  # 5MB
    
    # أنواع الملفات المسموحة
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    ALLOWED_PHOTO_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp'}  # دعم تنسيقات إضافية عالية الجودة
    
    # أحجام الملفات القصوى
    MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_PHOTO_SIZE = 15 * 1024 * 1024     # 15MB لدعم الصور عالية الجودة
    
    # إعدادات الصور - بدون قيود على الأبعاد
    # تم إزالة قيود الأبعاد للصور الشخصية
    
    # إعدادات الأمان
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    
    # إعدادات معدل الطلبات
    # Flask-Limiter يستخدم RATELIMIT_STORAGE_URI وليس URL
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', os.environ.get('RATELIMIT_STORAGE_URL', 'memory://'))
    
    # إعدادات Flask
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    # إعدادات WhatsApp Business API
    WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN') or 'your_access_token_here'
    WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID') or 'your_phone_number_id_here'
    WHATSAPP_ENABLED = os.environ.get('WHATSAPP_ENABLED', 'False').lower() == 'true'


class DevelopmentConfig(Config):
    """إعدادات التطوير"""
    DEBUG = True


class ProductionConfig(Config):
    """إعدادات الإنتاج"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """إعدادات الاختبار"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    # لا توجد مجدولة في نظام تسجيل البيانات


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

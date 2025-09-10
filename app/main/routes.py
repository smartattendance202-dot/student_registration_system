# -*- coding: utf-8 -*-
"""
المسارات الرئيسية
"""

import os
from flask import render_template, redirect, url_for, abort, current_app, send_from_directory
from flask_login import current_user, login_required
from app.main import bp
from app.services.files import serve_file, get_validation_system_status
from app.extensions import limiter


@bp.route('/')
def index():
    """الصفحة الرئيسية"""
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('student.status'))
    return render_template('main/index.html')


@bp.route('/files/<path:file_path>')
@limiter.exempt  # استثناء من rate limiting للملفات
@login_required
def serve_uploaded_file(file_path):
    """تقديم الملفات المرفوعة مع التحقق من الصلاحيات"""
    # استخراج معرف المستخدم من مسار الملف
    path_parts = file_path.split('/')
    if len(path_parts) >= 2:
        try:
            user_id = int(path_parts[1])
        except ValueError:
            abort(404)
    else:
        abort(404)

    return serve_file(file_path, user_id, check_permissions=True)


@bp.route('/files_or_static/<path:file_path>')
@limiter.exempt  # استثناء من rate limiting للملفات
@login_required
def serve_any_file(file_path):
    """Serve file from UPLOAD_FOLDER if present, otherwise fall back to app static folder.

    This helps when older uploads were placed under `static/` or when paths vary.
    """
    # try uploads folder
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    # تطبيع المسار لتجنب مشاكل الخلط بين الشرطات المائلة على ويندوز
    normalized_file_path = file_path.replace('/', os.sep).replace('\\', os.sep)

    # التأكد من أن المسار مطلق
    if os.path.isabs(upload_folder):
        upload_full = os.path.join(upload_folder, normalized_file_path)
    else:
        # إذا كان المسار نسبي، نجعله نسبة إلى جذر المشروع (مجلد أعلى من app)
        app_dir = os.path.dirname(os.path.abspath(__file__))  # app/main
        project_root = os.path.dirname(os.path.dirname(app_dir))  # جذر المشروع
        upload_full = os.path.join(project_root, upload_folder, normalized_file_path)

    # تطبيع المسار النهائي
    upload_full = os.path.normpath(upload_full)

    current_app.logger.debug(f'البحث عن الملف في: {upload_full}')

    if os.path.exists(upload_full):
        # extract user_id for permission check if possible
        path_parts = file_path.split('/')
        user_id = None
        if len(path_parts) >= 2:
            try:
                user_id = int(path_parts[1])
            except ValueError:
                user_id = None
        # للمشرفين، لا نحتاج للتحقق من الصلاحيات
        if current_user.role == 'admin':
            return serve_file(file_path, user_id, check_permissions=False)
        else:
            return serve_file(file_path, user_id, check_permissions=True)

    # fallback to static folder
    normalized_static_path = file_path.replace('/', os.sep)
    static_full = os.path.join(current_app.static_folder or 'static', normalized_static_path)
    if os.path.exists(static_full):
        # send from the static folder (no extra permission checks)
        return send_from_directory(current_app.static_folder or 'static', file_path)

    current_app.logger.error(f'الملف غير موجود في كلا المجلدين: {upload_full} و {static_full}')
    abort(404)


@bp.route('/system-status')
@login_required
def system_status():
    """عرض حالة نظام التحقق من الصور"""
    # فقط للمدراء أو للمطورين
    if current_user.role != 'admin':
        abort(403)
    
    status = get_validation_system_status()
    return render_template('main/system_status.html', status=status)
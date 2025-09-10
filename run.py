#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نقطة دخول تطبيق نظام تسجيل الطلاب
"""


import os
import sys
import logging
from app import create_app

app = create_app()

if __name__ == '__main__':
    # إنشاء مجلد الرفع إذا لم يكن موجوداً
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'temp'), exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'students'), exist_ok=True)

    print('Starting Flask development server on http://127.0.0.1:5000 ...')
    try:
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=app.config.get('FLASK_DEBUG', False),
            use_reloader=False
        )
    except Exception as e:
        print('Failed to start Flask server:', str(e))

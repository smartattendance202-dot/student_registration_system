# -*- coding: utf-8 -*-
"""
مسارات الطلاب
"""

import os
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.student import bp
from app.extensions import db
from app.forms.application import ApplicationForm
from app.models import Application, User
from app.services.files import save_uploaded_file, validate_file
from functools import wraps


def student_required(f):
    """ديكوريتر للتحقق من أن المستخدم طالب"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'student':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/status')
@login_required
@student_required
def status():
    """عرض حالة طلبات التسجيل"""
    applications = Application.query.filter_by(user_id=current_user.id).order_by(Application.created_at.desc()).all()
    application_count = len(applications)
    can_submit_new = Application.can_user_submit_new_application(current_user.id)

    return render_template('student/status.html',
                         title='حالة الطلبات',
                         applications=applications,
                         application_count=application_count,
                         can_submit_new=can_submit_new)


@bp.route('/application', methods=['GET', 'POST'])
@login_required
@student_required
def application():
    """تقديم طلب تسجيل جديد"""
    # التحقق من عدد الطلبات السابقة
    if not Application.can_user_submit_new_application(current_user.id):
        flash('لقد تجاوزت الحد الأقصى للطلبات (5 طلبات). لا يمكن تقديم طلبات إضافية.', 'error')
        return redirect(url_for('student.status'))
    
    form = ApplicationForm()
    
    if form.validate_on_submit():
        try:
            # حساب رقم الطلب الجديد
            application_count = Application.get_user_application_count(current_user.id)
            new_application_number = application_count + 1

            # إنشاء طلب جديد
            application = Application(
                user_id=current_user.id,
                full_name=form.full_name.data,
                birth_date=form.birth_date.data,
                gender=form.gender.data,
                nationality=form.nationality.data,
                birthplace=form.birthplace.data,
                phone=form.phone.data,
                email=form.email.data if form.email.data else None,
                term_name=form.term_name.data,
                school_name=form.school_name.data,
                guardian_name=form.guardian_name.data,
                guardian_phone=form.guardian_phone.data,
                application_number=new_application_number
            )
            
            # حساب وحفظ العمر
            application.calculate_and_save_age()
            
            # حفظ الصور الشخصية الخمس مع فحص الوجوه
            if form.image1.data:
                img1_path = save_uploaded_file(form.image1.data, 'applications', current_user.id, 'photo', 'الصورة الأولى')
                application.image1_path = img1_path

            if form.image2.data:
                img2_path = save_uploaded_file(form.image2.data, 'applications', current_user.id, 'photo', 'الصورة الثانية')
                application.image2_path = img2_path

            if form.image3.data:
                img3_path = save_uploaded_file(form.image3.data, 'applications', current_user.id, 'photo', 'الصورة الثالثة')
                application.image3_path = img3_path

            if form.image4.data:
                img4_path = save_uploaded_file(form.image4.data, 'applications', current_user.id, 'photo', 'الصورة الرابعة')
                application.image4_path = img4_path

            if form.image5.data:
                img5_path = save_uploaded_file(form.image5.data, 'applications', current_user.id, 'photo', 'الصورة الخامسة')
                application.image5_path = img5_path
            
            db.session.add(application)
            db.session.commit()
            
            remaining_applications = 5 - Application.get_user_application_count(current_user.id)
            if remaining_applications > 0:
                flash(f'تم تقديم طلبك رقم {new_application_number} بنجاح وحفظ بياناتك في النظام. يمكنك تقديم {remaining_applications} طلبات إضافية.', 'success')
            else:
                flash(f'تم تقديم طلبك رقم {new_application_number} بنجاح وحفظ بياناتك في النظام. هذا آخر طلب مسموح به.', 'success')
            return redirect(url_for('student.status'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'خطأ في تقديم الطلب: {str(e)}')
            flash('حدث خطأ أثناء تقديم الطلب. يرجى المحاولة مرة أخرى.', 'error')
    
    return render_template('student/application.html', 
                         title='تقديم طلب التسجيل', 
                         form=form)


@bp.route('/validate-image', methods=['POST'])
@login_required
@student_required
def validate_image():
    """فحص فوري للصورة عند اختيارها"""
    try:
        # التحقق من وجود الملف
        if 'image' not in request.files:
            return jsonify({
                'valid': False,
                'message': 'لم يتم اختيار ملف'
            })
        
        file = request.files['image']
        image_name = request.form.get('image_name', 'صورة')
        
        if not file or not file.filename:
            return jsonify({
                'valid': False,
                'message': 'لم يتم اختيار ملف صحيح'
            })
        
        # فحص الصورة باستخدام نظام التحقق
        valid, message = validate_file(file, 'photo', current_user.id, image_name)
        
        return jsonify({
            'valid': valid,
            'message': message
        })
        
    except Exception as e:
        current_app.logger.error(f'خطأ في فحص الصورة: {str(e)}')
        return jsonify({
            'valid': False,
            'message': 'خطأ في فحص الصورة. يرجى المحاولة مرة أخرى.'
        })



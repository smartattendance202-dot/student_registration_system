# -*- coding: utf-8 -*-
"""
مسارات المصادقة
"""

from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, current_user, login_required
from flask_limiter import Limiter
from app.auth import bp
from app.extensions import db, limiter
from app.forms.auth import LoginForm, RegistrationForm, VerificationForm, ChangePasswordForm
from app.services.sms import send_verification_sms
from app.models import User, Application


@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """تسجيل الدخول"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    # ملء الرقم تلقائياً إذا تم تمريره من صفحة التسجيل
    if request.method == 'GET' and request.args.get('phone'):
        form.phone.data = request.args.get('phone')
    
    if form.validate_on_submit():
        # الرقم تم تحويله بالفعل في validate_phone
        user = User.query.filter_by(phone=form.phone.data).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('حسابك غير مفعل. يرجى التواصل مع الإدارة.', 'error')
                return redirect(url_for('auth.login'))

            if not user.is_phone_verified:
                flash('يجب تأكيد رقم الهاتف أولاً. سيتم إرسال رمز التحقق.', 'warning')
                # إرسال رمز تحقق جديد
                verification_code = user.generate_verification_code()
                db.session.commit()

                if send_verification_sms(user.phone, verification_code):
                    session['verification_phone'] = user.phone
                    return redirect(url_for('auth.verify_phone'))
                else:
                    flash('خطأ في إرسال رمز التحقق. يرجى المحاولة لاحقاً.', 'error')
                    return redirect(url_for('auth.login'))

            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')

            if not next_page or not next_page.startswith('/'):
                next_page = url_for('student.status')

            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(next_page)
        else:
            flash('رقم الهاتف أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('auth/login.html', title='تسجيل الدخول', form=form)


@bp.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    """إنشاء حساب جديد"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    # تنظيف الحسابات غير المؤكدة منتهية الصلاحية
    try:
        deleted_count = User.delete_unverified_users()
        if deleted_count > 0:
            current_app.logger.info(f'تم حذف {deleted_count} حساب غير مؤكد منتهي الصلاحية')
    except Exception as e:
        current_app.logger.error(f'خطأ في تنظيف الحسابات غير المؤكدة: {str(e)}')

    form = RegistrationForm()
    
    # إضافة تسجيل للتشخيص
    if request.method == 'POST':
        current_app.logger.info(f'محاولة تسجيل بالرقم: {form.phone.data}')
        
        # التحقق من وجود الرقم مسبقاً قبل التحقق من النموذج
        if form.phone.data:
            # تنظيف الرقم
            clean_phone = form.phone.data.strip().replace(' ', '').replace('-', '')
            if clean_phone.startswith('+967'):
                clean_phone = clean_phone[4:]
            elif clean_phone.startswith('967'):
                clean_phone = clean_phone[3:]
            elif clean_phone.startswith('00967'):
                clean_phone = clean_phone[5:]
            
            if clean_phone.startswith('7') and len(clean_phone) == 9 and clean_phone.isdigit():
                full_phone = '+967' + clean_phone
                existing_user = User.query.filter_by(phone=full_phone).first()
                if existing_user:
                    flash('يوجد حساب مسجل بهذا الرقم بالفعل. يرجى تسجيل الدخول أو استخدام رقم آخر.', 'error')
                    return render_template('auth/register.html', title='إنشاء حساب جديد', form=form, 
                                         show_login_link=True, existing_phone=full_phone)
    
    if form.validate_on_submit():
        try:
            # إنشاء مستخدم جديد
            user = User(
                phone=form.phone.data,
                role='student',
                is_active=True,
                is_phone_verified=False
            )
            user.set_password(form.password.data)

            # إنشاء رمز التحقق
            verification_code = user.generate_verification_code()

            db.session.add(user)
            db.session.commit()

            # إرسال رمز التحقق
            if send_verification_sms(user.phone, verification_code):
                session['verification_phone'] = user.phone
                flash('تم إنشاء الحساب بنجاح. تم إرسال رمز التحقق إلى هاتفك.', 'success')
                return redirect(url_for('auth.verify_phone'))
            else:
                flash('تم إنشاء الحساب ولكن فشل إرسال رمز التحقق. يرجى المحاولة لاحقاً.', 'warning')
                return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'خطأ في إنشاء الحساب: {str(e)}')
            flash('حدث خطأ أثناء إنشاء الحساب. يرجى المحاولة مرة أخرى.', 'error')

    return render_template('auth/register.html', title='إنشاء حساب جديد', form=form)


@bp.route('/verify-phone', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def verify_phone():
    """التحقق من رمز الهاتف"""
    phone = session.get('verification_phone')
    if not phone:
        flash('جلسة التحقق منتهية. يرجى تسجيل الدخول مرة أخرى.', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(phone=phone).first()
    if not user:
        flash('المستخدم غير موجود.', 'error')
        return redirect(url_for('auth.login'))

    # التحقق من انتهاء صلاحية رمز التحقق
    if user.is_verification_expired():
        try:
            # حذف الحساب إذا انتهت صلاحية رمز التحقق
            Application.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            db.session.commit()
            session.pop('verification_phone', None)
            
            current_app.logger.info(f'تم حذف الحساب غير المؤكد منتهي الصلاحية: {phone}')
            flash('انتهت صلاحية رمز التحقق وتم حذف الحساب. يرجى إنشاء حساب جديد.', 'warning')
            return redirect(url_for('auth.register'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'خطأ في حذف الحساب منتهي الصلاحية {phone}: {str(e)}')
            flash('انتهت صلاحية رمز التحقق. يرجى إنشاء حساب جديد.', 'error')
            return redirect(url_for('auth.register'))

    form = VerificationForm()
    if form.validate_on_submit():
        if user.verify_code(form.verification_code.data):
            db.session.commit()
            session.pop('verification_phone', None)

            # تسجيل دخول تلقائي بعد التحقق
            login_user(user)
            flash('تم تأكيد رقم الهاتف بنجاح!', 'success')
            return redirect(url_for('student.status'))
        else:
            # التحقق مرة أخرى من انتهاء الصلاحية بعد فشل التحقق
            if user.is_verification_expired():
                try:
                    Application.query.filter_by(user_id=user.id).delete()
                    db.session.delete(user)
                    db.session.commit()
                    session.pop('verification_phone', None)
                    
                    current_app.logger.info(f'تم حذف الحساب غير المؤكد بعد فشل التحقق: {phone}')
                    flash('انتهت صلاحية رمز التحقق وتم حذف الحساب. يرجى إنشاء حساب جديد.', 'warning')
                    return redirect(url_for('auth.register'))
                    
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f'خطأ في حذف الحساب بعد فشل التحقق {phone}: {str(e)}')
            
            flash('رمز التحقق غير صحيح أو منتهي الصلاحية.', 'error')

    return render_template('auth/verify_phone.html', title='تأكيد رقم الهاتف', form=form, phone=phone)


@bp.route('/resend-code')
@limiter.limit("3 per 5 minutes")
def resend_code():
    """إعادة إرسال رمز التحقق"""
    phone = session.get('verification_phone')
    if not phone:
        flash('جلسة التحقق منتهية.', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(phone=phone).first()
    if not user:
        flash('المستخدم غير موجود.', 'error')
        return redirect(url_for('auth.login'))

    # إنشاء رمز جديد
    verification_code = user.generate_verification_code()
    db.session.commit()

    if send_verification_sms(user.phone, verification_code):
        flash('تم إرسال رمز التحقق الجديد.', 'success')
    else:
        flash('خطأ في إرسال رمز التحقق. يرجى المحاولة لاحقاً.', 'error')

    return redirect(url_for('auth.verify_phone'))


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """تغيير كلمة المرور"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('تم تغيير كلمة المرور بنجاح', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('كلمة المرور الحالية غير صحيحة', 'error')
    
    return render_template('auth/change_password.html', title='تغيير كلمة المرور', form=form)

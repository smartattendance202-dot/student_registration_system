# -*- coding: utf-8 -*-
"""
نماذج المصادقة - التسجيل برقم الهاتف مع رمز التحقق
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Regexp
from app.models import User


class LoginForm(FlaskForm):
    """نموذج تسجيل الدخول"""
    phone = StringField('رقم الجوال', validators=[
        DataRequired(message='رقم الجوال مطلوب')
    ])
    password = PasswordField('كلمة المرور', validators=[
        DataRequired(message='كلمة المرور مطلوبة')
    ])
    remember_me = BooleanField('تذكرني')
    submit = SubmitField('تسجيل الدخول')

    def validate_phone(self, phone):
        """تحويل رقم الهاتف إلى الصيغة الكاملة مع رمز اليمن"""
        if phone.data:
            # تنظيف الرقم من المسافات والرموز
            clean_phone = phone.data.strip().replace(' ', '').replace('-', '')
            
            # إزالة رمز الدولة إذا كان موجوداً للتحقق من الصيغة
            if clean_phone.startswith('+967'):
                clean_phone = clean_phone[4:]
            elif clean_phone.startswith('967'):
                clean_phone = clean_phone[3:]
            elif clean_phone.startswith('00967'):
                clean_phone = clean_phone[5:]
            
            # التحقق من أن الرقم يبدأ بـ 7 ويتكون من 9 أرقام
            if not clean_phone.startswith('7'):
                raise ValidationError('رقم الجوال يجب أن يبدأ بـ 7 (مثال: 712345678)')
            
            if len(clean_phone) != 9:
                raise ValidationError(f'رقم الجوال يجب أن يكون 9 أرقام، لكن الرقم المدخل {len(clean_phone)} أرقام')
            
            # التحقق من أن جميع الأحرف أرقام
            if not clean_phone.isdigit():
                raise ValidationError('رقم الجوال يجب أن يحتوي على أرقام فقط')
            
            # إضافة رمز اليمن تلقائياً
            phone.data = '+967' + clean_phone


class RegistrationForm(FlaskForm):
    """نموذج إنشاء حساب جديد"""
    phone = StringField('رقم الجوال', validators=[
        DataRequired(message='رقم الجوال مطلوب')
    ])
    password = PasswordField('كلمة المرور', validators=[
        DataRequired(message='كلمة المرور مطلوبة'),
        Length(min=8, message='كلمة المرور يجب أن تكون 8 أحرف على الأقل')
    ])
    password2 = PasswordField('تأكيد كلمة المرور', validators=[
        DataRequired(message='تأكيد كلمة المرور مطلوب'),
        EqualTo('password', message='كلمات المرور غير متطابقة')
    ])
    submit = SubmitField('إرسال رمز التحقق')

    def validate_phone(self, phone):
        """تحويل رقم الهاتف وفحص عدم التكرار"""
        if phone.data:
            # تنظيف الرقم من المسافات والرموز
            clean_phone = phone.data.strip().replace(' ', '').replace('-', '')
            
            # إزالة رمز الدولة إذا كان موجوداً للتحقق من الصيغة
            if clean_phone.startswith('+967'):
                clean_phone = clean_phone[4:]
            elif clean_phone.startswith('967'):
                clean_phone = clean_phone[3:]
            elif clean_phone.startswith('00967'):
                clean_phone = clean_phone[5:]
            
            # التحقق من أن الرقم يبدأ بـ 7 ويتكون من 9 أرقام
            if not clean_phone.startswith('7'):
                raise ValidationError('رقم الجوال يجب أن يبدأ بـ 7 (مثال: 712345678)')
            
            if len(clean_phone) != 9:
                raise ValidationError(f'رقم الجوال يجب أن يكون 9 أرقام، لكن الرقم المدخل {len(clean_phone)} أرقام')
            
            # التحقق من أن جميع الأحرف أرقام
            if not clean_phone.isdigit():
                raise ValidationError('رقم الجوال يجب أن يحتوي على أرقام فقط')
            
            # إنشاء الرقم الكامل
            full_phone = '+967' + clean_phone

            # فحص عدم تكرار الرقم
            try:
                user = User.query.filter_by(phone=full_phone).first()
                if user:
                    raise ValidationError('يوجد حساب مسجل بهذا الرقم بالفعل. يرجى تسجيل الدخول أو استخدام رقم آخر.')
            except Exception as e:
                # في حالة مشكلة في قاعدة البيانات، نظهر رسالة عامة
                if 'ValidationError' not in str(type(e)):
                    raise ValidationError('خطأ في التحقق من الرقم. يرجى المحاولة لاحقاً.')

            # تحديث البيانات بالرقم الكامل
            phone.data = full_phone


class VerificationForm(FlaskForm):
    """نموذج التحقق من رمز الهاتف"""
    verification_code = StringField('رمز التحقق', validators=[
        DataRequired(message='رمز التحقق مطلوب'),
        Length(min=6, max=6, message='رمز التحقق يجب أن يكون 6 أرقام')
    ])
    submit = SubmitField('تأكيد الرمز')


class ChangePasswordForm(FlaskForm):
    """نموذج تغيير كلمة المرور"""
    current_password = PasswordField('كلمة المرور الحالية', validators=[
        DataRequired(message='كلمة المرور الحالية مطلوبة')
    ])
    new_password = PasswordField('كلمة المرور الجديدة', validators=[
        DataRequired(message='كلمة المرور الجديدة مطلوبة'),
        Length(min=8, message='كلمة المرور يجب أن تكون 8 أحرف على الأقل')
    ])
    new_password2 = PasswordField('تأكيد كلمة المرور الجديدة', validators=[
        DataRequired(message='تأكيد كلمة المرور مطلوب'),
        EqualTo('new_password', message='كلمات المرور غير متطابقة')
    ])
    submit = SubmitField('تغيير كلمة المرور')

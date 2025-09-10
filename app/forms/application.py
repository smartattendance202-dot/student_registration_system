# -*- coding: utf-8 -*-
"""
نماذج طلبات التسجيل
"""

import re
from datetime import datetime, date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, DateField, TextAreaField, SubmitField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Email, Length, ValidationError, NumberRange, Optional
from app.models import User, Application


class ApplicationForm(FlaskForm):
    """نموذج طلب التسجيل"""
    
    # البيانات الشخصية
    full_name = StringField('الاسم الرباعي', validators=[
        DataRequired(message='الاسم الرباعي مطلوب'),
        Length(min=10, max=200, message='الاسم يجب أن يكون بين 10-200 حرف')
    ])
    
    birth_date = DateField('تاريخ الميلاد', validators=[
        DataRequired(message='تاريخ الميلاد مطلوب')
    ])
    
    gender = SelectField('الجنس', choices=[
        ('', 'اختر الجنس'),
        ('male', 'ذكر'),
        ('female', 'أنثى')
    ], validators=[DataRequired(message='الجنس مطلوب')])
    
    nationality = SelectField('الجنسية', choices=[
        ('', 'اختر الجنسية'),
        ('سعودي', 'سعودي'),
        ('مصري', 'مصري'),
        ('أردني', 'أردني'),
        ('سوري', 'سوري'),
        ('لبناني', 'لبناني'),
        ('فلسطيني', 'فلسطيني'),
        ('عراقي', 'عراقي'),
        ('يمني', 'يمني'),
        ('كويتي', 'كويتي'),
        ('إماراتي', 'إماراتي'),
        ('قطري', 'قطري'),
        ('بحريني', 'بحريني'),
        ('عماني', 'عماني'),
        ('أخرى', 'أخرى')
    ], validators=[DataRequired(message='الجنسية مطلوبة')])
    
    birthplace = StringField('مكان الميلاد', validators=[
        DataRequired(message='مكان الميلاد مطلوب'),
        Length(min=2, max=200, message='مكان الميلاد يجب أن يكون بين 2-200 حرف')
    ])
    
    # بيانات الاتصال
    phone = StringField('رقم الجوال', validators=[
        DataRequired(message='رقم الجوال مطلوب')
    ])

    email = StringField('البريد الإلكتروني (اختياري)', validators=[
        Optional(),
        Email(message='يرجى إدخال بريد إلكتروني صحيح')
    ])
    
    # البيانات الأكاديمية
    term_name = StringField('اسم الفصل الدراسي', validators=[
        DataRequired(message='اسم الفصل الدراسي مطلوب'),
        Length(min=5, max=100, message='اسم الفصل يجب أن يكون بين 5-100 حرف')
    ])

    school_name = StringField('اسم المدرسة', validators=[
        DataRequired(message='اسم المدرسة مطلوب'),
        Length(min=5, max=200, message='اسم المدرسة يجب أن يكون بين 5-200 حرف')
    ])
    
    # الصور الشخصية (5 صور)
    image1 = FileField('الصورة الشخصية الأولى', validators=[
        FileRequired(message='الصورة الشخصية الأولى مطلوبة'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'], message='يجب أن تكون صورة')
    ])

    image2 = FileField('الصورة الشخصية الثانية', validators=[
        FileRequired(message='الصورة الشخصية الثانية مطلوبة'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'], message='يجب أن تكون صورة')
    ])

    image3 = FileField('الصورة الشخصية الثالثة', validators=[
        FileRequired(message='الصورة الشخصية الثالثة مطلوبة'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'], message='يجب أن تكون صورة')
    ])

    image4 = FileField('الصورة الشخصية الرابعة', validators=[
        FileRequired(message='الصورة الشخصية الرابعة مطلوبة'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'], message='يجب أن تكون صورة')
    ])

    image5 = FileField('الصورة الشخصية الخامسة', validators=[
        FileRequired(message='الصورة الشخصية الخامسة مطلوبة'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'], message='يجب أن تكون صورة')
    ])
    
    # بيانات ولي الأمر
    guardian_name = StringField('اسم ولي الأمر', validators=[
        DataRequired(message='اسم ولي الأمر مطلوب'),
        Length(min=5, max=200, message='اسم ولي الأمر يجب أن يكون بين 5-200 حرف')
    ])
    
    guardian_phone = StringField('رقم جوال ولي الأمر', validators=[
        DataRequired(message='رقم جوال ولي الأمر مطلوب')
    ])
    
    # الإقرار
    privacy_agreement = BooleanField('أوافق على سياسة الخصوصية وشروط الاستخدام', validators=[
        DataRequired(message='يجب الموافقة على سياسة الخصوصية')
    ])
    
    submit = SubmitField('تقديم الطلب')

    def validate_birth_date(self, birth_date):
        """التحقق من صحة تاريخ الميلاد"""
        if birth_date.data:
            today = date.today()
            # التحقق من أن التاريخ ليس في المستقبل
            if birth_date.data > today:
                raise ValidationError('تاريخ الميلاد لا يمكن أن يكون في المستقبل')
            
            # التحقق من أن التاريخ معقول (ليس أقدم من 100 سنة)
            min_date = date(today.year - 100, today.month, today.day)
            if birth_date.data < min_date:
                raise ValidationError('تاريخ الميلاد غير صحيح')
    
    def validate_phone(self, phone):
        """التحقق من صحة رقم الجوال اليمني وإضافة رمز الدولة"""
        if phone.data:
            # تنظيف الرقم
            clean_phone = phone.data.strip().replace(' ', '').replace('-', '')
            
            # إزالة رمز الدولة إذا كان موجوداً
            if clean_phone.startswith('+967'):
                clean_phone = clean_phone[4:]
            elif clean_phone.startswith('967'):
                clean_phone = clean_phone[3:]
            elif clean_phone.startswith('00967'):
                clean_phone = clean_phone[5:]
            
            # التحقق من صحة الرقم اليمني (يبدأ بـ 7 ويكون 9 أرقام)
            if not (clean_phone.startswith('7') and len(clean_phone) == 9 and clean_phone.isdigit()):
                raise ValidationError('رقم الجوال يجب أن يبدأ بـ 7 ويكون 9 أرقام (مثال: 712345678)')
            
            # إضافة رمز اليمن
            phone.data = '+967' + clean_phone

    def validate_guardian_phone(self, guardian_phone):
        """التحقق من صحة رقم جوال ولي الأمر اليمني وإضافة رمز الدولة"""
        if guardian_phone.data:
            # تنظيف الرقم
            clean_phone = guardian_phone.data.strip().replace(' ', '').replace('-', '')
            
            # إزالة رمز الدولة إذا كان موجوداً
            if clean_phone.startswith('+967'):
                clean_phone = clean_phone[4:]
            elif clean_phone.startswith('967'):
                clean_phone = clean_phone[3:]
            elif clean_phone.startswith('00967'):
                clean_phone = clean_phone[5:]
            
            # التحقق من صحة الرقم اليمني (يبدأ بـ 7 ويكون 9 أرقام)
            if not (clean_phone.startswith('7') and len(clean_phone) == 9 and clean_phone.isdigit()):
                raise ValidationError('رقم جوال ولي الأمر يجب أن يبدأ بـ 7 ويكون 9 أرقام (مثال: 712345678)')
            
            # إضافة رمز اليمن
            guardian_phone.data = '+967' + clean_phone


# حذف نموذج التحديث لأنه لم يعد مطلوباً

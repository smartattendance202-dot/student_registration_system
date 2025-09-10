# -*- coding: utf-8 -*-
"""
نماذج قاعدة البيانات المبسطة - نظام تسجيل البيانات فقط
"""

from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from app.extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    """تحميل المستخدم للجلسة"""
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    """نموذج المستخدمين - للطلاب فقط"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('student', name='user_roles'), nullable=False, default='student')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_phone_verified = db.Column(db.Boolean, nullable=False, default=False)
    verification_code = db.Column(db.String(10), nullable=True)
    verification_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    applications = db.relationship('Application',
                                  foreign_keys='Application.user_id',
                                  backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """تشفير كلمة المرور"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """التحقق من كلمة المرور"""
        return check_password_hash(self.password_hash, password)
    
    def generate_verification_code(self):
        """إنشاء رمز التحقق"""
        import random
        self.verification_code = str(random.randint(100000, 999999))
        self.verification_expires = datetime.utcnow() + timedelta(minutes=10)
        return self.verification_code

    def verify_code(self, code):
        """التحقق من رمز التحقق"""
        if not self.verification_code or not self.verification_expires:
            return False

        if datetime.utcnow() > self.verification_expires:
            return False

        if self.verification_code == code:
            self.is_phone_verified = True
            self.verification_code = None
            self.verification_expires = None
            return True

        return False

    def is_verification_expired(self):
        """التحقق من انتهاء صلاحية رمز التحقق"""
        if not self.verification_expires:
            return False
        return datetime.utcnow() > self.verification_expires

    @staticmethod
    def delete_unverified_users():
        """حذف المستخدمين غير المؤكدين والذين انتهت صلاحية رمز التحقق"""
        from app.extensions import db
        
        # البحث عن المستخدمين غير المؤكدين والذين انتهت صلاحية رمز التحقق
        expired_users = User.query.filter(
            User.is_phone_verified == False,
            User.verification_expires.isnot(None),
            User.verification_expires < datetime.utcnow()
        ).all()
        
        deleted_count = 0
        for user in expired_users:
            try:
                # حذف جميع الطلبات المرتبطة بالمستخدم أولاً
                Application.query.filter_by(user_id=user.id).delete()
                
                # حذف المستخدم
                db.session.delete(user)
                deleted_count += 1
                
                print(f"🗑️ تم حذف المستخدم غير المؤكد: {user.phone}")
                
            except Exception as e:
                print(f"❌ خطأ في حذف المستخدم {user.phone}: {str(e)}")
                db.session.rollback()
                continue
        
        if deleted_count > 0:
            try:
                db.session.commit()
                print(f"✅ تم حذف {deleted_count} مستخدم غير مؤكد من قاعدة البيانات")
            except Exception as e:
                print(f"❌ خطأ في حفظ التغييرات: {str(e)}")
                db.session.rollback()
        else:
            print("ℹ️ لا توجد حسابات غير مؤكدة منتهية الصلاحية للحذف")
        
        return deleted_count

    @staticmethod
    def cleanup_old_unverified_users(hours=24):
        """حذف المستخدمين غير المؤكدين الأقدم من عدد ساعات محدد"""
        from app.extensions import db
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # البحث عن المستخدمين غير المؤكدين والأقدم من الوقت المحدد
        old_unverified_users = User.query.filter(
            User.is_phone_verified == False,
            User.created_at < cutoff_time
        ).all()
        
        deleted_count = 0
        for user in old_unverified_users:
            try:
                # حذف جميع الطلبات المرتبطة بالمستخدم أولاً
                Application.query.filter_by(user_id=user.id).delete()
                
                # حذف المستخدم
                db.session.delete(user)
                deleted_count += 1
                
                print(f"🗑️ تم حذف المستخدم القديم غير المؤكد: {user.phone} (تم إنشاؤه في {user.created_at})")
                
            except Exception as e:
                print(f"❌ خطأ في حذف المستخدم {user.phone}: {str(e)}")
                db.session.rollback()
                continue
        
        if deleted_count > 0:
            try:
                db.session.commit()
                print(f"✅ تم حذف {deleted_count} مستخدم قديم غير مؤكد من قاعدة البيانات")
            except Exception as e:
                print(f"❌ خطأ في حفظ التغييرات: {str(e)}")
                db.session.rollback()
        else:
            print(f"ℹ️ لا توجد حسابات غير مؤكدة أقدم من {hours} ساعة للحذف")
        
        return deleted_count

    def __repr__(self):
        return f'<User {self.phone}>'


class Application(db.Model):
    """نموذج طلبات التسجيل"""
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # البيانات الشخصية
    full_name = db.Column(db.String(200), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=True)  # العمر محفوظ في قاعدة البيانات
    gender = db.Column(db.Enum('male', 'female', name='gender_types'), nullable=False)
    nationality = db.Column(db.String(100), nullable=False)
    birthplace = db.Column(db.String(200), nullable=False)
    
    # بيانات الاتصال
    phone = db.Column(db.String(20), nullable=False)  # رقم يمني
    email = db.Column(db.String(120), nullable=True)  # اختياري
    
    # البيانات الأكاديمية
    term_name = db.Column(db.String(100), nullable=False)
    school_name = db.Column(db.String(200), nullable=False)
    
    # الصور الشخصية (5 صور)
    image1_path = db.Column(db.String(500))
    image2_path = db.Column(db.String(500))
    image3_path = db.Column(db.String(500))
    image4_path = db.Column(db.String(500))
    image5_path = db.Column(db.String(500))
    
    # بيانات ولي الأمر
    guardian_name = db.Column(db.String(200), nullable=False)
    guardian_phone = db.Column(db.String(20), nullable=False)
    
    # معلومات التسجيل
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    application_number = db.Column(db.Integer, nullable=False, default=1)  # رقم الطلب للمستخدم
    
    # فهارس لتحسين الأداء
    __table_args__ = (
        db.Index('idx_app_full_name', 'full_name'),
        db.Index('idx_app_email', 'email'),
        db.Index('idx_app_phone', 'phone'),
        db.Index('idx_app_created_at', 'created_at'),
    )
    
    def calculate_and_save_age(self):
        """حساب العمر من تاريخ الميلاد وحفظه في قاعدة البيانات"""
        if self.birth_date:
            today = datetime.now().date()
            calculated_age = today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
            self.age = calculated_age
            return calculated_age
        return None

    @hybrid_property
    def current_age(self):
        """حساب العمر الحالي من تاريخ الميلاد (للعرض المباشر)"""
        if self.birth_date:
            today = datetime.now().date()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return self.age  # إرجاع العمر المحفوظ إذا لم يكن هناك تاريخ ميلاد

    @property
    def age_display(self):
        """عرض العمر مع النص"""
        age_value = self.age if self.age is not None else self.current_age
        if age_value is not None:
            return f"{age_value} سنة"
        return "غير محدد"

    @staticmethod
    def get_user_application_count(user_id):
        """حساب عدد طلبات المستخدم"""
        return Application.query.filter_by(user_id=user_id).count()

    @staticmethod
    def can_user_submit_new_application(user_id):
        """التحقق من إمكانية تقديم طلب جديد (أقل من 5 طلبات)"""
        return Application.get_user_application_count(user_id) < 5
    
    def __repr__(self):
        return f'<Application {self.full_name}>'

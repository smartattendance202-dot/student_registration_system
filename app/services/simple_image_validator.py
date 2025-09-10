"""
خدمة التحقق من الصور المبسطة (بدون مكتبات التعرف على الوجوه)
تعمل كخطة احتياطية عندما لا تكون مكتبات التعرف على الوجوه متوفرة
"""

from PIL import Image, ImageStat
import hashlib
import json
import os
from flask import current_app
from typing import Tuple, Dict, List
import io


class SimpleImageValidator:
    """خدمة التحقق من الصور المبسطة"""
    
    def __init__(self):
        self.min_size = (200, 200)
        self.max_aspect_ratio = 2.0
        self.min_aspect_ratio = 0.5
    
    def validate_image_basic(self, image_file) -> Tuple[bool, str]:
        """
        التحقق الأساسي من الصورة
        
        Args:
            image_file: ملف الصورة
            
        Returns:
            tuple: (هل الصورة صحيحة, رسالة التوضيح)
        """
        try:
            # قراءة الصورة
            image_file.seek(0)
            image = Image.open(image_file)
            
            # فحص الأبعاد
            width, height = image.size
            if width < self.min_size[0] or height < self.min_size[1]:
                return False, f"الصورة صغيرة جداً. الحد الأدنى: {self.min_size[0]}×{self.min_size[1]} بكسل"
            
            # فحص نسبة الأبعاد
            aspect_ratio = width / height
            if aspect_ratio < self.min_aspect_ratio or aspect_ratio > self.max_aspect_ratio:
                return False, "نسبة أبعاد الصورة غير مناسبة للصور الشخصية"
            
            # فحص جودة الصورة
            quality_ok, quality_msg = self._check_image_quality(image)
            if not quality_ok:
                return False, quality_msg
            
            # إعادة تعيين مؤشر الملف
            image_file.seek(0)
            
            return True, "الصورة مقبولة للرفع"
            
        except Exception as e:
            current_app.logger.error(f"خطأ في التحقق من الصورة: {str(e)}")
            image_file.seek(0)
            return False, "خطأ في قراءة الصورة. يرجى التأكد من صحة الملف"
    
    def _check_image_quality(self, image: Image.Image) -> Tuple[bool, str]:
        """
        فحص جودة الصورة الأساسي
        
        Args:
            image: كائن الصورة
            
        Returns:
            tuple: (هل الجودة مقبولة, رسالة)
        """
        try:
            # تحويل إلى RGB إذا لزم الأمر
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # حساب إحصائيات الصورة
            stat = ImageStat.Stat(image)
            
            # فحص السطوع (متوسط قيم RGB)
            brightness = sum(stat.mean) / 3
            if brightness < 30:
                return False, "الصورة مظلمة جداً. يرجى استخدام صورة أكثر إضاءة"
            elif brightness > 220:
                return False, "الصورة مضيئة جداً. يرجى استخدام صورة بإضاءة متوازنة"
            
            # فحص التباين (الانحراف المعياري)
            contrast = sum(stat.stddev) / 3
            if contrast < 15:
                return False, "الصورة تفتقر للوضوح والتباين"
            
            return True, "جودة الصورة مقبولة"
            
        except Exception as e:
            current_app.logger.error(f"خطأ في فحص جودة الصورة: {str(e)}")
            return False, "خطأ في تحليل جودة الصورة"
    
    def get_image_hash(self, image_file) -> str:
        """
        حساب hash للصورة للمقارنة السريعة
        
        Args:
            image_file: ملف الصورة
            
        Returns:
            str: hash الصورة
        """
        try:
            image_file.seek(0)
            content = image_file.read()
            image_file.seek(0)
            return hashlib.md5(content).hexdigest()
        except Exception:
            return ""
    
    def check_duplicate_hash(self, user_id: int, image_hash: str) -> Tuple[bool, str]:
        """
        فحص تكرار الصورة باستخدام hash
        
        Args:
            user_id: معرف المستخدم
            image_hash: hash الصورة
            
        Returns:
            tuple: (هل يوجد تكرار, اسم الصورة المكررة)
        """
        try:
            # مجلد بيانات المستخدم
            data_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'image_hashes')
            os.makedirs(data_dir, exist_ok=True)
            
            user_file = os.path.join(data_dir, f"user_{user_id}_hashes.json")
            
            # قراءة البيانات الموجودة
            if os.path.exists(user_file):
                with open(user_file, 'r', encoding='utf-8') as f:
                    user_hashes = json.load(f)
                
                # البحث عن hash مطابق
                for image_name, stored_hash in user_hashes.items():
                    if stored_hash == image_hash:
                        return True, image_name
            
            return False, ""
            
        except Exception as e:
            current_app.logger.error(f"خطأ في فحص تكرار الصورة: {str(e)}")
            return False, ""
    
    def save_image_hash(self, user_id: int, image_name: str, image_hash: str):
        """
        حفظ hash الصورة
        
        Args:
            user_id: معرف المستخدم
            image_name: اسم الصورة
            image_hash: hash الصورة
        """
        try:
            # مجلد بيانات المستخدم
            data_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'image_hashes')
            os.makedirs(data_dir, exist_ok=True)
            
            user_file = os.path.join(data_dir, f"user_{user_id}_hashes.json")
            
            # قراءة البيانات الموجودة أو إنشاء جديدة
            if os.path.exists(user_file):
                with open(user_file, 'r', encoding='utf-8') as f:
                    user_hashes = json.load(f)
            else:
                user_hashes = {}
            
            # إضافة hash الجديد
            user_hashes[image_name] = image_hash
            
            # حفظ البيانات
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(user_hashes, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            current_app.logger.error(f"خطأ في حفظ hash الصورة: {str(e)}")
    
    def validate_person_image_simple(self, image_file, user_id: int, image_name: str) -> Tuple[bool, str]:
        """
        التحقق المبسط من صورة الشخص
        
        Args:
            image_file: ملف الصورة
            user_id: معرف المستخدم
            image_name: اسم الصورة
            
        Returns:
            tuple: (هل الصورة صحيحة, رسالة التوضيح)
        """
        try:
            # 1. التحقق الأساسي من الصورة
            basic_ok, basic_msg = self.validate_image_basic(image_file)
            if not basic_ok:
                return False, basic_msg
            
            # 2. فحص التكرار باستخدام hash
            image_hash = self.get_image_hash(image_file)
            if image_hash:
                is_duplicate, duplicate_image = self.check_duplicate_hash(user_id, image_hash)
                if is_duplicate:
                    return False, f"هذه الصورة مطابقة للصورة الموجودة: {duplicate_image}. يرجى رفع صورة مختلفة"
                
                # حفظ hash الصورة الجديدة
                self.save_image_hash(user_id, image_name, image_hash)
            
            return True, "تم قبول الصورة بنجاح"
            
        except Exception as e:
            current_app.logger.error(f"خطأ في التحقق من صورة الشخص: {str(e)}")
            return False, "خطأ في معالجة الصورة. يرجى المحاولة مرة أخرى"


# إنشاء instance عام للاستخدام
simple_image_validator = SimpleImageValidator()
"""
خدمة التعرف على الوجوه ومنع تكرار الصور
"""

import face_recognition
import cv2
import numpy as np
from PIL import Image
import io
import os
from flask import current_app
import hashlib
import json
from typing import List, Tuple, Optional, Dict, Any


class FaceRecognitionService:
    """خدمة التعرف على الوجوه والتحقق من صحة الصور"""
    
    def __init__(self):
        self.face_encodings_cache = {}
        self.min_face_size = (50, 50)  # الحد الأدنى لحجم الوجه
        self.similarity_threshold = 0.6  # عتبة التشابه (أقل = أكثر صرامة)
    
    def detect_faces_in_image(self, image_file) -> Tuple[bool, str, List[np.ndarray]]:
        """
        اكتشاف الوجوه في الصورة
        
        Args:
            image_file: ملف الصورة
            
        Returns:
            tuple: (هل توجد وجوه, رسالة, قائمة ترميزات الوجوه)
        """
        try:
            # قراءة الصورة
            image_file.seek(0)
            image = Image.open(image_file)
            
            # تحويل إلى RGB إذا لزم الأمر
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # تحويل إلى numpy array
            image_array = np.array(image)
            
            # اكتشاف مواقع الوجوه
            face_locations = face_recognition.face_locations(image_array)
            
            if not face_locations:
                return False, "لم يتم العثور على أي وجه في الصورة. يرجى رفع صورة شخصية واضحة.", []
            
            # التحقق من حجم الوجوه
            valid_faces = []
            for face_location in face_locations:
                top, right, bottom, left = face_location
                face_width = right - left
                face_height = bottom - top
                
                if face_width >= self.min_face_size[0] and face_height >= self.min_face_size[1]:
                    valid_faces.append(face_location)
            
            if not valid_faces:
                return False, "الوجوه في الصورة صغيرة جداً أو غير واضحة. يرجى رفع صورة أوضح.", []
            
            # استخراج ترميزات الوجوه
            face_encodings = face_recognition.face_encodings(image_array, valid_faces)
            
            if not face_encodings:
                return False, "لا يمكن تحليل الوجوه في الصورة. يرجى رفع صورة أوضح.", []
            
            # إعادة تعيين مؤشر الملف
            image_file.seek(0)
            
            return True, f"تم العثور على {len(face_encodings)} وجه في الصورة.", face_encodings
            
        except Exception as e:
            current_app.logger.error(f"خطأ في اكتشاف الوجوه: {str(e)}")
            image_file.seek(0)
            return False, "خطأ في تحليل الصورة. يرجى المحاولة مرة أخرى.", []
    
    def check_image_quality(self, image_file) -> Tuple[bool, str]:
        """
        فحص جودة الصورة
        
        Args:
            image_file: ملف الصورة
            
        Returns:
            tuple: (هل الجودة مقبولة, رسالة)
        """
        try:
            image_file.seek(0)
            image = Image.open(image_file)
            
            # فحص الأبعاد
            width, height = image.size
            if width < 200 or height < 200:
                return False, "الصورة صغيرة جداً. الحد الأدنى: 200×200 بكسل."
            
            # فحص نسبة العرض إلى الارتفاع
            aspect_ratio = width / height
            if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                return False, "نسبة أبعاد الصورة غير مناسبة. يرجى استخدام صورة بنسبة أبعاد طبيعية."
            
            # تحويل إلى numpy للفحص المتقدم
            image_array = np.array(image.convert('RGB'))
            
            # فحص السطوع
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            brightness = np.mean(gray)
            
            if brightness < 50:
                return False, "الصورة مظلمة جداً. يرجى استخدام صورة أكثر إضاءة."
            elif brightness > 200:
                return False, "الصورة مضيئة جداً. يرجى استخدام صورة بإضاءة متوازنة."
            
            # فحص التباين
            contrast = np.std(gray)
            if contrast < 20:
                return False, "الصورة تفتقر للوضوح. يرجى استخدام صورة أكثر وضوحاً."
            
            image_file.seek(0)
            return True, "جودة الصورة مقبولة."
            
        except Exception as e:
            current_app.logger.error(f"خطأ في فحص جودة الصورة: {str(e)}")
            image_file.seek(0)
            return False, "خطأ في فحص جودة الصورة."
    
    def compare_faces(self, face_encodings1: List[np.ndarray], face_encodings2: List[np.ndarray]) -> bool:
        """
        مقارنة الوجوه بين صورتين
        
        Args:
            face_encodings1: ترميزات الوجوه من الصورة الأولى
            face_encodings2: ترميزات الوجوه من الصورة الثانية
            
        Returns:
            bool: هل الوجوه متشابهة
        """
        try:
            for encoding1 in face_encodings1:
                for encoding2 in face_encodings2:
                    # حساب المسافة بين الوجوه
                    distance = face_recognition.face_distance([encoding1], encoding2)[0]
                    
                    # إذا كانت المسافة أقل من العتبة، فالوجوه متشابهة
                    if distance < self.similarity_threshold:
                        return True
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"خطأ في مقارنة الوجوه: {str(e)}")
            return False
    
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
    
    def save_face_encodings(self, user_id: int, image_name: str, face_encodings: List[np.ndarray]):
        """
        حفظ ترميزات الوجوه لمستخدم معين
        
        Args:
            user_id: معرف المستخدم
            image_name: اسم الصورة
            face_encodings: ترميزات الوجوه
        """
        try:
            # تحويل numpy arrays إلى lists للحفظ في JSON
            encodings_list = [encoding.tolist() for encoding in face_encodings]
            
            # إنشاء مجلد البيانات إذا لم يكن موجوداً
            data_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'face_data')
            os.makedirs(data_dir, exist_ok=True)
            
            # ملف بيانات المستخدم
            user_file = os.path.join(data_dir, f"user_{user_id}_faces.json")
            
            # قراءة البيانات الموجودة أو إنشاء جديدة
            if os.path.exists(user_file):
                with open(user_file, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
            else:
                user_data = {}
            
            # إضافة الترميزات الجديدة
            user_data[image_name] = encodings_list
            
            # حفظ البيانات
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            current_app.logger.error(f"خطأ في حفظ ترميزات الوجوه: {str(e)}")
    
    def load_user_face_encodings(self, user_id: int) -> Dict[str, List[np.ndarray]]:
        """
        تحميل ترميزات الوجوه لمستخدم معين
        
        Args:
            user_id: معرف المستخدم
            
        Returns:
            dict: قاموس يحتوي على ترميزات الوجوه لكل صورة
        """
        try:
            data_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'face_data')
            user_file = os.path.join(data_dir, f"user_{user_id}_faces.json")
            
            if not os.path.exists(user_file):
                return {}
            
            with open(user_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            
            # تحويل lists إلى numpy arrays
            result = {}
            for image_name, encodings_list in user_data.items():
                result[image_name] = [np.array(encoding) for encoding in encodings_list]
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"خطأ في تحميل ترميزات الوجوه: {str(e)}")
            return {}
    
    def check_duplicate_face(self, user_id: int, new_face_encodings: List[np.ndarray]) -> Tuple[bool, str]:
        """
        فحص تكرار الوجه مع الصور الموجودة للمستخدم
        
        Args:
            user_id: معرف المستخدم
            new_face_encodings: ترميزات الوجه الجديد
            
        Returns:
            tuple: (هل يوجد تكرار, اسم الصورة المكررة)
        """
        try:
            existing_encodings = self.load_user_face_encodings(user_id)
            
            for image_name, face_encodings in existing_encodings.items():
                if self.compare_faces(new_face_encodings, face_encodings):
                    return True, image_name
            
            return False, ""
            
        except Exception as e:
            current_app.logger.error(f"خطأ في فحص تكرار الوجه: {str(e)}")
            return False, ""
    
    def validate_person_image(self, image_file, user_id: int, image_name: str) -> Tuple[bool, str]:
        """
        التحقق الشامل من صحة صورة الشخص
        
        Args:
            image_file: ملف الصورة
            user_id: معرف المستخدم
            image_name: اسم الصورة
            
        Returns:
            tuple: (هل الصورة صحيحة, رسالة التوضيح)
        """
        try:
            # 1. فحص جودة الصورة
            quality_ok, quality_msg = self.check_image_quality(image_file)
            if not quality_ok:
                return False, quality_msg
            
            # 2. اكتشاف الوجوه
            faces_found, faces_msg, face_encodings = self.detect_faces_in_image(image_file)
            if not faces_found:
                return False, faces_msg
            
            # 3. فحص التكرار
            is_duplicate, duplicate_image = self.check_duplicate_face(user_id, face_encodings)
            if is_duplicate:
                return False, f"هذا الوجه مشابه للصورة الموجودة: {duplicate_image}. يرجى رفع صورة مختلفة."
            
            # 4. حفظ ترميزات الوجه للمقارنات المستقبلية
            self.save_face_encodings(user_id, image_name, face_encodings)
            
            return True, f"تم قبول الصورة. {faces_msg}"
            
        except Exception as e:
            current_app.logger.error(f"خطأ في التحقق من صورة الشخص: {str(e)}")
            return False, "خطأ في معالجة الصورة. يرجى المحاولة مرة أخرى."


# إنشاء instance عام للاستخدام
face_recognition_service = FaceRecognitionService()
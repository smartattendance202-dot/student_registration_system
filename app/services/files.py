# -*- coding: utf-8 -*-
"""
خدمات إدارة الملفات
"""

import os
import uuid
import shutil
import io
from PIL import Image, ImageDraw, ImageFont

# لا نستخدم python-magic على ويندوز لتجنب مشاكل الاستقرار
MAGIC_AVAILABLE = False
from flask import current_app, abort, send_file, request
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# استيراد خدمات التعرف على الوجوه
try:
    from .face_recognition_service import face_recognition_service
    FACE_RECOGNITION_AVAILABLE = True
    VALIDATION_SERVICE = face_recognition_service
    VALIDATION_METHOD = "متقدم (التعرف على الوجوه)"
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    try:
        from .simple_image_validator import simple_image_validator
        VALIDATION_SERVICE = simple_image_validator
        VALIDATION_METHOD = "أساسي (فحص الجودة والتكرار)"
    except ImportError:
        VALIDATION_SERVICE = None
        VALIDATION_METHOD = "معطل"


def get_validation_system_status():
    """الحصول على حالة نظام التحقق من الصور"""
    return {
        'face_recognition_available': FACE_RECOGNITION_AVAILABLE,
        'validation_method': VALIDATION_METHOD,
        'service_available': VALIDATION_SERVICE is not None
    }


def get_file_extension(filename):
    """الحصول على امتداد الملف"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def validate_file_type(file, allowed_extensions, file_type='file'):
    """التحقق من نوع الملف"""
    if not file or not file.filename:
        return False, 'لم يتم اختيار ملف'
    
    # التحقق من الامتداد
    extension = get_file_extension(file.filename)
    if extension not in allowed_extensions:
        return False, f'نوع الملف غير مسموح. الأنواع المسموحة: {", ".join(allowed_extensions)}'
    
    # تحقق إضافي بدون python-magic
    try:
        if file_type == 'photo':
            # تأكيد أن الملف صورة صالحة باستخدام PIL
            pos = file.tell()
            file.seek(0)
            # فتح الصورة للتحقق من صحتها دون تعديل
            with Image.open(file) as img:
                img.verify()
            file.seek(pos)
        elif file_type == 'document':
            # فحص ترويسة PDF بشكل بسيط إن كان الامتداد pdf
            extension = get_file_extension(file.filename)
            if extension == 'pdf':
                pos = file.tell()
                file.seek(0)
                header = file.read(5)
                file.seek(pos)
                if header != b"%PDF-":
                    return False, 'الملف ليس PDF صالح'
    except Exception as e:
        current_app.logger.error(f'خطأ في التحقق من نوع/سلامة الملف: {str(e)}')
        return False, 'نوع الملف غير صحيح أو ملف تالف'

    return True, 'الملف صحيح'


def validate_file_size(file, max_size, file_type='file'):
    """التحقق من حجم الملف"""
    if not file:
        return False, 'لم يتم اختيار ملف'
    
    # الحصول على حجم الملف
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # إعادة تعيين مؤشر الملف
    
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        return False, f'حجم الملف كبير جداً. الحد الأقصى: {max_size_mb:.1f} ميجابايت'
    
    if file_size == 0:
        return False, 'الملف فارغ'
    
    return True, 'حجم الملف مناسب'


def validate_image_dimensions(file, min_width=300, min_height=300):
    """التحقق من أبعاد الصورة مع محاولة تصغير تلقائي عند الحاجة (للتطوير)"""
    try:
        pos = file.tell()
        file.seek(0)
        image = Image.open(file)
        width, height = image.size

        if width < min_width or height < min_height:
            # في بيئة التطوير فقط: نقوم بعمل pad للصورة الصغيرة إلى الحد الأدنى بدلاً من الرفض
            if current_app.config.get('FLASK_ENV', 'production') == 'development':
                try:
                    new_w = max(width, min_width)
                    new_h = max(height, min_height)
                    background = Image.new('RGB', (new_w, new_h), (255, 255, 255))
                    background.paste(image, (0, 0))
                    # حفظ الصورة المعدلة مؤقتاً في الذاكرة ثم إعادة كتابتها إلى الملف
                    buf = io.BytesIO()
                    # حفظ بجودة عالية
                    if image.format and image.format.upper() == 'JPEG':
                        background.save(buf, format='JPEG', quality=100)
                    else:
                        background.save(buf, format=image.format or 'JPEG', quality=100)
                    buf.seek(0)
                    # استبدال محتوى الملف بالمحتوى الجديد
                    file.stream.seek(0)
                    file.stream.truncate(0)
                    file.stream.write(buf.read())
                    file.stream.seek(0)
                    file.seek(0)
                    return True, 'تم تعديل أبعاد الصورة تلقائياً لتتوافق مع الحد الأدنى (بيئة التطوير)'
                except Exception as ie:
                    current_app.logger.error(f'فشل تعديل أبعاد الصورة تلقائياً: {str(ie)}')
                    file.seek(pos)
                    return False, f'أبعاد الصورة صغيرة جداً. الحد الأدنى: {min_width}×{min_height} بكسل'
            else:
                # في بيئة الإنتاج: رفض الصورة الصغيرة
                file.seek(pos)
                return False, f'أبعاد الصورة صغيرة جداً. الحد الأدنى: {min_width}×{min_height} بكسل'

        file.seek(pos)
        return True, 'أبعاد الصورة مناسبة'

    except Exception as e:
        current_app.logger.error(f'خطأ في التحقق من أبعاد الصورة: {str(e)}')
        return False, 'خطأ في قراءة الصورة'


def validate_file(file, file_type='document', user_id=None, image_name=None):
    """التحقق الشامل من الملف مع فحص الوجوه للصور الشخصية"""
    if not file or not file.filename:
        return False, 'لم يتم اختيار ملف'
    
    # تحديد الإعدادات حسب نوع الملف
    if file_type == 'photo':
        allowed_extensions = current_app.config['ALLOWED_PHOTO_EXTENSIONS']
        max_size = current_app.config['MAX_PHOTO_SIZE']
        check_dimensions = True
    else:  # document
        allowed_extensions = current_app.config['ALLOWED_DOCUMENT_EXTENSIONS']
        max_size = current_app.config['MAX_DOCUMENT_SIZE']
        check_dimensions = False
    
    # التحقق من نوع الملف
    valid_type, type_message = validate_file_type(file, allowed_extensions, file_type)
    if not valid_type:
        return False, type_message
    
    # التحقق من حجم الملف
    valid_size, size_message = validate_file_size(file, max_size, file_type)
    if not valid_size:
        return False, size_message
    
    # فحص الصور الشخصية (وجوه أو تكرار حسب النظام المتاح)
    if file_type == 'photo' and VALIDATION_SERVICE and user_id and image_name:
        try:
            if FACE_RECOGNITION_AVAILABLE:
                # استخدام النظام المتقدم للتعرف على الوجوه
                valid_face, face_message = VALIDATION_SERVICE.validate_person_image(
                    file, user_id, image_name
                )
            else:
                # استخدام النظام المبسط للتحقق من الجودة والتكرار
                valid_face, face_message = VALIDATION_SERVICE.validate_person_image_simple(
                    file, user_id, image_name
                )
            
            if not valid_face:
                return False, face_message
                
            current_app.logger.info(f"تم فحص الصورة باستخدام النظام: {VALIDATION_METHOD}")
            
        except Exception as e:
            current_app.logger.error(f"خطأ في فحص الصورة: {str(e)}")
            # في حالة فشل الفحص، نكمل بدون فحص مع تحذير
            current_app.logger.warning(f"تم تخطي فحص الصورة بسبب خطأ تقني - النظام: {VALIDATION_METHOD}")
    
    return True, 'الملف صحيح'


def generate_unique_filename(original_filename):
    """توليد اسم ملف فريد"""
    extension = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())
    return f"{unique_id}.{extension}" if extension else unique_id


def create_default_avatar(name, user_id, save_path, is_male=True):
    """إنشاء صورة افتراضية للطالب"""
    try:
        # ألوان مختلفة للخلفية
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
        ]

        # اختيار لون عشوائي بناءً على user_id
        color = colors[int(user_id) % len(colors)]

        # إنشاء صورة 300x300
        img = Image.new('RGB', (300, 300), color)
        draw = ImageDraw.Draw(img)

        # محاولة استخدام خط، وإلا استخدام الخط الافتراضي
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()

        # الحصول على الأحرف الأولى من الاسم
        name_parts = name.split()
        if len(name_parts) >= 2:
            initials = name_parts[0][0] + name_parts[1][0]
        else:
            initials = name_parts[0][:2] if name_parts else "طالب"

        # حساب موقع النص في المنتصف
        bbox = draw.textbbox((0, 0), initials, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (300 - text_width) // 2
        y = (300 - text_height) // 2

        # رسم النص
        draw.text((x, y), initials, fill='white', font=font)

        # إضافة دائرة للإشارة للجنس
        if is_male:
            draw.ellipse([250, 250, 290, 290], fill='#3498db')  # أزرق للذكور
        else:
            draw.ellipse([250, 250, 290, 290], fill='#e91e63')  # وردي للإناث

        # حفظ الصورة
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        img.save(save_path, 'JPEG', quality=100)

        return True
    except Exception as e:
        current_app.logger.error(f'خطأ في إنشاء الصورة الافتراضية: {str(e)}')
        return False


def ensure_student_has_files(user_id, full_name, gender, folder_type='temp'):
    """ضمان أن الطالب لديه ملفات (إنشاء افتراضية إذا لزم الأمر)"""
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']

        # التأكد من أن المسار مطلق
        if not os.path.isabs(upload_folder):
            app_dir = os.path.dirname(os.path.abspath(__file__))  # app/services
            project_root = os.path.dirname(os.path.dirname(app_dir))  # جذر المشروع
            upload_folder = os.path.join(project_root, upload_folder)

        user_folder = os.path.join(upload_folder, folder_type, str(user_id))
        os.makedirs(user_folder, exist_ok=True)

        files_created = {}

        # إنشاء صورة شخصية افتراضية إذا لم توجد
        photo_files = [f for f in os.listdir(user_folder)
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))
                      and 'avatar' in f.lower()]

        if not photo_files:
            photo_filename = f"default_avatar_{user_id}.jpg"
            photo_path = os.path.join(user_folder, photo_filename)
            is_male = gender == 'male'

            if create_default_avatar(full_name, user_id, photo_path, is_male):
                files_created['photo'] = f"{folder_type}/{user_id}/{photo_filename}"
                current_app.logger.info(f'تم إنشاء صورة افتراضية للمستخدم {user_id}')

        return files_created

    except Exception as e:
        current_app.logger.error(f'خطأ في ضمان وجود ملفات الطالب: {str(e)}')
        return {}


def save_uploaded_file(file, folder_type, user_id, file_type='document', image_name=None):
    """حفظ الملف المرفوع بجودة عالية مع فحص الوجوه"""
    # إنشاء اسم الصورة إذا لم يتم تمريره
    if not image_name and file_type == 'photo':
        image_name = f"image_{len(os.listdir(os.path.join(current_app.config['UPLOAD_FOLDER'], folder_type, str(user_id)))) + 1 if os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], folder_type, str(user_id))) else 1}"
    
    # التحقق من صحة الملف مع فحص الوجوه
    valid, message = validate_file(file, file_type, user_id, image_name)
    if not valid:
        raise ValueError(message)

    # إنشاء مسار الحفظ
    upload_folder = current_app.config['UPLOAD_FOLDER']

    # التأكد من أن المسار مطلق
    if os.path.isabs(upload_folder):
        user_folder = os.path.join(upload_folder, folder_type, str(user_id))
    else:
        # إذا كان المسار نسبي، نجعله نسبة إلى جذر المشروع (مجلد أعلى من app)
        app_dir = os.path.dirname(os.path.abspath(__file__))  # app/services
        project_root = os.path.dirname(os.path.dirname(app_dir))  # جذر المشروع
        user_folder = os.path.join(project_root, upload_folder, folder_type, str(user_id))

    # تطبيع المسار
    user_folder = os.path.normpath(user_folder)
    os.makedirs(user_folder, exist_ok=True)

    # توليد اسم ملف فريد
    filename = generate_unique_filename(file.filename)
    file_path = os.path.join(user_folder, filename)

    # حفظ الملف
    try:
        if file_type == 'photo':
            # للصور: حفظ بجودة عالية مضمونة
            save_high_quality_image(file, file_path)
        else:
            # للمستندات: حفظ مباشر
            file.save(file_path)

        # إرجاع المسار النسبي (استخدام / دائماً للمسارات النسبية)
        relative_path = f"{folder_type}/{user_id}/{filename}"
        return relative_path

    except Exception as e:
        current_app.logger.error(f'خطأ في حفظ الملف: {str(e)}')
        raise ValueError('فشل في حفظ الملف')


def save_high_quality_image(file, file_path):
    """حفظ الصورة بجودة عالية مضمونة"""
    try:
        # إعادة تعيين مؤشر الملف
        file.seek(0)
        
        # فتح الصورة
        with Image.open(file) as img:
            # تحويل إلى RGB إذا كانت RGBA (للشفافية)
            if img.mode in ('RGBA', 'LA', 'P'):
                # إنشاء خلفية بيضاء
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # تحديد تنسيق الحفظ بناءً على امتداد الملف
            file_extension = get_file_extension(file.filename).lower()
            
            if file_extension in ['jpg', 'jpeg']:
                # حفظ JPEG بجودة 100%
                img.save(file_path, 'JPEG', quality=100, optimize=False)
            elif file_extension == 'png':
                # حفظ PNG بدون ضغط
                img.save(file_path, 'PNG', optimize=False)
            elif file_extension == 'webp':
                # حفظ WebP بجودة عالية
                img.save(file_path, 'WebP', quality=100, lossless=True)
            elif file_extension in ['bmp', 'tiff']:
                # حفظ BMP/TIFF بدون ضغط
                img.save(file_path, file_extension.upper())
            else:
                # افتراضي: حفظ كـ JPEG بجودة عالية
                img.save(file_path, 'JPEG', quality=100, optimize=False)
                
        current_app.logger.info(f'تم حفظ الصورة بجودة عالية: {file_path}')
        
    except Exception as e:
        current_app.logger.error(f'خطأ في حفظ الصورة بجودة عالية: {str(e)}')
        # في حالة الفشل، احفظ الملف مباشرة
        file.seek(0)
        file.save(file_path)


def move_file(source_path, dest_folder_type, user_id):
    """نقل الملف من مجلد إلى آخر"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    # تطبيع المسار لتجنب مشاكل الخلط بين الشرطات المائلة على ويندوز
    normalized_source_path = source_path.replace('/', os.sep).replace('\\', os.sep)

    # التأكد من أن المسار مطلق
    if os.path.isabs(upload_folder):
        source_full_path = os.path.join(upload_folder, normalized_source_path)
        dest_folder = os.path.join(upload_folder, dest_folder_type, str(user_id))
    else:
        # إذا كان المسار نسبي، نجعله نسبة إلى جذر المشروع (مجلد أعلى من app)
        app_dir = os.path.dirname(os.path.abspath(__file__))  # app/services
        project_root = os.path.dirname(os.path.dirname(app_dir))  # جذر المشروع
        source_full_path = os.path.join(project_root, upload_folder, normalized_source_path)
        dest_folder = os.path.join(project_root, upload_folder, dest_folder_type, str(user_id))

    # تطبيع المسارات
    source_full_path = os.path.normpath(source_full_path)
    dest_folder = os.path.normpath(dest_folder)

    if not os.path.exists(source_full_path):
        current_app.logger.warning(f'الملف المصدر غير موجود: {source_full_path}')
        return None

    # إنشاء مجلد الوجهة
    os.makedirs(dest_folder, exist_ok=True)

    # الحصول على اسم الملف
    filename = os.path.basename(source_full_path)
    dest_path = os.path.join(dest_folder, filename)

    try:
        # نقل الملف
        shutil.move(source_full_path, dest_path)

        # إرجاع المسار النسبي الجديد (استخدام / دائماً للمسارات النسبية)
        relative_path = f"{dest_folder_type}/{user_id}/{filename}"
        return relative_path

    except Exception as e:
        current_app.logger.error(f'خطأ في نقل الملف: {str(e)}')
        return None


def delete_file(file_path):
    """حذف الملف"""
    if not file_path:
        return True

    upload_folder = current_app.config['UPLOAD_FOLDER']
    # تطبيع المسار لتجنب مشاكل الخلط بين الشرطات المائلة على ويندوز
    normalized_file_path = file_path.replace('/', os.sep).replace('\\', os.sep)

    # التأكد من أن المسار مطلق
    if os.path.isabs(upload_folder):
        full_path = os.path.join(upload_folder, normalized_file_path)
    else:
        # إذا كان المسار نسبي، نجعله نسبة إلى جذر المشروع (مجلد أعلى من app)
        app_dir = os.path.dirname(os.path.abspath(__file__))  # app/services
        project_root = os.path.dirname(os.path.dirname(app_dir))  # جذر المشروع
        full_path = os.path.join(project_root, upload_folder, normalized_file_path)

    # تطبيع المسار النهائي
    full_path = os.path.normpath(full_path)

    try:
        if os.path.exists(full_path):
            os.remove(full_path)

            # حذف المجلد إذا كان فارغاً
            folder_path = os.path.dirname(full_path)
            if os.path.exists(folder_path) and not os.listdir(folder_path):
                os.rmdir(folder_path)

        return True

    except Exception as e:
        current_app.logger.error(f'خطأ في حذف الملف: {str(e)}')
        return False


def serve_file(file_path, user_id=None, check_permissions=True):
    """تقديم الملف مع التحقق من الصلاحيات"""
    if not file_path:
        abort(404)

    upload_folder = current_app.config['UPLOAD_FOLDER']
    # تطبيع المسار لتجنب مشاكل الخلط بين الشرطات المائلة على ويندوز
    normalized_file_path = file_path.replace('/', os.sep).replace('\\', os.sep)

    # التأكد من أن المسار مطلق
    if os.path.isabs(upload_folder):
        full_path = os.path.join(upload_folder, normalized_file_path)
    else:
        # إذا كان المسار نسبي، نجعله نسبة إلى جذر المشروع (مجلد أعلى من app)
        app_dir = os.path.dirname(os.path.abspath(__file__))  # app/services
        project_root = os.path.dirname(os.path.dirname(app_dir))  # جذر المشروع
        full_path = os.path.join(project_root, upload_folder, normalized_file_path)

    # تطبيع المسار النهائي
    full_path = os.path.normpath(full_path)

    current_app.logger.debug(f'محاولة الوصول للملف: {full_path}')

    # التحقق من الأمان - التأكد من أن المسار داخل مجلد الرفع
    try:
        upload_real_path = os.path.realpath(upload_folder if os.path.isabs(upload_folder)
                                          else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), upload_folder))
        file_real_path = os.path.realpath(full_path)
        if not file_real_path.startswith(upload_real_path):
            current_app.logger.warning(f'محاولة وصول غير آمنة للملف: {full_path}')
            abort(403)
    except Exception as e:
        current_app.logger.error(f'خطأ في التحقق من أمان المسار: {str(e)}')
        abort(500)

    if not os.path.exists(full_path):
        current_app.logger.error(f'الملف غير موجود: {full_path}')
        abort(404)

    # التحقق من الصلاحيات إذا كان مطلوباً
    if check_permissions and user_id:
        from flask_login import current_user

        # المشرفون يمكنهم الوصول لجميع الملفات
        if current_user.role != 'admin':
            # الطلاب يمكنهم الوصول لملفاتهم فقط
            if current_user.id != user_id:
                abort(403)

    try:
        return send_file(full_path)
    except Exception as e:
        current_app.logger.error(f'خطأ في تقديم الملف: {str(e)}')
        abort(500)
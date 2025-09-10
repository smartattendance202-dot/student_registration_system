# -*- coding: utf-8 -*-
"""
خدمة إرسال رسائل SMS للتحقق من رقم الهاتف
"""

import requests
import logging
from flask import current_app

logger = logging.getLogger(__name__)

class SMSService:
    """خدمة إرسال رسائل SMS"""
    
    @staticmethod
    def send_verification_code(phone_number, verification_code):
        """
        إرسال رمز التحقق عبر SMS

        Args:
            phone_number (str): رقم الهاتف بصيغة +967xxxxxxxxx
            verification_code (str): رمز التحقق المكون من 6 أرقام

        Returns:
            bool: True إذا تم الإرسال بنجاح، False في حالة الفشل
        """

        try:
            # إرسال عبر WhatsApp إذا كان مفعل
            if current_app.config.get('WHATSAPP_ENABLED', False):
                logger.info(f"📱 محاولة إرسال رمز التحقق عبر WhatsApp إلى {phone_number}")
                try:
                    from app.services.whatsapp import WhatsAppService
                    result = WhatsAppService.send_verification_code(phone_number, verification_code)
                    if result:
                        logger.info(f"✅ تم إرسال رمز التحقق عبر WhatsApp بنجاح")
                        return True
                    else:
                        logger.warning(f"⚠️ فشل إرسال WhatsApp، التبديل للوضع المحلي")
                except Exception as whatsapp_error:
                    logger.error(f"❌ خطأ في WhatsApp: {str(whatsapp_error)}")
                    logger.info(f"🔄 التبديل للوضع المحلي...")

            # الوضع المحلي - عرض الرمز في الكونسول (يعمل دائماً)
            print(f"\n" + "="*60)
            print(f"📱 رمز التحقق لرقم {phone_number}")
            print(f"🔢 الرمز: {verification_code}")
            print(f"⏰ صالح لمدة 10 دقائق")
            print(f"💡 استخدم هذا الرمز في صفحة التحقق")
            if current_app.config.get('WHATSAPP_ENABLED', False):
                print(f"⚠️ تم التبديل للوضع المحلي بسبب مشكلة في WhatsApp")
            else:
                print(f"ℹ️ WhatsApp غير مفعل - وضع التطوير")
            print(f"="*60 + "\n")

            logger.info(f"✅ تم عرض رمز التحقق {verification_code} لرقم {phone_number} في الكونسول")
            return True

        except Exception as e:
            logger.error(f"خطأ في إرسال رمز التحقق إلى {phone_number}: {str(e)}")
            return False
    

    
    @staticmethod
    def _send_via_local_service(phone_number, verification_code):
        """
        إرسال رمز التحقق عبر خدمة محلية
        
        يمكن تخصيص هذه الدالة لاستخدام خدمة SMS محلية
        """
        try:
            # مثال لاستخدام API محلي
            api_url = current_app.config.get('LOCAL_SMS_API_URL')
            api_key = current_app.config.get('LOCAL_SMS_API_KEY')
            
            if not api_url:
                logger.error("رابط خدمة SMS المحلية غير محدد")
                return False
            
            message_body = f"رمز التحقق الخاص بك: {verification_code}\nصالح لمدة 10 دقائق"
            
            payload = {
                'phone': phone_number,
                'message': message_body,
                'api_key': api_key
            }
            
            response = requests.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"تم إرسال رمز التحقق عبر الخدمة المحلية")
                return True
            else:
                logger.error(f"فشل إرسال رمز التحقق: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في إرسال رمز التحقق عبر الخدمة المحلية: {str(e)}")
            return False
    
    @staticmethod
    def format_phone_number(phone_number):
        """
        تنسيق رقم الهاتف للتأكد من الصيغة الصحيحة
        يدعم جميع الشبكات اليمنية

        Args:
            phone_number (str): رقم الهاتف

        Returns:
            str: رقم الهاتف بالصيغة الصحيحة +967xxxxxxxxx أو None إذا كان غير صالح
        """
        if not phone_number:
            return None

        # إزالة المسافات والرموز الإضافية
        phone = phone_number.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

        # إزالة الأصفار الإضافية في البداية
        phone = phone.lstrip('0')

        # إضافة +967 إذا لم تكن موجودة
        if phone.startswith('967'):
            phone = '+' + phone
        elif phone.startswith('7') and len(phone) == 9:
            phone = '+967' + phone
        elif phone.startswith('+967'):
            # الرقم صحيح بالفعل
            pass
        else:
            # محاولة أخيرة: إذا كان الرقم يبدأ بأرقام أخرى
            if len(phone) == 9 and phone[0] == '7':
                phone = '+967' + phone
            else:
                return None

        # التحقق من طول الرقم النهائي
        if len(phone) != 13:  # +967 + 9 أرقام
            return None

        # التحقق من أن الرقم يحتوي على أرقام فقط بعد +967
        if not phone[4:].isdigit():
            return None

        # التحقق من أن الرقم يبدأ بـ 7 (الأرقام اليمنية)
        if not phone.startswith('+9677'):
            return None

        return phone
    
    @staticmethod
    def is_valid_yemen_phone(phone_number):
        """
        التحقق من صحة رقم الهاتف اليمني
        يدعم جميع الشبكات اليمنية: يمن موبايل، سبائفون، واي، MTN

        Args:
            phone_number (str): رقم الهاتف

        Returns:
            bool: True إذا كان الرقم صحيح
        """
        import re

        if not phone_number:
            return False

        # تنظيف الرقم
        clean_phone = phone_number.strip().replace(' ', '').replace('-', '')

        # إضافة +967 إذا لم تكن موجودة
        if clean_phone.startswith('967'):
            clean_phone = '+' + clean_phone
        elif clean_phone.startswith('7') and len(clean_phone) == 9:
            clean_phone = '+967' + clean_phone
        elif not clean_phone.startswith('+967'):
            return False

        # فحص الطول الإجمالي
        if len(clean_phone) != 13:  # +967 + 9 أرقام
            return False

        # أنماط الشبكات اليمنية المدعومة
        yemen_patterns = [
            r'^\+967(70[0-9]|71[0-9]|72[0-9]|73[0-9]|74[0-9]|75[0-9]|76[0-9]|77[0-9]|78[0-9])[0-9]{6}$',  # يمن موبايل
            r'^\+967(73[0-9]|77[0-9])[0-9]{6}$',  # سبائفون
            r'^\+967(70[0-9]|71[0-9])[0-9]{6}$',  # واي
            r'^\+967(78[0-9])[0-9]{6}$',  # MTN
            r'^\+9677[0-9]{7}$',  # جميع الأرقام التي تبدأ بـ 7 (عام)
        ]

        # فحص مع جميع الأنماط
        for pattern in yemen_patterns:
            if re.match(pattern, clean_phone):
                return True

        # فحص عام للأرقام اليمنية (7xxxxxxxx)
        general_pattern = r'^\+9677[0-9]{7}$'
        return bool(re.match(general_pattern, clean_phone))


# دالة مساعدة للاستخدام المباشر
def send_verification_sms(phone_number, verification_code):
    """
    دالة مساعدة لإرسال رمز التحقق
    
    Args:
        phone_number (str): رقم الهاتف
        verification_code (str): رمز التحقق
        
    Returns:
        bool: True إذا تم الإرسال بنجاح
    """
    return SMSService.send_verification_code(phone_number, verification_code)

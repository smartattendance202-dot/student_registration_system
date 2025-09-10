# -*- coding: utf-8 -*-
"""
خدمة إرسال رسائل WhatsApp Business API
"""

import requests
import logging
from flask import current_app

logger = logging.getLogger(__name__)

class WhatsAppService:
    """خدمة إرسال رسائل WhatsApp Business"""
    
    @staticmethod
    def send_verification_code(phone_number, verification_code):
        """
        إرسال رمز التحقق عبر WhatsApp Business API
        
        Args:
            phone_number (str): رقم الهاتف بصيغة +967xxxxxxxxx
            verification_code (str): رمز التحقق المكون من 6 أرقام
            
        Returns:
            bool: True إذا تم الإرسال بنجاح، False في حالة الفشل
        """
        try:
            # الحصول على إعدادات WhatsApp من التكوين
            access_token = current_app.config.get('WHATSAPP_ACCESS_TOKEN')
            phone_number_id = current_app.config.get('WHATSAPP_PHONE_NUMBER_ID')
            
            if not access_token or not phone_number_id:
                logger.error("إعدادات WhatsApp غير مكتملة")
                return False
            
            # تنظيف رقم الهاتف (إزالة + واستبدالها بـ 00)
            clean_phone = phone_number.replace('+', '')
            
            # رسالة رمز التحقق
            message_text = f"""🔐 رمز التحقق الخاص بك

الرمز: *{verification_code}*

⏰ صالح لمدة 10 دقائق فقط
🔒 لا تشارك هذا الرمز مع أي شخص

نظام تسجيل الطلاب"""
            
            # إعداد البيانات للإرسال
            url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": clean_phone,
                "type": "text",
                "text": {
                    "body": message_text
                }
            }
            
            # إرسال الطلب
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"✅ تم إرسال رمز التحقق عبر WhatsApp إلى {phone_number}")
                logger.info(f"معرف الرسالة: {response_data.get('messages', [{}])[0].get('id', 'غير محدد')}")
                return True
            else:
                logger.error(f"❌ فشل إرسال رمز التحقق عبر WhatsApp: {response.status_code}")
                logger.error(f"الاستجابة: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("❌ انتهت مهلة الاتصال مع WhatsApp API")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("❌ خطأ في الاتصال مع WhatsApp API")
            return False
        except Exception as e:
            logger.error(f"❌ خطأ غير متوقع في إرسال رمز التحقق عبر WhatsApp: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_message(phone_number, user_name=None):
        """
        إرسال رسالة ترحيب للمستخدم الجديد
        
        Args:
            phone_number (str): رقم الهاتف
            user_name (str): اسم المستخدم (اختياري)
            
        Returns:
            bool: True إذا تم الإرسال بنجاح
        """
        try:
            access_token = current_app.config.get('WHATSAPP_ACCESS_TOKEN')
            phone_number_id = current_app.config.get('WHATSAPP_PHONE_NUMBER_ID')
            
            if not access_token or not phone_number_id:
                return False
            
            clean_phone = phone_number.replace('+', '')
            
            welcome_text = f"""🎉 مرحباً بك في نظام تسجيل الطلاب!

{"عزيزي " + user_name if user_name else "عزيزي الطالب"}

تم تأكيد رقم هاتفك بنجاح ✅

يمكنك الآن:
📝 تعبئة استمارة التسجيل
📄 رفع المستندات المطلوبة
📊 متابعة حالة طلبك

نتمنى لك التوفيق! 🌟"""
            
            url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": clean_phone,
                "type": "text",
                "text": {
                    "body": welcome_text
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"✅ تم إرسال رسالة الترحيب عبر WhatsApp إلى {phone_number}")
                return True
            else:
                logger.error(f"❌ فشل إرسال رسالة الترحيب: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال رسالة الترحيب: {str(e)}")
            return False
    
    @staticmethod
    def test_connection():
        """
        اختبار الاتصال مع WhatsApp Business API
        
        Returns:
            dict: نتيجة الاختبار
        """
        try:
            access_token = current_app.config.get('WHATSAPP_ACCESS_TOKEN')
            phone_number_id = current_app.config.get('WHATSAPP_PHONE_NUMBER_ID')
            
            if not access_token or not phone_number_id:
                return {
                    'success': False,
                    'message': 'إعدادات WhatsApp غير مكتملة'
                }
            
            # اختبار الحصول على معلومات رقم الهاتف
            url = f"https://graph.facebook.com/v18.0/{phone_number_id}"
            
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'message': 'الاتصال مع WhatsApp API ناجح',
                    'phone_number': data.get('display_phone_number', 'غير محدد'),
                    'status': data.get('verified_name', 'غير محدد')
                }
            else:
                return {
                    'success': False,
                    'message': f'فشل الاتصال: {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في الاختبار: {str(e)}'
            }
# -*- coding: utf-8 -*-
"""
اختبار بسيط للتحقق من أرقام الجوال
"""

def test_phone_validation():
    """اختبار منطق التحقق من أرقام الجوال"""
    
    def validate_yemeni_phone(phone_data):
        """محاكاة دالة التحقق"""
        if not phone_data:
            return False, "رقم الجوال مطلوب"
        
        # تنظيف الرقم
        clean_phone = phone_data.strip().replace(' ', '').replace('-', '')
        
        # إزالة رمز الدولة إذا كان موجوداً
        if clean_phone.startswith('+967'):
            clean_phone = clean_phone[4:]
        elif clean_phone.startswith('967'):
            clean_phone = clean_phone[3:]
        elif clean_phone.startswith('00967'):
            clean_phone = clean_phone[5:]
        
        # التحقق من صحة الرقم اليمني (يبدأ بـ 7 ويكون 9 أرقام)
        if not (clean_phone.startswith('7') and len(clean_phone) == 9 and clean_phone.isdigit()):
            return False, 'رقم الجوال يجب أن يبدأ بـ 7 ويكون 9 أرقام (مثال: 712345678)'
        
        # إضافة رمز اليمن
        final_phone = '+967' + clean_phone
        return True, final_phone
    
    print("🧪 اختبار التحقق من أرقام الجوال اليمنية...")
    print("="*60)
    
    # أرقام للاختبار
    test_phones = [
        "773397089",    # صحيح
        "777679136",    # صحيح
        "712345678",    # صحيح
        "+967773397089", # صحيح مع رمز الدولة
        "967777679136",  # صحيح مع رمز الدولة
        "673397089",     # خطأ - لا يبدأ بـ 7
        "77339708",      # خطأ - أقل من 9 أرقام
        "7733970899",    # خطأ - أكثر من 9 أرقام
        "abc123456",     # خطأ - يحتوي على أحرف
        "812345678",     # خطأ - يبدأ بـ 8
        "",              # خطأ - فارغ
    ]
    
    for phone in test_phones:
        is_valid, result = validate_yemeni_phone(phone)
        status = "✅" if is_valid else "❌"
        print(f"{status} '{phone}' → {result}")
    
    print("="*60)
    print("✅ انتهى الاختبار")

if __name__ == "__main__":
    test_phone_validation()
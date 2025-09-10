# -*- coding: utf-8 -*-
"""
اختبار التحقق من أرقام الجوال اليمنية
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.forms.application import ApplicationForm

def test_phone_validation():
    """اختبار التحقق من أرقام الجوال"""
    app = create_app()
    
    with app.app_context():
        print("🧪 اختبار التحقق من أرقام الجوال اليمنية...")
        print("="*60)
        
        # أرقام صحيحة للاختبار
        valid_phones = [
            "773397089",
            "777679136", 
            "712345678",
            "770123456",
            "771234567",
            "772345678",
            "773456789",
            "774567890",
            "775678901",
            "776789012",
            "777890123",
            "778901234",
            "779012345"
        ]
        
        # أرقام غير صحيحة للاختبار
        invalid_phones = [
            "673397089",  # لا يبدأ بـ 7
            "77339708",   # أقل من 9 أرقام
            "7733970899", # أكثر من 9 أرقام
            "abc123456",  # يحتوي على أحرف
            "812345678",  # يبدأ بـ 8
            "612345678",  # يبدأ بـ 6
            "",           # فارغ
            "7123456",    # قصير جداً
        ]
        
        print("✅ اختبار الأرقام الصحيحة:")
        print("-"*40)
        
        for phone in valid_phones:
            form = ApplicationForm()
            form.phone.data = phone
            
            try:
                form.validate_phone(form.phone)
                print(f"✅ {phone} → {form.phone.data}")
            except Exception as e:
                print(f"❌ {phone} → خطأ: {str(e)}")
        
        print(f"\n❌ اختبار الأرقام غير الصحيحة:")
        print("-"*40)
        
        for phone in invalid_phones:
            form = ApplicationForm()
            form.phone.data = phone
            
            try:
                form.validate_phone(form.phone)
                print(f"⚠️ {phone} → تم قبوله (يجب أن يرفض!)")
            except Exception as e:
                print(f"✅ {phone} → رُفض بشكل صحيح: {str(e)}")
        
        print(f"\n🧪 اختبار أرقام جوال ولي الأمر:")
        print("-"*40)
        
        for phone in ["773397089", "777679136"]:
            form = ApplicationForm()
            form.guardian_phone.data = phone
            
            try:
                form.validate_guardian_phone(form.guardian_phone)
                print(f"✅ ولي الأمر {phone} → {form.guardian_phone.data}")
            except Exception as e:
                print(f"❌ ولي الأمر {phone} → خطأ: {str(e)}")
        
        print("="*60)
        print("✅ انتهى الاختبار")

if __name__ == "__main__":
    test_phone_validation()
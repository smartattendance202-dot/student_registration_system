#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت تثبيت مكتبات التعرف على الوجوه
"""

import subprocess
import sys
import os

def install_package(package):
    """تثبيت حزمة Python"""
    try:
        print(f"جاري تثبيت {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ تم تثبيت {package} بنجاح")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ فشل في تثبيت {package}: {e}")
        return False

def check_package(package):
    """فحص وجود حزمة"""
    try:
        __import__(package)
        print(f"✅ {package} موجودة بالفعل")
        return True
    except ImportError:
        print(f"⚠️ {package} غير موجودة")
        return False

def main():
    print("🚀 بدء تثبيت مكتبات التعرف على الوجوه...")
    print("=" * 50)
    
    # قائمة المكتبات المطلوبة
    packages = [
        ("numpy", "numpy==1.24.3"),
        ("cv2", "opencv-python==4.8.1.78"),
        ("face_recognition", "face-recognition==1.3.0")
    ]
    
    success_count = 0
    total_count = len(packages)
    
    for import_name, install_name in packages:
        print(f"\n📦 فحص {import_name}...")
        
        if not check_package(import_name):
            if install_package(install_name):
                success_count += 1
            else:
                print(f"💡 نصيحة: قد تحتاج لتثبيت Visual Studio Build Tools لـ {install_name}")
        else:
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 النتائج: {success_count}/{total_count} مكتبات تم تثبيتها بنجاح")
    
    if success_count == total_count:
        print("🎉 تم تثبيت جميع المكتبات بنجاح!")
        print("✅ نظام التعرف على الوجوه جاهز للاستخدام")
        
        # اختبار سريع
        print("\n🧪 اختبار سريع...")
        try:
            import face_recognition
            import cv2
            import numpy as np
            print("✅ جميع المكتبات تعمل بشكل صحيح")
        except Exception as e:
            print(f"⚠️ خطأ في الاختبار: {e}")
    else:
        print("⚠️ بعض المكتبات لم يتم تثبيتها")
        print("💡 قد تحتاج لتثبيت المتطلبات التالية:")
        print("   - Visual Studio Build Tools")
        print("   - CMake")
        print("   - dlib")
    
    print("\n📚 للمزيد من المساعدة، راجع:")
    print("   - https://github.com/ageitgey/face_recognition#installation")
    print("   - FACE_RECOGNITION_INTEGRATION.md")

if __name__ == "__main__":
    main()
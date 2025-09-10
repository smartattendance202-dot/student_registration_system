# -*- coding: utf-8 -*-
"""
سكريبت لتحديث العمر للطلبات الموجودة
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import Application
from app.extensions import db

def update_existing_ages():
    """تحديث العمر للطلبات الموجودة"""
    app = create_app()
    
    with app.app_context():
        print("🔄 بدء تحديث العمر للطلبات الموجودة...")
        print("="*60)
        
        # البحث عن جميع الطلبات التي لا تحتوي على عمر
        applications = Application.query.filter(Application.age.is_(None)).all()
        
        if not applications:
            print("✅ جميع الطلبات تحتوي على العمر بالفعل")
            return
        
        print(f"📋 عدد الطلبات التي تحتاج تحديث: {len(applications)}")
        print("-"*60)
        
        updated_count = 0
        error_count = 0
        
        for i, application in enumerate(applications, 1):
            try:
                # حساب وحفظ العمر
                calculated_age = application.calculate_and_save_age()
                
                if calculated_age is not None:
                    print(f"{i:3d}. ✅ {application.full_name} - العمر: {calculated_age} سنة")
                    updated_count += 1
                else:
                    print(f"{i:3d}. ⚠️ {application.full_name} - لا يمكن حساب العمر")
                    error_count += 1
                    
            except Exception as e:
                print(f"{i:3d}. ❌ {application.full_name} - خطأ: {str(e)}")
                error_count += 1
        
        # حفظ التغييرات
        try:
            db.session.commit()
            print(f"\n" + "="*60)
            print(f"📊 نتائج التحديث:")
            print(f"   ✅ تم تحديث: {updated_count} طلب")
            print(f"   ❌ أخطاء: {error_count} طلب")
            print(f"   📈 إجمالي: {len(applications)} طلب")
            print(f"\n✅ تم حفظ جميع التغييرات في قاعدة البيانات")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ خطأ في حفظ التغييرات: {str(e)}")
            return
        
        print("="*60)

def show_age_statistics():
    """عرض إحصائيات الأعمار"""
    app = create_app()
    
    with app.app_context():
        print("📊 إحصائيات الأعمار...")
        print("="*60)
        
        # إجمالي الطلبات
        total_applications = Application.query.count()
        applications_with_age = Application.query.filter(Application.age.isnot(None)).count()
        applications_without_age = total_applications - applications_with_age
        
        print(f"📋 إجمالي الطلبات: {total_applications}")
        print(f"✅ طلبات تحتوي على عمر: {applications_with_age}")
        print(f"❌ طلبات بدون عمر: {applications_without_age}")
        
        if applications_with_age > 0:
            # إحصائيات الأعمار
            from sqlalchemy import func
            
            age_stats = db.session.query(
                func.min(Application.age).label('min_age'),
                func.max(Application.age).label('max_age'),
                func.avg(Application.age).label('avg_age')
            ).filter(Application.age.isnot(None)).first()
            
            print(f"\n📈 إحصائيات الأعمار:")
            print(f"   🔽 أصغر عمر: {age_stats.min_age} سنة")
            print(f"   🔼 أكبر عمر: {age_stats.max_age} سنة")
            print(f"   📊 متوسط العمر: {age_stats.avg_age:.1f} سنة")
            
            # توزيع الأعمار
            age_ranges = [
                (0, 15, "أقل من 16 سنة"),
                (16, 20, "16-20 سنة"),
                (21, 25, "21-25 سنة"),
                (26, 30, "26-30 سنة"),
                (31, 40, "31-40 سنة"),
                (41, 100, "أكثر من 40 سنة")
            ]
            
            print(f"\n📊 توزيع الأعمار:")
            for min_age, max_age, label in age_ranges:
                count = Application.query.filter(
                    Application.age >= min_age,
                    Application.age <= max_age
                ).count()
                if count > 0:
                    percentage = (count / applications_with_age) * 100
                    print(f"   {label}: {count} طلب ({percentage:.1f}%)")
        
        print("="*60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='أداة تحديث وإحصائيات الأعمار')
    parser.add_argument('--action', choices=['update', 'stats'], default='update',
                       help='الإجراء المطلوب: update (تحديث) أو stats (إحصائيات)')
    
    args = parser.parse_args()
    
    if args.action == 'update':
        update_existing_ages()
    elif args.action == 'stats':
        show_age_statistics()
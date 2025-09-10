# -*- coding: utf-8 -*-
"""
أداة تنظيف الحسابات غير المؤكدة
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User

def cleanup_unverified_users():
    """تنظيف الحسابات غير المؤكدة"""
    app = create_app()
    
    with app.app_context():
        print("🧹 بدء تنظيف الحسابات غير المؤكدة...")
        print("="*60)
        
        # 1. حذف الحسابات منتهية الصلاحية
        print("1️⃣ حذف الحسابات منتهية الصلاحية...")
        expired_count = User.delete_unverified_users()
        
        # 2. حذف الحسابات القديمة (أكثر من 24 ساعة)
        print("\n2️⃣ حذف الحسابات القديمة غير المؤكدة (أكثر من 24 ساعة)...")
        old_count = User.cleanup_old_unverified_users(hours=24)
        
        # 3. عرض إحصائيات
        print(f"\n" + "="*60)
        print(f"📊 إحصائيات التنظيف:")
        print(f"   🗑️ حسابات منتهية الصلاحية: {expired_count}")
        print(f"   🗑️ حسابات قديمة (24+ ساعة): {old_count}")
        print(f"   📈 إجمالي المحذوف: {expired_count + old_count}")
        
        # 4. عرض الحسابات المتبقية غير المؤكدة
        remaining_unverified = User.query.filter_by(is_phone_verified=False).count()
        total_users = User.query.count()
        verified_users = User.query.filter_by(is_phone_verified=True).count()
        
        print(f"\n📈 إحصائيات قاعدة البيانات:")
        print(f"   👥 إجمالي المستخدمين: {total_users}")
        print(f"   ✅ مستخدمين مؤكدين: {verified_users}")
        print(f"   ⏳ مستخدمين غير مؤكدين: {remaining_unverified}")
        
        if remaining_unverified > 0:
            print(f"\n⚠️ تحذير: يوجد {remaining_unverified} حساب غير مؤكد لم يتم حذفه")
            print(f"   💡 هذه الحسابات قد تكون حديثة أو لا تزال صالحة")
        
        print(f"\n✅ تم الانتهاء من التنظيف!")
        print("="*60)

def show_unverified_users():
    """عرض الحسابات غير المؤكدة"""
    app = create_app()
    
    with app.app_context():
        print("👁️ عرض الحسابات غير المؤكدة...")
        print("="*60)
        
        unverified_users = User.query.filter_by(is_phone_verified=False).all()
        
        if not unverified_users:
            print("✅ لا توجد حسابات غير مؤكدة")
            return
        
        print(f"📋 عدد الحسابات غير المؤكدة: {len(unverified_users)}")
        print("-"*60)
        
        for i, user in enumerate(unverified_users, 1):
            status = "منتهي الصلاحية" if user.is_verification_expired() else "صالح"
            status_icon = "❌" if user.is_verification_expired() else "⏳"
            
            print(f"{i:2d}. {status_icon} {user.phone}")
            print(f"     📅 تم الإنشاء: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if user.verification_expires:
                print(f"     ⏰ انتهاء الصلاحية: {user.verification_expires.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"     📊 الحالة: {status}")
            print()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='أداة تنظيف الحسابات غير المؤكدة')
    parser.add_argument('--action', choices=['cleanup', 'show'], default='cleanup',
                       help='الإجراء المطلوب: cleanup (تنظيف) أو show (عرض)')
    
    args = parser.parse_args()
    
    if args.action == 'cleanup':
        cleanup_unverified_users()
    elif args.action == 'show':
        show_unverified_users()
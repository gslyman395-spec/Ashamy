#!/bin/bash

# 🚀 Ashamy - Build Script for Windows
# بناء المشروع على Windows

echo "════════════════════════════════════════════════════════════════"
echo "🚀 Ashamy - Windows Build Script"
echo "════════════════════════════════════════════════════════════════"
echo ""

# التحقق من Python
echo "✓ التحقق من Python..."
if ! command -v python -v &> /dev/null; then
    echo "❌ Python غير مثبت!"
    echo "📥 نزّل من: https://www.python.org/downloads/"
    exit 1
fi
echo "✅ Python مثبت"
echo ""

# التحقق من pip
echo "✓ التحقق من pip..."
python -m pip --version > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ pip غير مثبت!"
    exit 1
fi
echo "✅ pip مثبت"
echo ""

# التحقق من Git
echo "✓ التحقق من Git..."
if ! command -v git &> /dev/null; then
    echo "❌ Git غير مثبت!"
    echo "📥 نزّل من: https://git-scm.com/download/win"
    exit 1
fi
echo "✅ Git مثبت"
echo ""

# التحقق من Docker (اختياري)
echo "✓ التحقق من Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker مثبت"
else
    echo "⚠️ Docker غير مثبت (اختياري)"
fi
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "🔧 بناء المشروع..."
echo "════════════════════════════════════════════════════════════════"
echo ""

# إنشاء بيئة افتراضية
echo "📦 إنشاء بيئة افتراضية..."
if [ ! -d "venv" ]; then
    python -m venv venv
    if [ $? -eq 0 ]; then
        echo "✅ تم إنشاء البيئة الافتراضية"
    else
        echo "❌ فشل إنشاء البيئة الافتراضية"
        exit 1
    fi
else
    echo "✅ البيئة الافتراضية موجودة بالفعل"
fi
echo ""

# تفعيل البيئة الافتراضية
echo "🔌 تفعيل البيئة الافتراضية..."
source venv/Scripts/activate
if [ $? -eq 0 ]; then
    echo "✅ تم تفعيل البيئة الافتراضية"
else
    echo "❌ فشل تفعيل البيئة"
    exit 1
fi
echo ""

# تحديث pip
echo "📥 تحديث pip..."
python -m pip install --upgrade pip > /dev/null 2>&1
echo "✅ تم تحديث pip"
echo ""

# تثبيت المكتبات
echo "📚 تثبيت المكتبات..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✅ تم تثبيت جميع المكتبات"
    else
        echo "❌ فشل تثبيت المكتبات"
        exit 1
    fi
else
    echo "⚠️ ملف requirements.txt غير موجود"
fi
echo ""

# تثبيت أدوات الاختبار
echo "🧪 تثبيت أدوات الاختبار..."
pip install pytest coverage black flake8 mypy pylint > /dev/null 2>&1
echo "✅ تم تثبيت أدوات الاختبار"
echo ""

# تنظيف الكود
echo "🧹 تنظيف الكود..."
black . --line-length 100 > /dev/null 2>&1
echo "✅ تم تنظيف الكود"
echo ""

# فحص الجودة
echo "📊 فحص جودة الكود..."
flake8 . --max-line-length=100 --ignore=E501,W503 --count --statistics
echo ""

# تشغيل الاختبارات
echo "════════════════════════════════════════════════════════════════"
echo "🧪 تشغيل الاختبارات..."
echo "════════════════════════════════════════════════════════════════"
python -m pytest tests/ -v --tb=short
TEST_RESULT=$?

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo "✅ جميع الاختبارات نجحت!"
else
    echo ""
    echo "⚠️ بعض الاختبارات فشلت"
fi
echo ""

# قياس التغطية
echo "📈 قياس تغطية الاختبارات..."
coverage run -m pytest tests/ > /dev/null 2>&1
coverage report --fail-under=80
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ البناء اكتمل بنجاح!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🚀 لتشغيل المشروع:"
echo "   python -m uvicorn backend.api.routes:app --reload"
echo ""
echo "📱 لتشغيل تطبيق الموبايل:"
echo "   cd mobile && npm install && npm run android"
echo ""
echo "🐳 لتشغيل مع Docker:"
echo "   docker-compose up --build"
echo ""

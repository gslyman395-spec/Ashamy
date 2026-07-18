#!/bin/bash
# ============================================
# سكريبت بناء APK لتطبيق Ashamy
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📦 تثبيت الحزم..."
npm install

echo "🔑 إنشاء debug keystore إذا لم يكن موجوداً..."
if [ ! -f android/app/debug.keystore ]; then
    keytool -genkeypair -v \
        -keystore android/app/debug.keystore \
        -alias androiddebugkey \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -storepass android \
        -keypass android \
        -dname "CN=Android Debug,O=Android,C=US"
    echo "✅ تم إنشاء debug.keystore"
fi

echo "🏗️  بناء APK..."
cd android
chmod +x ./gradlew
./gradlew assembleDebug

APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
if [ -f "$APK_PATH" ]; then
    echo ""
    echo "✅ تم البناء بنجاح!"
    echo "📱 ملف APK موجود في:"
    echo "   $(pwd)/$APK_PATH"
    echo ""
    echo "لتثبيته على الهاتف عبر USB:"
    echo "   adb install $APK_PATH"
else
    echo "❌ لم يتم إنشاء APK. تحقق من الأخطاء أعلاه."
    exit 1
fi

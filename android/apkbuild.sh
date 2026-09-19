#!/bin/bash
# 元宝沙盒 APK 构建器（无需 Android Studio / Gradle / dl.google.com）
# 用法: bash apkbuild.sh <工程目录> <输出.apk>
# 工程目录需含: AndroidManifest.xml, src/, res/
set -e
ulimit -f unlimited
APP="$1"; OUT="$2"
[ -z "$APP" ] || [ -z "$OUT" ] && { echo "用法: bash apkbuild.sh <工程目录> <输出.apk>"; exit 1; }

AJ=/usr/lib/android-sdk/platforms/android-23/android.jar
DX=/usr/lib/android-sdk/build-tools/debian/lib/dx.jar
cd "$APP"
mkdir -p gen obj out

echo "[1/6] aapt 生成 R.java"
aapt package -m -J gen/ -M AndroidManifest.xml -S res/ -I "$AJ"

echo "[2/6] javac 编译（API 23）"
SRCS=$(find src gen -name "*.java")
javac -source 8 -target 8 -bootclasspath "$AJ" -d obj/ $SRCS 2>&1 | grep -v warning || true

echo "[3/6] dx 转 dex"
java -jar "$DX" --dex --output=out/classes.dex obj/

echo "[4/6] 打包 + 注入 dex"
aapt package -f -M AndroidManifest.xml -S res/ -I "$AJ" -F out/unsigned.apk
(cd out && aapt add unsigned.apk classes.dex >/dev/null)

echo "[5/6] zipalign 对齐"
zipalign -f 4 out/unsigned.apk out/aligned.apk

echo "[6/6] 签名"
if [ ! -f out/app.ks ]; then
  keytool -genkeypair -keystore out/app.ks -alias yuanbao -keyalg RSA \
    -keysize 2048 -validity 10000 -storepass 123456 -keypass 123456 \
    -dname "CN=Yuanbao, O=Tencent, C=CN" >/dev/null 2>&1
fi
apksigner sign --ks out/app.ks --ks-pass pass:123456 \
  --key-pass pass:123456 --out "$OUT" out/aligned.apk

echo ""
echo "✅ 构建完成: $OUT"
apksigner verify "$OUT" >/dev/null 2>&1 && echo "   验签: 通过" || echo "   验签: 失败"
aapt dump badging "$OUT" 2>/dev/null | head -2 | sed 's/^/   /'

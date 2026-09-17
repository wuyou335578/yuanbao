#!/bin/bash
# 一键恢复：Zig完整版 + sokol + 视觉
# 用法: bash restore_all.sh [目标目录]
set -eu
W="${1:-$PWD/restore}"; mkdir -p "$W"; cd "$W"
G="https://codeload.github.com/wuyou335578"
say(){ echo "== $1"; }

say "下载两个仓库"
curl -sL -o a.tgz "$G/yuanbao/tar.gz/refs/heads/main"
curl -sL -o b.tgz "$G/yuanbao-relay/tar.gz/refs/heads/main"
tar xzf a.tgz; tar xzf b.tgz; rm -f a.tgz b.tgz
A=$(find . -maxdepth 1 -type d -name 'yuanbao-*' ! -name '*relay*'|head -1)
B=$(find . -maxdepth 1 -type d -name '*relay*'|head -1)

say "Zig 0.16.0 完整版"
cat "$A"/zig/zp* > zig.zip
echo "bf0ce2bce4e543e02c7833792bb8f17f  zig.zip" | md5sum -c - || { echo "MD5 不符"; exit 1; }
unzip -q zig.zip; rm zig.zip; chmod +x zig
./zig version

say "sokol 图形栈"
unzip -q "$A"/sokol/sokol-zig-pkg.zip
mv sokol-zig sokol 2>/dev/null || true

say "视觉"
cp -r "$B"/tools "$B"/models .
pip install -q onnxruntime opencv-python -i https://mirrors.cloud.tencent.com/pypi/simple 2>/dev/null || echo "  (pip 跳过)"

say "系统库"
apt-get install -y -qq tesseract-ocr libgl1-mesa-dev libx11-dev libasound2-dev 2>/dev/null || echo "  (apt 跳过, 需 root)"

say "完成"
echo "  zig:    $W/zig"
echo "  sokol:  $W/sokol  (用包内 build-offline.zig 替换 build.zig)"
echo "  视觉:   python3 tools/detect.py 图.jpg --model models/yolov8n.onnx"
echo "  文档:   $B/HANDOVER.md  调试看 yuanbao/调试指南.md"

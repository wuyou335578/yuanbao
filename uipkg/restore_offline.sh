#!/bin/bash
# 从本地 deb 离线恢复 UI 设计软件 + 编程工具
# 优先用本地 deb；缺失的依赖走 apt 补
set -e
cd "$(dirname "$0")"

echo "== 1/3 修 apt 源（默认 archive.ubuntu.com 会被代理 403）"
cat > /etc/apt/sources.list <<'SRC'
deb https://mirrors.tencent.com/ubuntu/ jammy main restricted universe multiverse
deb https://mirrors.tencent.com/ubuntu/ jammy-updates main restricted universe multiverse
deb https://mirrors.tencent.com/ubuntu/ jammy-security main restricted universe multiverse
SRC
apt-get update -qq 2>/dev/null

echo "== 2/3 装本地 deb（ulimit -f unlimited 必须）"
ulimit -f unlimited
dpkg -i debs/*.deb 2>/dev/null || true

echo "== 3/3 apt 补全缺失依赖"
apt-get install -y --no-install-recommends -f

echo "== 验证"
for c in gimp inkscape krita shellcheck clangd cmake ninja; do
  printf "  %-12s %s\n" "$c" "$(command -v $c >/dev/null 2>&1 && echo OK || echo MISSING)"
done

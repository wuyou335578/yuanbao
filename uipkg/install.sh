#!/bin/bash
# 一键重装 UI 设计软件 + 编程工具（元宝沙盒专用）
# 用法: bash install.sh
set -e

echo "== 修复 apt 源（沙盒默认是 archive.ubuntu.com，会被代理 403）"
cat > /etc/apt/sources.list <<'SRC'
deb https://mirrors.tencent.com/ubuntu/ jammy main restricted universe multiverse
deb https://mirrors.tencent.com/ubuntu/ jammy-updates main restricted universe multiverse
deb https://mirrors.tencent.com/ubuntu/ jammy-backports main restricted universe multiverse
deb https://mirrors.tencent.com/ubuntu/ jammy-security main restricted universe multiverse
SRC

echo "== apt update"
apt-get update

echo "== 安装（ulimit -f unlimited 必须加，否则大包被截断）"
ulimit -f unlimited
apt-get install -y --no-install-recommends $(grep -v '^#' packages.list | grep -v '^$' | tr '\n' ' ')

echo "== 验证"
for c in gimp inkscape krita shellcheck clangd cmake ninja; do
  printf "  %-12s %s\n" "$c" "$(command -v $c >/dev/null 2>&1 && echo OK || echo MISSING)"
done

#!/usr/bin/env bash
# 一键恢复：UI 设计 + 编程工具全套（Ubuntu 22.04）
# 用法: bash restore_tools.sh
set -e

echo "== 1/3 切腾讯镜像源（默认的 archive.ubuntu.com 会被代理 403）"
cat > /etc/apt/sources.list <<'SRC'
deb https://mirrors.tencent.com/ubuntu/ jammy main restricted universe multiverse
deb https://mirrors.tencent.com/ubuntu/ jammy-updates main restricted universe multiverse
deb https://mirrors.tencent.com/ubuntu/ jammy-security main restricted universe multiverse
SRC
apt-get update -qq

echo "== 2/3 安装（ulimit -f unlimited 是关键）"
# 必须！否则 libembree3.so.3(200MB) 会被 100MB 上限截断，dpkg 崩溃
ulimit -f unlimited

PKGS="
  gimp inkscape krita blender openscad kdenlive audacity
  golang-go rustc cargo maven default-jdk-headless
  neovim vim shellcheck clangd cmake ninja-build
"
apt-get install -y --no-install-recommends $PKGS

echo "== 3/3 验证"
for c in gimp inkscape krita blender openscad go rustc cargo mvn nvim shellcheck clangd cmake javac; do
  printf "  %-10s %s\n" "$c" "$(command -v $c >/dev/null 2>&1 && echo OK || echo MISSING)"
done
echo "完成"

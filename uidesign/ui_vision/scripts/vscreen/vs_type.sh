#!/bin/bash
# 虚拟键盘输入：vs_type.sh "文字"
timeout 30 env DISPLAY=:99 xdotool type --delay 30 "$1"
echo "已输入: $1"

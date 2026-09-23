#!/bin/bash
# 虚拟按键：vs_key.sh Return
timeout 30 env DISPLAY=:99 xdotool key "$1"
echo "已按键: $1"

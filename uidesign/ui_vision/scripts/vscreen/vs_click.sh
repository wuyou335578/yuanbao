#!/bin/bash
# 虚拟鼠标点击：vs_click.sh X Y
timeout 30 env DISPLAY=:99 xdotool mousemove --sync "$1" "$2" click 1
echo "已点击 ($1,$2)"

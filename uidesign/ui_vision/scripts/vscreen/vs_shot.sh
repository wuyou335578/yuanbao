#!/bin/bash
# 截取虚拟屏
OUT="${1:-/data/user_persistent_data/uiparse/vscreen/screen.png}"
timeout 60 env DISPLAY=:99 scrot -d 1 "$OUT" 2>/dev/null
echo "$OUT  $(python3 -c "from PIL import Image;print(Image.open('$OUT').size)")"

#!/bin/bash
# 启动虚拟屏 :99（1080x2340，手机竖屏 3x）
D=/data/user_persistent_data/uiparse/vscreen
pgrep -f "Xvfb :99" >/dev/null || (setsid Xvfb :99 -screen 0 1080x2340x24 -nolisten tcp >/dev/null 2>&1 &)
sleep 2
echo "虚拟屏 :99  $(timeout 10 env DISPLAY=:99 xdotool getdisplaygeometry)"

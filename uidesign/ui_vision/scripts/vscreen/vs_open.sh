#!/bin/bash
# 在虚拟屏上用 chrome 打开 HTML（手机视口 360x780 CSS，3x 渲染成 1080x2340）
H="$1"
D=/data/user_persistent_data/uiparse/vscreen
pkill -f "user-data-dir=$D/profile" 2>/dev/null; sleep 1
( DISPLAY=:99 setsid google-chrome --no-sandbox --disable-dev-shm-usage --disable-gpu \
  --no-first-run --disable-extensions --disable-component-update \
  --force-device-scale-factor=3 --window-size=360,780 --window-position=0,0 \
  --app="file://$H" --user-data-dir="$D/profile" >/dev/null 2>&1 & )
echo "chrome 已启动（本命令会因后台进程挂住，属正常）"

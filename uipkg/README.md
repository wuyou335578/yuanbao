# UI 设计软件 + 编程工具 离线包

## 含 199 个 deb（286 MB）

**UI / 设计**
GIMP 2.10.30（位图）、Inkscape 1.1.2（矢量）、Krita 5.0.2（绘画）

**编程 / 插件**
shellcheck、clangd、cmake、ninja-build

（另有 blender / openscad / kdenlive / audacity / go / rustc / maven / jdk 等，
见 installed.list 完整清单）

## 两种恢复方式

### A. 离线（本地 deb，最快）
```bash
bash restore_offline.sh
```
先用 `dpkg -i debs/*.deb`，再用 `apt-get install -f` 补缺失依赖。

### B. 联网（仅装 7 个核心包）
```bash
bash install.sh
```

## 两个必踩坑

1. **必须切腾讯源** — 默认 `archive.ubuntu.com` 被代理 403
2. **必须 `ulimit -f unlimited`** — 单文件上限默认 100MB，
   blender 的 `libembree3.so.3`(200MB) 会被截断导致 dpkg 崩溃

## 注意

- 这些是 GUI 程序，沙盒无桌面环境
- **命令行批处理可用**：`inkscape in.svg -o out.png`（实测通过）
- GIMP 批处理需虚拟屏（Xvfb），重置后需重装

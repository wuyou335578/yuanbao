# ai全栈开发 完整包（分卷）

**153 MB，切成了 7 个分卷**（GitHub 单文件上限 100MB，API 实测 30MB 可、45MB 拒，故用 25MB/份）。

## 复原

```bash
cat aipkg_* > ai全栈开发.zip
md5sum ai全栈开发.zip
# 应为 f761770999694bab00c5bd909458942e
unzip ai全栈开发.zip
cd ai全栈开发
bash 一键恢复.sh /opt/dev
export PATH="/opt/dev:$PATH"
zig version        # → 0.16.0
```

⚠️ **必须先** `ulimit -f unlimited`（沙盒默认单文件上限 100MB，
zig 二进制 165MB 会被截断）。`一键恢复.sh` 里已带。

## 包里有什么

| 内容 | 说明 |
|---|---|
| zig 0.16.0 **完整版** | 能编 C/C++/Zig（pip 装的是残缺版，编不了 C++） |
| zls 0.16.0 | Zig 语言服务器，版本须与 zig 对齐 |
| raylib 6.0 运行时 | 图形库（含 `libraylib.so.600` 软链） |
| sokol-zig | 图形栈（含 C ABI） |
| 视觉模型 | yolov8n（目标检测 58ms/张）+ resnet50（分类）+ 7 个脚本 |
| Xvfb 离线 deb | 虚拟显示屏，无需联网安装 |
| 沙盒教程 | 1064 行完整教程 + 4 个脚本 |

## 关键点

- **沙盒会重置且无预警** → 用 `一键恢复.sh`，或把 zip 存持久区缓存（5 秒恢复）
- **网络是白名单**，403 = 代理拒绝（不是断网），别找 VPN
- **无 GPU**，视觉走 CPU（有 AVX-512，不慢）
- **Xvfb 启动要脱离会话**，直接 `&` 会挂住 shell

详见包内 `05_沙盒教程/完整使用教程.md`。

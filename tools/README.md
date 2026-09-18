# 开发工具包（UI 设计 + 编程）

## 包含

**UI / 设计**
| 软件 | 用途 |
|---|---|
| GIMP 2.10 | 位图编辑（PS 替代） |
| Inkscape 1.1 | 矢量图（AI 替代） |
| Krita 5.0 | 数字绘画 |
| Blender 3.0 | 3D 建模 + 渲染（可无头脚本建模） |
| OpenSCAD | 参数化 CAD（纯代码建模） |
| Kdenlive | 视频剪辑 |
| Audacity | 音频编辑 |

**编程 / 构建**
| 工具 | 版本 |
|---|---|
| Go | golang-go |
| Rust | rustc + cargo |
| Java | default-jdk-headless（含 javac） |
| Maven | mvn |
| clangd | C/C++ 语言服务器 |
| cmake / ninja | 构建系统 |
| shellcheck | Shell 静态检查 |
| neovim / vim | 命令行编辑器 |

## 恢复方式

### A. 联网装（推荐）
```bash
bash restore_tools.sh
```
脚本已内置：切腾讯源 + `ulimit -f unlimited` + 装全部包 + 验证。

### B. 离线装（无网时）
```bash
cat tools_paa tools_pab ... tools_pal > 开发工具包.tar.gz
tar xzf 开发工具包.tar.gz
cd debs && dpkg -i *.deb
```

## 两个必踩的坑

1. **必须切腾讯源** — 默认的 `archive.ubuntu.com` 会被代理 403。
2. **必须 `ulimit -f unlimited`** — 单文件上限默认 100MB，
   Blender 的 `libembree3.so.3`(200MB) 会被截断导致 dpkg 崩溃。

## 校验

整包 md5: `12fe43c38b8eaa2943c966bd7817c13b`

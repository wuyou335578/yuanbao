# sokol-zig 包 —— Zig 图形开发栈

> Zig 0.16.0 + C ABI + sokol-zig，**已实测编译通过**。

## 包内容

```
sokol-zig-pkg.zip (2.58 MB, md5 0f2f85700248beed6a62baa34895ed6d)
├── sokol-zig/          Zig 绑定（含 C ABI，自包含）
│   ├── src/sokol/*.zig      Zig 绑定层（gfx/app/audio/gl/...）
│   └── src/sokol/c/          C ABI：31 个文件（.h + .c）
├── sokol-c/            上游 C 库（参考：tests/util/shdgen/bindgen）
└── build-offline.zig   ★ 可直接用的最小构建（不联网）
```

## 关键：sokol-zig 自带 C ABI

`sokol-zig/src/sokol/c/` 里**已经有 C 头文件和实现**：

```
sokol_gfx.h / .c      图形核心
sokol_app.h / .c      窗口与输入
sokol_audio.h / .c    音频
sokol_time / gl / glue / shape / debugtext / fetch / cmdbuf / imgui ...
```

所以 **sokol-zig 本身就是「Zig 绑定 + C ABI」的完整包**，不需要额外下载 sokol C 库。
`sokol-c/` 只是上游参考（多出 tests、util、shdgen、bindgen）。

## 已验证（zig 0.16.0 实测）

```
zig version           0.16.0
编译产物               libsokol.a  5.67 MB ✅
后端                   SOKOL_GLCORE（Linux 桌面 OpenGL）
```

### 官方 build.zig 直接用会失败

官方 `build.zig.zon` 声明了两个依赖：

```
emsdk  → git+https://github.com/emscripten-core/emsdk     （web 构建）
shdc   → git+https://github.com/floooh/sokol-tools-bin    （着色器编译）
```

**git 协议在本环境不通**（`unable to discover remote git server capabilities:
ProtocolError`），所以 `zig build` 会直接失败。

**解法**：用包里的 `build-offline.zig` 替换 `build.zig`，
同时 `build.zig.zon` 的 dependencies 改成 `.{}`。它不依赖任何网络。

## 使用方法

```bash
# 1. 解压
unzip sokol-zig-pkg.zip && cd sokol-zig

# 2. 用离线构建替换官方构建
cp ../build-offline.zig build.zig
cat > build.zig.zon <<'EOF'
.{ .name = .sokol, .version = "0.1.0",
   .paths = .{"src","build.zig","build.zig.zon"},
   .dependencies = .{}, .fingerprint = 0xf306c7659b844957 }
EOF

# 3. 编译
zig build
# → zig-out/lib/libsokol.a
```

## 系统依赖（Linux 编译必需）

sokol_app 需要 X11，sokol_audio 需要 ALSA。**缺了会编译失败**：

```bash
apt-get install -y libx11-dev libgl1-mesa-dev libxi-dev \
                   libxcursor-dev libxinerama-dev libxrandr-dev \
                   libasound2-dev
```

实测缺 `X11/Xlib.h` → sokol_app.h 报错；
缺 `alsa/asoundlib.h` → sokol_audio.h 报错。

## 后端宏（必须选一个）

| 宏 | 用途 |
|---|---|
| `SOKOL_GLCORE` | Linux/Windows 桌面 OpenGL |
| `SOKOL_DUMMY_BACKEND` | 无 GPU，仅编译验证 |
| `SOKOL_D3D11` / `SOKOL_METAL` / `SOKOL_WGPU` / `SOKOL_VULKAN` | 其他平台 |

**注意**：`SOKOL_DUMMY_BACKEND` 只能让 `sokol_gfx` 通过，
`sokol_app` 在 Linux 上仍要求 GLCORE/GLES3/WGPU/VULKAN 之一，
会报 `unknown 3D API selected for Linux`。

另外 C 源文件用 `#if defined(IMPL)` 控制实现，
**必须同时定义 `-DIMPL`**，否则只有声明没有实现，链接会缺符号。

## Zig 0.16 API 提醒

0.16 移除了 `b.addStaticLibrary()`，改用：

```zig
const mod = b.createModule(.{
    .root_source_file = b.path("..."),
    .target = target, .optimize = optimize, .link_libc = true,
});
mod.addCSourceFile(.{ .file = ..., .flags = &.{"-DIMPL"} });
const lib = b.addLibrary(.{
    .name = "sokol", .root_module = mod, .linkage = .static,
});
```

## 配套

Zig 完整版编译器在本仓库 `zig/` 目录（分卷），
用 `restore_zig.sh` 一键恢复。**版本必须是 0.16.0**，
sokol-zig 的 README 明确写「For Zig version 0.16+」。

# 元宝沙盒 APP（Android）开发能力说明

> 实测日期：2026-09-18，全部跑通验证

---

## 一、结论：能做 APK

**完整链路实测通过**：

```
Java 源码 → class → dex → APK → 对齐 → 签名 → 验签通过
```

产物示例：`YuanbaoHello.apk` 8.4 KB
验签：SHA-256 证书完整
`aapt dump badging` 正常读出包名 / SDK / 应用名

---

## 二、关键突破：不需要官方 SDK

直接路线**全堵死**：

```
dl.google.com（Android SDK 官方源）  → 403
Android Studio / Gradle 完整 SDK     → 依赖上述源，装不了
apt 的 android-sdk-build-tools       → 只有 3.6KB，是个联网下载器，不含工具
```

**真正的路子在 apt 仓库里**，这些是 Debian 原生打包的真实可执行文件：

| 工具 | 来自包 | 作用 |
|---|---|---|
| `android.jar` (API 23) | libandroid-23-java | 编译依赖 |
| `dx.jar` | dalvik-exchange | class → dex |
| `aapt` | aapt | 打包资源 |
| `zipalign` | zipalign | 对齐优化 |
| `apksigner` | apksigner | 签名 |

**全部不依赖任何外网。**

---

## 三、安装命令（照抄）

```bash
ulimit -f unlimited
cat > /etc/apt/sources.list <<'SRC'
deb https://mirrors.tencent.com/ubuntu/ jammy main restricted universe multiverse
deb https://mirrors.tencent.com/ubuntu/ jammy-updates main restricted universe multiverse
deb https://mirrors.tencent.com/ubuntu/ jammy-security main restricted universe multiverse
SRC
apt-get update
apt-get install -y --no-install-recommends \
  openjdk-17-jdk-headless libandroid-23-java dalvik-exchange \
  aapt zipalign apksigner
```

---

## 四、一键构建

```bash
bash apkbuild.sh <工程目录> <输出.apk>
```

工程目录结构：
```
MyApp/
├── AndroidManifest.xml
├── src/com/xxx/MainActivity.java
└── res/values/strings.xml
```

脚本自动完成 6 步：R.java → javac → dx → 打包 → 对齐 → 签名 → 验签。

---

## 五、Maven 通道能拿 AndroidX（重大）

```
https://mirrors.tencent.com/nexus/repository/maven-public/
```

实测可获取：

| 库 | 大小 |
|---|---|
| androidx appcompat 1.6.1 | 1109 KB |
| androidx core 1.10.1 | 1219 KB |
| androidx activity 1.7.0 | 139 KB |
| androidx constraintlayout 2.1.4 | 465 KB |
| com.google.android.material 1.9.0 | 2151 KB |
| gson 2.10.1 | 277 KB |
| okhttp 4.11.0 | 769 KB |

**Material Design 组件可用**，能做现代 UI 风格。

---

## 六、⚠️ 四个限制（必须知道）

**1. API 只有 23（Android 6.0）**
本地 android.jar 由 libandroid-23-java 提供，仅 API 23。
用 AndroidX 新库时可能遇到 API 不匹配，需要降级库版本或自行适配。

**2. 不能运行**
```
adb ❌   Android 运行环境 ❌   /dev/kvm ❌
```
沙盒里没有 Android 系统，APK 装不了也跑不起来。
**只能构建，不能测试运行** —— 装到真机验证得你来。

**3. 没有 Gradle**
不装也能过（本方案走 aapt+dx 直构）。
但如果你要接现有 Gradle 工程，这条路走不通。

**4. 装的根分区，重置会没**
工具链装在 `/`，沙盒重置后需要重装（apt 命令在上面，几分钟）。
**工程源码务必放 `/data/workspace`**。

---

## 七、现在磁盘够了能多做什么

以前卡在磁盘小（记录里写"1GB 磁盘"），现在实测持久区 189GB+ 无压力，

新增可能：
- **缓存整套 AndroidX/Material 库到持久区**，重置不用重下
- 存多个完整工程
- 交叉编译原生库：zig 支持 `-target aarch64-linux-android`，
  能编出 Android 的 .so 塞进 APK

---

## 八、另一条路：改现有 APK

如果要改已有 App（不是从零写）：

```
apktool 反编译 → 改 smali / 资源 → 回编译 → 签名
```

apktool 已通过 Maven 通道验证可用（2.9.3，25 个依赖自动拉取）。

**⚠️ 注意**：apktool.jar 曾被 ulimit 截断成 0 字节（下载时没解除 100MB 限制）。
重新获取时务必先 `ulimit -f unlimited`，否则拿到的是坏文件。

---

## 九、速查

| 想做什么 | 路子 |
|---|---|
| 从零写 App | apkbuild.sh（Java + API 23） |
| 用现代 UI 组件 | Maven 拿 AndroidX / Material |
| 改现有 APK | apktool 反编译 → 改 → 回编译 |
| 带原生代码 | zig -target aarch64-linux-android 编 .so |
| 运行测试 | ❌ 做不到，需你装真机 |

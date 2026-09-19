# 四个限制 × "丢仓库我去下载"——逐条实测结论

> 实测日期：2026-09-18，全部跑通验证

---

## 总表

| 限制 | 丢仓库能解决吗 | 结论 |
|---|---|---|
| 1. API 只有 23 | **不用你丢，我自己能拿** | ✅ 已解决 |
| 2. 不能运行 APK | ❌ **无解** | 仓库也救不了 |
| 3. 没有 Gradle | ⚠️ **需要你丢** | 我下载不到源头 |
| 4. 重置会丢工具 | ✅ **能解决** | 闭环已实测 |

---

# 限制 1：API 只有 23 —— 我自己解决了

## 突破口：Robolectric 的 android-all

Maven 通道（腾讯镜像）能拿到各 API 级别的完整 android.jar：

```
https://mirrors.tencent.com/nexus/repository/maven-public/
org/robolectric/android-all/13-robolectric-9030017/android-all-13-robolectric-9030017.jar
```

实测可获取：

| 目标 | 状态 | 大小 |
|---|---|---|
| **API 33 (Android 13)** | ✅ 200 | **170.1 MB** |
| API 28 (Android 9) | ✅ 200 | 115.3 MB |
| API 32 / 30 | ❌ 404 | 该版本号镜像上没有 |

**66510 个类文件，含完整 android.app.Activity。**

## 关键坑：不能用 -bootclasspath

android-all 是**完整实现包**（Robolectric 用来在 JVM 上跑测试），
**不含 java.lang.Object**，所以：

```bash
javac -bootclasspath android-33.jar ...     ❌ 报错
# error: cannot access Object
#   class file for java.lang.Object not found
```

**正确姿势 —— 用 `-classpath`**：让 JDK 提供 java.* 基础类，
android-all 只补 android.* ：

```bash
javac -nowarn -classpath android-33.jar -d . NewApi.java    ✅
```

## 实测对比

同一份代码（用了 `NotificationChannel`，API 26+ 才有）：

| 用哪个 jar | 结果 |
|---|---|
| API 23 android.jar | ❌ 3 个 `cannot find symbol` |
| **API 33 android.jar（-classpath）** | ✅ **编译成功，生成 class** |

**限制 1 解除**：现在能用 API 33 的新 API 写代码。

---

# 限制 4：重置会丢工具 —— 闭环实测通过

## 完整验证过程

```
① 上传工具链到仓库
   android-33.jar 171MB → 分 7 卷（每卷 25MB）
   + dx.jar + apkbuild.sh + 说明文档
   → commit c0e1b4960a4b ✅

② 模拟重置：删除本地 androidsdk/ 目录
   删除前 md5: 32a9ff24e5b41caf44b0bb96093f5ac8

③ 从仓库下载（blobs API）
   ↓ 7 个分卷 + dx.jar + 脚本，全部成功

④ 合并分卷
   170.1 MB
   md5: 32a9ff24e5b41caf44b0bb96093f5ac8  ✅ 完全一致

⑤ 用恢复的 dx.jar 构建 APK
   aapt → javac → dx → 打包 → zipalign
   ✅ 产物 2.5 KB
```

**结论：丢仓库 → 我下载 → 恢复 → 能干活，闭环成立。**

## 分卷为什么是 25MB

GitHub 单文件上限 100MB，但 base64 上传会膨胀 33%，
实测 25MB/卷 最稳（153MB、171MB 的包都这么传成功过）。

合并命令：
```bash
cat andpkg_* > android-33.jar
```

---

# 限制 3：没有 Gradle —— 需要你丢

## 我下载不到源头

```
services.gradle.org（Gradle 官方源）  → 403
org/gradle/gradle-tooling-api (Maven) → 404
Maven Central 上没有 Gradle 完整发行版
```

**Gradle 完整发行版 ≈ 130MB**，官方源被墙，Maven 上没有。

## 你要怎么做

1. 你自己下载 `gradle-8.5-bin.zip`（约 130MB）
2. 传进仓库（分卷，每卷 25MB）
3. 我从仓库下载 → 合并 → 解压 → 能用

**不过说实话**：本方案走 `aapt + dx` 直构，**不依赖 Gradle 也能做 App**。
只有你要接**现有 Gradle 工程**时才需要它。

---

# 限制 2：不能运行 APK —— 真无解

## 为什么仓库救不了

```
adb          ❌ 无
Android 系统  ❌ 沙盒是 Linux，不是 Android
/dev/kvm     ❌ 无（无法硬件加速虚拟化）
```

**丢什么都解决不了** —— 不是缺文件，是缺**整个 Android 运行环境**。
APK 是给 Android 系统执行的，Linux 上装不了、跑不起来。

## 部分缓解：Robolectric 跑单元测试

Maven 能拿到 Robolectric 本体（实测 200），
它能在 **JVM 上执行 Android 代码**：

- ✅ 能测：业务逻辑、数据流转、工具类
- ❌ 不能测：UI 渲染、真机特性、性能

**真机验证仍然得你来。**

---

# 实操清单

## 你要往仓库丢什么（按优先级）

| 优先级 | 文件 | 大小 | 用途 |
|---|---|---|
| 高 | Gradle 发行版（如需接现有工程） | 130MB | 解限制 3 |
| 中 | AndroidX / Material 的 aar | 各 1-2MB | 现代 UI |
| 低 | 其他 SDK | — | 按需 |

**API 33 的 android.jar 我已经传进仓库了**，不用你重复丢。

## 我这边已入库（yuanbao/android/）

```
android/
├── andpkg_000 ~ andpkg_006    android-33.jar 分卷（171MB）
├── dx.jar                     class → dex
├── apkbuild.sh                一键构建脚本
└── APP开发能力说明.md
```

## 恢复命令

```bash
ulimit -f unlimited                    # 必须先解除 100MB 陷阱
# 从仓库下载 android/ 下所有文件
cat andpkg_* > android-33.jar
```

---

# 一句话总结

> **API 限制我自己拿了（API 33）、重置丢失已闭环验证、Gradle 需要你丢、
> 运行 APK 无论丢什么都解决不了——缺的不是文件，是 Android 系统本身。**

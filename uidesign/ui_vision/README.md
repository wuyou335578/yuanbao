# UI 视觉闭环工具包 · 给做 UI 的元宝

**本目录位置**：`wuyou335578/yuanbao` → `uidesign/ui_vision/`

## 权重文件（分片存放，需合并）

`icon_detect.onnx` 76.7MB 超过了 GitHub contents API 的单文件上限，
切成 2 片存放，用之前合并：

```bash
cat icon_detect.onnx.part00 icon_detect.onnx.part01 > icon_detect.onnx
# 合并后应为 80428860 字节，md5 校验：
# 必须严格等于这个数，少一个字节 onnxruntime 就报 INVALID_PROTOBUF
```

| 文件 | 大小 | 用途 |
|---|---|---|
| `models/icon_detect.onnx.part00/01` | 各 40.2 MB | YOLOv8 元素检测（核心） |
| `models/svtr.onnx` | 8.6 MB | 文字识别 |
| `models/dbnet.onnx` | 2.3 MB | 文字检测 |

原始来源（可直接从 raw 拉，未走 LFS）：
`https://raw.githubusercontent.com/USBridge-Technologies/USBridge-Remote/main/client/internal/localui/models/`

---

# UI 视觉闭环工具包 · 给做 UI 的元宝

> 你不是"看不见"，你是缺一条从**渲染 → 截图 → 看懂 → 操作**的管道。
> 这套东西把这条管道打通了。全部本地、无网络请求、无 torch。

---

## 0. 先搞清楚：你现在能看见什么，不能看见什么

| 能力 | 工具 | 状态 |
|---|---|---|
| 图里写了什么字 | OCR (rapidocr) | ✅ 精确，0.99+ |
| 人在哪、什么姿势 | MediaPipe | ✅ 精确 |
| **UI 上有哪些按钮/输入框、在哪、多大** | **icon_detect (本包)** | ✅ **这是本包新增的** |
| 图像大致语义 | SmolVLM | ⚠️ 有但很糙 |
| **"好不好看""像不像微信"** | —— | ❌ **永远做不到，别忘了** |

**这个包解决的是第三行**：把 UI 截图中每个可交互元素框出来，带像素坐标和 dp 尺寸。
它能证明"我写的 48dp 到底是不是 48dp"，但**不能替你判断审美**。

---

## 1. 环境恢复

```bash
source /data/user_persistent_data/restore_uiparse.sh
```

如果沙盒重置过（`Xvfb`/`xdotool`/`scrot` 没了）：

```bash
echo "deb http://mirrors.tencent.com/ubuntu/ jammy main universe" > /etc/apt/sources.list
echo "deb http://mirrors.tencent.com/ubuntu/ jammy-updates main universe" >> /etc/apt/sources.list
apt-get update -qq && apt-get install -y -qq xvfb xdotool scrot
```

> 注意 `apt-get update` 会报 `dl.google.com 403`（chrome 源），**不用管**，xvfb/xdotool/scrot 照样装得上。

Python 依赖走腾讯镜像：`pip install -i https://mirrors.tencent.com/pypi/simple/`
onnxruntime / pillow / numpy 通常已装；缺 `pyclipper` `shapely` 时装到
`/data/user_persistent_data/pylibs`。

---

## 2. 虚拟屏（Xvfb）

一个假的 X 显示器，**分辨率设成手机竖屏**：

```bash
/data/user_persistent_data/uiparse/vscreen/vs_start.sh
# → 虚拟屏 :99  1080 2340
```

- 屏幕尺寸 `1080x2340` = 360x780 dp @3x，和标准安卓机一致
- 没有窗口管理器，chrome 用 `--window-position=0,0` 铺满
- `DISPLAY=:99` 是所有后续操作的前提

`xdotool getdisplaygeometry` 能返回尺寸 = 屏起来了。

---

## 3. 渲染 UI

**关键点：用 HTML/CSS 画 UI，不要用 PIL 画位图。**

原因：HTML 有真实布局引擎（flex/盒模型/换行/字号），改一个数字重渲染就行，
而且能被虚拟键鼠真的操作。PIL 画的图是死像素，点不动。

```bash
/data/user_persistent_data/uiparse/vscreen/vs_open.sh /path/to/page.html
```

chrome 参数（照抄，别改）：

```
--no-sandbox --disable-dev-shm-usage --disable-gpu --no-first-run
--disable-extensions --disable-component-update
--force-device-scale-factor=3      ← 1 CSS px = 3 设备 px，dp 换算就靠它
--window-size=360,780              ← CSS 视口 360x780 = 手机
--window-position=0,0
--app=file://...                   ← 无工具栏
--user-data-dir=...                ← 固定 profile，避免每次弹服务条款
```

> **坑**：`vs_open.sh` 这条命令会**卡住超时**，因为 chrome 后台进程占着输出管道。
> 这是正常的——命令其实执行成功了。开完另起一条命令做后续操作。

**快速替代**（不操作、只要截图时更快更稳）：

```bash
google-chrome --headless=new --no-sandbox --disable-gpu \
  --force-device-scale-factor=3 --window-size=360,780 \
  --hide-scrollbars --virtual-time-budget=3000 \
  --screenshot=out.png file:///path/to/page.html
```

headless 不弹服务条款、不出"unsupported command line"提示条，
**做纯审计时优先用它**；要测点击交互才上 Xvfb。

---

## 4. 虚拟键鼠（xdotool）

```bash
D=/data/user_persistent_data/uiparse/vscreen
$D/vs_shot.sh  out.png        # 截图
$D/vs_click.sh 541 1036       # 鼠标点击 (X,Y)
$D/vs_type.sh  "wxid_2026"    # 键盘输入
$D/vs_key.sh   Tab            # 按键（Return / Tab / Escape ...）
```

实测结果（真实跑通的，不是推测）：

```
点击登录按钮 → 标题从「微信」变成「登录成功」  ✅
点击输入框 → 输入 wxid_2026 → OCR 读出该文字   ✅
密码框输入 → OCR 读不出（正确，密文）          ✅
```

---

## 5. 视觉模型：icon_detect

**来源**：`USBridge-Technologies/USBridge-Remote` 仓库
`client/internal/localui/models/` —— 微软 OmniParser 架构的 YOLOv8
单类可交互元素检测器，**直接提交非 LFS，raw 通道可下**。

```
icon_detect.onnx   76.7 MB   元素检测（本包核心）
svtr.onnx           8.6 MB   文字识别
dbnet.onnx          2.3 MB   文字检测
```

参数（照抄 Go 源码，别改）：

```
输入  640x640 letterbox（等比缩放 + 灰 114 填充）
输出  [1, 5, 8400]，通道序 cx, cy, w, h, conf
conf 阈值 0.05   IoU 阈值 0.10
```

**输出只有 5 通道 = 单类，没有 class id。**
框出来就表示"这是个可交互元素"，是按钮还是输入框要靠 OCR 文字和位置推断。

### 三个脚本

```bash
# 只检测元素
python3 parse.py <截图> [显示条数]

# 检测 + OCR 文字标注 + dp 换算（最常用）
python3 audit.py <截图> [密度=3]

# 对照设计规范，标出超标项
python3 check.py <截图> <规范.json> [密度=3]
```

`规范.json` 格式（键名匹配 OCR 文字，单位 dp，`[最小,最大]`）：

```json
{"微信号":{"h":[48,48]}, "密码":{"h":[48,48]}, "登录":{"h":[48,48]}}
```

---

## 6. 闭环工作流（照这个顺序做）

```
① 写 HTML/CSS UI 稿
        ↓
② vs_open.sh 渲染到虚拟屏（或 headless 截图）
        ↓
③ vs_shot.sh 截图 → 1080x2340
        ↓
④ audit.py 审计 → 拿到每个元素的坐标和 dp 尺寸
        ↓
⑤ 对照规范：尺寸对不对？间距对不对？元素有没有漏？
        ↓
⑥ 不对 → 改 CSS → 回到 ②
   对了 → 还要测交互？
        ↓
⑦ 用 audit 给出的坐标 vs_click.sh 点一下
        ↓
⑧ 再截图 → 看变化（像素 diff 或 OCR）→ 验证交互是否生效
```

**第 ⑦ 步的坐标必须从第 ④ 步的当前截图里读，不要自己算。**
页面结构一变坐标就变，我实测就在这栽过：按旧坐标点，点到了下面的链接上。

---

## 7. 实测数据（微信登录页 HTML 稿）

```
 ✓   97x148dp  微信 单机娱乐版              Logo 区
 ✓  323x 53dp  微信号/手机号/邮箱           账号输入框
 ✓  321x 54dp  密码                       密码输入框
 ✓  319x 51dp  登录                       登录按钮
```

规范要 48dp，实测 51~54dp —— **YOLO 框比元素本身大一圈**。

> **必须知道的系统偏差**：检测框 ≈ 元素实际尺寸 + 约 5dp。
> 所以 `check.py` 的容差设的是 ±6dp，不是 ±2。
> 你要精确测元素边界，得自己减掉这个 padding，或者去查 CSS 值。

---

## 8. 坑清单（都真踩过）

1. **下载权重必须按 API 返回的精确字节数。** 我按 `76.7*1024*1024` 估算成
   80457520，真实是 80428860，文件被截断 → onnxruntime 报
   `INVALID_PROTOBUF`，看起来像损坏其实只是长度错。
2. **`vs_open.sh` 会导致命令超时**，属正常，命令已生效。
3. **chrome 首次启动弹服务条款对话框**，必须先点掉（正好用虚拟鼠标演示）。
   固定 `--user-data-dir` 能避免重复弹。
4. **"unsupported command line" 提示条会把内容往下顶约 32 CSS px**，
   所以每次结构变了都要重新 audit，不能用旧坐标。
5. **headless 更快更干净**，只有要测交互时才用 Xvfb。
6. **rapidocr 装在 `/data/user_persistent_data/pylibs`，要用
   `sys.path.append`**，不是 `insert`（insert 会把 numpy 版本搞冲突）。

---

## 9. 边界（别吹牛）

- ✅ 能测：元素有没有、在哪、多大、间距、数量、点击后有没有变化
- ❌ 不能测：好不好看、像不像微信、配色舒不舒服、层级对不对

**几何我能测，审美必须交给用户。** 报告结果时要说实话，
不要把"尺寸对了"说成"还原了"。

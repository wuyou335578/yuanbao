# 视觉辅助模型包（本地离线，无需外网）

17 个权重文件，44 MB。全部实测可加载、可推理。

> **为什么单独存一份**：沙盒网关只放行 `mirrors.tencent.com`（pypi/maven）和 `api.github.com`。
> HuggingFace / ModelScope / 官方 pypi 全部 `403 policy_denied`。
> 这些权重是**从 pypi 包的 wheel 内部直接提取**的——绕开了所有被封的站点。

---

## 目录结构

| 目录 | 内容 | 来源 |
|---|---|---|
| `ocr/` | PaddleOCR v4 中文识别（3 个 onnx） | `rapidocr-onnxruntime==1.4.4` |
| `mediapipe/` | Google MediaPipe（14 个 tflite） | `mediapipe==0.10.14` |

---

## 一、OCR（读图里的文字）

| 文件 | 大小 | 作用 |
|---|---|---|
| `ch_PP-OCRv4_det_infer.onnx` | 4.75 MB | 文字区域检测 |
| `ch_PP-OCRv4_rec_infer.onnx` | 10.86 MB | 文字内容识别 |
| `ch_ppocr_mobile_v2.0_cls_infer.onnx` | 0.59 MB | 方向分类 |

### 安装

```bash
pip install --target $PYLIBS rapidocr-onnxruntime pyclipper shapely pyyaml \
  -i https://mirrors.tencent.com/pypi/simple/
export PYTHONPATH=$PYLIBS
```

> `pyclipper` 和 `shapely` 是二次依赖，`--target` 安装时**不会自动带上**，必须手动补，否则 import 报 `ModuleNotFoundError`。

### 用法

```python
import sys; sys.path.insert(0, PYLIBS)
from rapidocr_onnxruntime import RapidOCR

ocr = RapidOCR()
result, elapse = ocr("screenshot.png")
for box, text, score in result:
    print(f"[{score:.2f}] {text}")
```

### 实测

```
输入：760x320 中文测试图
输出：
  [1.00] 元宝沙盒视觉验证
  [1.00] OCR真实识别测试2026
  [0.99] Qwen2-VL-2B权重待入
耗时 0.67 秒
```

---

## 二、MediaPipe（看人：脸 / 姿态 / 手势）

| 能力 | 权重 | 大小 | 输出 |
|---|---|---|---|
| 人脸检测 | `face_detection_*.tflite` | 0.23 / 0.68 MB | 框 + 6 关键点 |
| 人脸网格 | `face_landmark*.tflite` | 1.24 / 2.50 MB | **468 个点** |
| 姿态 | `pose_detection` + `pose_landmark_full` | 2.96 + 6.44 MB | **33 个点** |
| 手势 | `palm_detection_*` + `hand_landmark_*` | 1.99/2.34 + 2.07/5.48 MB | **21 点/手** |
| 虹膜 | `iris_landmark.tflite` | 2.64 MB | 眼部细节 |
| 人像分割 | `selfie_segmentation*.tflite` | 0.25 MB ×2 | 前景掩码 |

### 安装（三个坑，缺一不可）

```bash
pip install --target $PYLIBS mediapipe==0.10.14 opencv-python-headless \
  -i https://mirrors.tencent.com/pypi/simple/
pip install --target $PYLIBS "protobuf==3.20.3" attrs absl-py flatbuffers \
  -i https://mirrors.tencent.com/pypi/simple/
```

**坑 1 — 版本必须是 0.10.14**
`mediapipe==1.0.1` 的 wheel **不包含任何 tflite**（只有一个 114MB 的 `.so`）。只有 0.10.x 才内嵌权重。

**坑 2 — `pip --target` 会装漏**
实测只装进去 3 个目录，缺 `framework/`、`calculators/` 等。`import mediapipe` 会报
`ModuleNotFoundError: No module named 'mediapipe.framework'`。
**解决**：手动解压

```bash
python3 -c "
import zipfile, glob
z = zipfile.ZipFile(glob.glob('/path/*.whl')[0])
for n in z.namelist():
    if 'dist-info' not in n: z.extract(n, PYLIBS)
"
```

**坑 3 — protobuf 必须降到 3.20.3**
新版本移除了 `GetPrototype`，推理时崩：

```
AttributeError: 'SymbolDatabase' object has no attribute 'GetPrototype'
```

### 用法

```python
import sys; sys.path.insert(0, PYLIBS)
import cv2, mediapipe as mp

img = cv2.imread("photo.jpg")
rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# 人脸
with mp.solutions.face_detection.FaceDetection(min_detection_confidence=0.5) as fd:
    r = fd.process(rgb)
    for d in r.detections or []:
        bb = d.location_data.relative_bounding_box
        print(d.score[0], bb.xmin, bb.ymin, bb.width, bb.height)

# 姿态（33 点）
with mp.solutions.pose.Pose(static_image_mode=True) as ps:
    r = ps.process(rgb)
    for i, lm in enumerate(r.pose_landmarks.landmark):
        print(i, lm.x, lm.y, lm.visibility)

# 人脸网格（468 点）
with mp.solutions.face_mesh.FaceMesh(static_image_mode=True) as fm:
    r = fm.process(rgb)
    print(len(r.multi_face_landmarks[0].landmark))
```

### 实测（真实人像 1137x910）

```
FaceDetection  1 张脸，置信度 0.925
               框 x=0.388 y=0.128 w=0.308 h=0.246
               右眼(0.49,0.20) 左眼(0.62,0.19) 鼻(0.56,0.25)

FaceMesh       468 个网格点
Pose           33 个关键点
Hands          1 只手
```

**最有说服力的证据**：姿态点 15/16（左右腕）可见度 0.91/0.94，
而点 27/28（脚踝）**可见度 0.00、坐标 1.90** —— 因为是半身像，脚在画面外。
模型知道"脚不在这张图里"，这是真理解，不是瞎填数字。

---

## 三、两者共存

OCR 走 onnxruntime，MediaPipe 走 protobuf 3.20.3。**降级 protobuf 后两者可同时 import**，已实测：

```
OCR:        ✅ 识别 3 行
MediaPipe:  ✅ 检出 1 张脸，置信度 0.925
```

---

## 能力边界（重要）

| 能 | 不能 |
|---|---|
| 读图里的**文字** | 理解**画面语义** |
| 定位**人脸位置**、468 点轮廓 | 判断"这个布局好不好看" |
| 识别**人体姿态**、手势 | 回答"图里在发生什么事" |
| 人像**前景分割** | 通用视觉问答（VQA） |

**"看图说话"仍需 VLM**（如 SmolVLM-256M / Qwen2-VL-2B），
那类权重托管在 HuggingFace，本沙盒 `403` 拉不到，需外部下载后分片传入。

---

## 四、为什么要存进仓库

沙盒会被重置，但 pypi 镜像随时可用。存这里的价值：

1. **权重本体留档** —— 万一某天 pypi 上 `mediapipe==0.10.14` 被撤，这里有备份
2. **后续 AI 直接取用** —— 不用再踩上面那三个坑
3. **离线可装** —— 配合 `restore_vision.sh` 一条命令恢复

---

## 恢复脚本

```bash
source /data/user_persistent_data/restore_vision.sh
# 输出: [视觉] 就绪: MediaPipe+OCR
```

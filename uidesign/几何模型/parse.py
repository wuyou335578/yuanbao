#!/usr/bin/env python3
"""OmniParser 架构的 UI 屏幕解析器（onnxruntime，无 torch）
  icon_detect.onnx : YOLOv8 单类可交互元素检测 (OmniParser icon_detect)
  配合 rapidocr 做文字识别 -> 输出带文字标注的 UI 元素清单
"""
import sys, os, numpy as np
from PIL import Image
import onnxruntime as ort

D = os.path.dirname(os.path.abspath(__file__))
CONF, IOU = 0.05, 0.10

_so = ort.SessionOptions(); _so.log_severity_level = 3
_s = None
def sess():
    global _s
    if _s is None:
        _s = ort.InferenceSession(os.path.join(D, "icon_detect.onnx"), _so,
                                  providers=["CPUExecutionProvider"])
    return _s

def letterbox(im, size=640):
    """等比缩放到 640x640，灰白填充，返回 (张量, scale, padx, pady)"""
    w0, h0 = im.size
    s = min(size / w0, size / h0)
    nw, nh = int(round(w0 * s)), int(round(h0 * s))
    r = im.resize((nw, nh), Image.BILINEAR)
    canvas = Image.new("RGB", (size, size), (114, 114, 114))
    canvas.paste(r, ((size - nw) // 2, (size - nh) // 2))
    a = np.asarray(canvas, dtype=np.float32) / 255.0
    return np.transpose(a, (2, 0, 1))[None], s, (size - nw) // 2, (size - nh) // 2

def nms(boxes, scores, thr=IOU):
    order = np.argsort(-scores)
    keep = []
    for i in order:
        ok = True
        for k in keep:
            xx1, yy1 = max(boxes[i][0], boxes[k][0]), max(boxes[i][1], boxes[k][1])
            xx2, yy2 = min(boxes[i][2], boxes[k][2]), min(boxes[i][3], boxes[k][3])
            inter = max(0, xx2 - xx1) * max(0, yy2 - yy1)
            a1 = (boxes[i][2]-boxes[i][0]) * (boxes[i][3]-boxes[i][1])
            a2 = (boxes[k][2]-boxes[k][0]) * (boxes[k][3]-boxes[k][1])
            if inter / max(1e-6, a1 + a2 - inter) > thr:
                ok = False; break
        if ok: keep.append(i)
    return keep

def detect(path, conf=CONF):
    im = Image.open(path).convert("RGB")
    w0, h0 = im.size
    x, s, px, py = letterbox(im)
    raw = sess().run(None, {"images": x})[0].reshape(5, 8400)
    cx, cy, bw, bh, cf = raw[0], raw[1], raw[2], raw[3], raw[4]
    m = cf > conf
    idx = np.nonzero(m)[0]
    if len(idx) == 0: return []
    boxes = np.stack([(cx[idx]-bw[idx]/2 - px)/s, (cy[idx]-bh[idx]/2 - py)/s,
                      (cx[idx]+bw[idx]/2 - px)/s, (cy[idx]+bh[idx]/2 - py)/s], axis=1)
    boxes[:, 0::2] = np.clip(boxes[:, 0::2], 0, w0)
    boxes[:, 1::2] = np.clip(boxes[:, 1::2], 0, h0)
    keep = nms(boxes, cf[idx])
    out = []
    for i in keep:
        x1, y1, x2, y2 = boxes[i]
        out.append({"bbox": [round(float(v), 1) for v in (x1, y1, x2, y2)],
                    "conf": round(float(cf[idx][i]), 3)})
    out.sort(key=lambda d: (d["bbox"][1], d["bbox"][0]))
    return out

if __name__ == "__main__":
    p = sys.argv[1]
    top = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    r = detect(p)
    im = Image.open(p); print(f"图像 {im.size}  检出 {len(r)} 个元素")
    for i, e in enumerate(r[:top]):
        x1, y1, x2, y2 = e["bbox"]
        print(f" {i+1:3d}. conf={e['conf']:.2f} ({x1:6.0f},{y1:6.0f})-({x2:6.0f},{y2:6.0f}) "
              f"{x2-x1:5.0f}x{y2-y1:5.0f}")

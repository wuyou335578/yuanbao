#!/usr/bin/env python3
"""UI 理解闭环: icon_detect 框元素 -> 逐个裁剪 -> icon_caption 语义描述

用法: python3 ui_understand.py <UI截图> [像素密度]
"""
import os, sys, time
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/data/user_persistent_data/toklibs")
import onnxruntime as ort

ICON_DETECT = "/data/user_persistent_data/uiparse/icon_detect.onnx"
PROMPT = "What does the image describe?"


def detect(img_path, conf_th=0.05, iou_th=0.10):
    """YOLOv8 单类可交互元素检测"""
    im = Image.open(img_path).convert("RGB")
    w0, h0 = im.size
    s = ort.InferenceSession(ICON_DETECT, providers=["CPUExecutionProvider"])
    # letterbox 到 640
    side = 640
    scale = min(side / w0, side / h0)
    nw, nh = int(w0 * scale), int(h0 * scale)
    res = im.resize((nw, nh), Image.BILINEAR)
    canvas = Image.new("RGB", (side, side), (114, 114, 114))
    canvas.paste(res, ((side - nw) // 2, (side - nh) // 2))
    a = np.asarray(canvas, dtype=np.float32) / 255.0
    x = np.transpose(a, (2, 0, 1))[None]
    out = s.run(None, {s.get_inputs()[0].name: x})[0]
    # (1,5,N) 或 (1,N,5)
    if out.shape[1] == 5:
        out = out[0].T  # -> (N,5)
    else:
        out = out[0]
    boxes = []
    for cx, cy, bw, bh, conf in out:
        if conf < conf_th:
            continue
        boxes.append([cx, cy, bw, bh, float(conf)])
    # NMS
    boxes.sort(key=lambda b: -b[4])
    keep = []
    for b in boxes:
        ok = True
        for k in keep:
            if iou(b, k) > iou_th:
                ok = False
                break
        if ok:
            keep.append(b)
    # 还原到原图坐标
    pad_x, pad_y = (side - nw) // 2, (side - nh) // 2
    res_boxes = []
    for cx, cy, bw, bh, conf in keep:
        x1 = (cx - bw / 2 - pad_x) / scale
        y1 = (cy - bh / 2 - pad_y) / scale
        x2 = (cx + bw / 2 - pad_x) / scale
        y2 = (cy + bh / 2 - pad_y) / scale
        res_boxes.append([max(0, x1), max(0, y1), min(w0, x2), min(h0, y2), conf])
    return im, res_boxes


def iou(a, b):
    ax1, ay1 = a[0] - a[2] / 2, a[1] - a[3] / 2
    ax2, ay2 = a[0] + a[2] / 2, a[1] + a[3] / 2
    bx1, by1 = b[0] - b[2] / 2, b[1] - b[3] / 2
    bx2, by2 = b[0] + b[2] / 2, b[1] + b[3] / 2
    ix, iy = max(0, min(ax2, bx2) - max(ax1, bx1)), max(0, min(ay2, by2) - max(ay1, by1))
    inter = ix * iy
    ua = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / ua if ua > 0 else 0


def main():
    if len(sys.argv) < 2:
        print("用法: python3 ui_understand.py <UI截图> [密度]")
        sys.exit(1)
    img_path = sys.argv[1]
    dens = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0

    t0 = time.time()
    im, boxes = detect(img_path)
    print(f"[{time.time()-t0:.1f}s] icon_detect 检出 {len(boxes)} 个元素", flush=True)

    import importlib.util
    spec = importlib.util.spec_from_file_location("ic", os.path.join(HERE, "ic_run.py"))
    ic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ic)
    ic._load()
    print(f"[{time.time()-t0:.1f}s] icon_caption 加载完成\n", flush=True)

    print(f"{'#':>2} {'尺寸(dp)':>12} {'位置':>14} {'conf':>5}  描述")
    print("-" * 78)
    for i, (x1, y1, x2, y2, conf) in enumerate(boxes):
        crop = im.crop((int(x1), int(y1), int(x2), int(y2)))
        tmp = "/tmp/_ui_crop.png"
        crop.save(tmp)
        # 补边: 小图标放大到 64 以上便于识别
        cw, ch = crop.size
        try:
            cap = ic.infer(tmp, PROMPT, 24)
        except Exception as e:
            cap = f"<失败 {type(e).__name__}>"
        wdp, hdp = int((x2 - x1) / dens), int((y2 - y1) / dens)
        print(f"{i:>2} {wdp:>5}x{hdp:<6} @({int(x1/dens):>3},{int(y1/dens):>3}) {conf:>5.2f}  {cap}", flush=True)
    print(f"\n[总用时 {time.time()-t0:.1f}s]")


if __name__ == "__main__":
    main()

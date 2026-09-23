#!/usr/bin/env python3
"""UI 审计：YOLO 元素检测 + OCR 文字标注 + dp 换算（默认 @3x）"""
import sys
sys.path.append('/data/user_persistent_data/pylibs')
import parse
from rapidocr_onnxruntime import RapidOCR

img = sys.argv[1]
den = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
els = parse.detect(img)
res, _ = RapidOCR()(img)
texts = [(t, [b[0][0], b[0][1], b[2][0], b[2][1]]) for b, t, s in (res or [])]
print(f"{img}  元素 {len(els)} 个 / 文字 {len(texts)} 段  (1dp = {den}px)\n")
for e in els:
    x1, y1, x2, y2 = e['bbox']
    lab = [t for t, bx in texts
           if x1 <= (bx[0]+bx[2])/2 <= x2 and y1 <= (bx[1]+bx[3])/2 <= y2]
    print(f" conf={e['conf']:.2f} ({x1:5.0f},{y1:5.0f})-({x2:5.0f},{y2:5.0f}) "
          f"{int((x2-x1)/den):3d}x{int((y2-y1)/den):3d}dp  {' | '.join(lab)}")

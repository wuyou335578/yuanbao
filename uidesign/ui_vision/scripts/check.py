#!/usr/bin/env python3
"""把审计结果和设计规范对比，标出超标项
用法: python3 check.py <截图> <规范json> [密度]
规范 json 格式: {"登录按钮":{"h":[48,48],"w":[312,312]}, "输入框":{"h":[48,48]}}
  h/w 单位 dp，写 [最小,最大]；匹配方式：元素 OCR 文字包含键名
"""
import sys, json
sys.path.append('/data/user_persistent_data/pylibs')
import parse
from rapidocr_onnxruntime import RapidOCR

img, spec_f = sys.argv[1], sys.argv[2]
den = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
spec = json.load(open(spec_f))
els = parse.detect(img)
res, _ = RapidOCR()(img)
texts = [(t, [b[0][0], b[0][1], b[2][0], b[2][1]]) for b, t, s in (res or [])]

print(f"{img}  元素 {len(els)}\n")
bad = 0
for e in els:
    x1, y1, x2, y2 = e['bbox']
    lab = [t for t, bx in texts
           if x1 <= (bx[0]+bx[2])/2 <= x2 and y1 <= (bx[1]+bx[3])/2 <= y2]
    name = " ".join(lab) or "(无文字)"
    w, h = (x2-x1)/den, (y2-y1)/den
    flag = ""
    for k, lim in spec.items():
        if k in name:
            if 'h' in lim and not (lim["h"][0]-6 <= h <= lim["h"][1]+6):
                flag += f"  ✗高 {h:.0f}dp 应为 {lim['h'][0]}~{lim['h'][1]}"
                bad += 1
            if 'w' in lim and not (lim["w"][0]-6 <= w <= lim["w"][1]+6):
                flag += f"  ✗宽 {w:.0f}dp 应为 {lim['w'][0]}~{lim['w'][1]}"
                bad += 1
    print(f" {'✗' if flag else '✓'} {w:5.0f}x{h:4.0f}dp  {name[:26]:28s}{flag}")
print(f"\n超标 {bad} 项")

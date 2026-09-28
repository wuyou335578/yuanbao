#!/usr/bin/env python3
"""几何图形精确分析：OpenCV 提取数学级参数（圆心/半径/顶点/角度/边长/颜色）
用法: python3 geo_analyze.py <图片> [--json out.json]
特点: 给精确数值，不猜语义。适合圆/三角/矩形/多边形/直线/网格。
     语义判断（这是什么图标）请用 icon_caption，本脚本只管测量。
"""
import sys, os, json, math
import cv2
import numpy as np


def dedup_circles(cs, tol=12):
    """霍夫圆会重复检出同心圆/同一圆，按 (x,y,r) 近似去重"""
    kept = []
    for c in sorted(cs, key=lambda t: -t[2]):
        x, y, r = c
        dup = False
        for kx, ky, kr in kept:
            if abs(x - kx) < tol and abs(y - ky) < tol and abs(r - kr) < tol:
                dup = True
                break
        if not dup:
            kept.append(c)
    return kept


def dedup_lines(L, ang_tol=3, dist_tol=10):
    """合并近似共线的线段"""
    out = []
    for x1, y1, x2, y2 in L:
        ang = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180
        length = math.hypot(x2 - x1, y2 - y1)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dup = False
        for o in out:
            if abs(o['angle'] - ang) < ang_tol:
                # 点到直线距离近似：用中点距离粗判
                if math.hypot(mx - o['mx'], my - o['my']) < dist_tol:
                    dup = True
                    o['length'] = max(o['length'], length)
                    break
        if not dup:
            out.append({'angle': round(ang, 1), 'length': round(length),
                        'mx': mx, 'my': my})
    return out


def analyze(path):
    im = cv2.imread(path)
    if im is None:
        raise SystemExit("读不了图: %s" % path)
    h, w = im.shape[:2]
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    res = {'image': path, 'size': [w, h], 'circles': [], 'shapes': [], 'lines': []}

    # 圆
    blur = cv2.medianBlur(gray, 5)
    circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, 1, 40,
                               param1=100, param2=30, minRadius=10, maxRadius=0)
    if circles is not None:
        cs = [tuple(map(int, np.round(c))) for c in circles[0]]
        for x, y, r in dedup_circles(cs):
            if not (0 <= x < w and 0 <= y < h):
                continue
            b, g, rr = im[y, x].tolist()
            res['circles'].append({'center': [x, y], 'radius': r,
                                   'color_rgb': [int(rr), int(g), int(b)]})

    # 轮廓 -> 多边形拟合
    edges = cv2.Canny(gray, 50, 150)
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    NAMES = {3: '三角形', 4: '四边形', 5: '五边形', 6: '六边形',
             7: '七边形', 8: '八边形', 10: '十边形'}
    for c in sorted(cnts, key=cv2.contourArea, reverse=True):
        a = cv2.contourArea(c)
        if a < 400:
            continue
        peri = cv2.arcLength(c, True)
        ap = cv2.approxPolyDP(c, 0.04 * peri, True)
        n = len(ap)
        M = cv2.moments(c)
        if not M['m00']:
            continue
        cx, cy = int(M['m10'] / M['m00']), int(M['m01'] / M['m00'])
        x, y, bw, bh = cv2.boundingRect(c)
        b, g, rr = (im[cy, cx].tolist() if 0 <= cy < h and 0 <= cx < w else [0, 0, 0])
        verts = [[int(p[0][0]), int(p[0][1])] for p in ap]
        res['shapes'].append({
            'type': NAMES.get(n, '圆/曲线(%d顶点)' % n),
            'vertices': n, 'area': int(a), 'center': [cx, cy],
            'bbox': [int(x), int(y), int(bw), int(bh)],
            'color_rgb': [int(rr), int(g), int(b)],
            'points': verts[:12],
        })

    # 直线
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 60, minLineLength=50, maxLineGap=8)
    if lines is not None:
        for o in dedup_lines(lines.reshape(-1, 4)):
            res['lines'].append({'angle_deg': o['angle'], 'length_px': o['length']})
    return res


def main():
    args = sys.argv[1:]
    if not args:
        print("用法: python3 geo_analyze.py <图片> [--json out.json]")
        return
    path = args[0]
    out = None
    if '--json' in args:
        out = args[args.index('--json') + 1]

    r = analyze(path)
    print("图像: %s  %dx%d" % (os.path.basename(path), r['size'][0], r['size'][1]))

    print("\n圆 (%d):" % len(r['circles']))
    for c in r['circles']:
        print("  圆心%-12s 半径%-4d RGB%s" % (tuple(c['center']), c['radius'], c['color_rgb']))

    print("\n形状 (%d):" % len(r['shapes']))
    for s in r['shapes'][:12]:
        print("  %-14s %d顶点 面积%-7d 中心%-11s 外接%dx%d RGB%s"
              % (s['type'], s['vertices'], s['area'], tuple(s['center']),
                 s['bbox'][2], s['bbox'][3], s['color_rgb']))

    print("\n直线 (%d 条, 已去重):" % len(r['lines']))
    for l in r['lines'][:10]:
        print("  角度%6.1f°  长%d px" % (l['angle_deg'], l['length_px']))

    if out:
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(r, f, ensure_ascii=False, indent=2)
        print("\nJSON: %s" % out)


if __name__ == "__main__":
    main()

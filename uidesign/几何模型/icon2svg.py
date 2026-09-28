#!/usr/bin/env python3
"""图标符号 -> SVG 矢量还原 + 自然语言外观描述 + 像素级复现验证

用法:
  python3 icon2svg.py <图片> <x1,y1,x2,y2> [--out 目录] [--smooth]
      [--fg dark|light]  前景是深色还是浅色，默认自动判断

输出:
  <out>/icon.svg        矢量文件（可无限缩放、可编辑）
  <out>/icon_render.png 由 SVG 逻辑渲染回的位图
  <out>/icon_orig.png   原图裁剪放大
  <out>/icon_cmp.png    左右对比图
  控制台: 外观描述 + 几何参数 + IoU 复现精度

原理:
  RETR_TREE 保留轮廓嵌套层级 -> 按深度交替填充(前/背景) 自动生成"洞"
  -> 等价于 SVG 的 fill-rule="evenodd"，可还原圆环/笑脸/同心等带洞图形
"""
import sys, os, json, math
import cv2
import numpy as np

SCALE = 4          # 小图标放大倍数，提高轮廓精度
EPS = 0.8          # 轮廓简化容差(px, 在放大后的图上)
MIN_AREA = 20      # 放大后最小轮廓面积，滤噪


def depth_of(hier, i):
    """沿 first_parent 上溯，算轮廓嵌套深度"""
    d = 0
    p = hier[0][i][3]
    seen = set()
    while p != -1 and p not in seen:
        seen.add(p)
        d += 1
        p = hier[0][p][3]
    return d


def analyze(img_path, bbox, out_dir, fg=None, smooth=False):
    os.makedirs(out_dir, exist_ok=True)
    im = cv2.imread(img_path)
    if im is None:
        raise SystemExit("读不了图: %s" % img_path)
    H, W = im.shape[:2]
    x1, y1, x2, y2 = [int(v) for v in bbox]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(W, x2), min(H, y2)
    crop = im[y1:y2, x1:x2]

    ow, oh = x2 - x1, y2 - y1
    big = cv2.resize(crop, (ow * SCALE, oh * SCALE), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(os.path.join(out_dir, "icon_orig.png"), big)

    gray = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    ratio = float((th > 0).sum()) / th.size
    # 前景应是少数派；若 OTSU 把背景当成了白，则反相
    if fg == "dark":
        need_inv = ratio > 0.5
    elif fg == "light":
        need_inv = ratio < 0.5
    else:
        need_inv = ratio > 0.5
    if need_inv:
        th = cv2.bitwise_not(th)
    fg_ratio = float((th > 0).sum()) / th.size

    cnts, hier = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if hier is None:
        hier = np.array([[[-1, -1, -1, -1]] * len(cnts)])

    # 取前景主色
    mask = (th > 0)
    if mask.sum() > 0:
        px = big[mask].reshape(-1, 3).astype(float)
        med = np.median(px, axis=0)          # BGR
        fg_rgb = (int(med[2]), int(med[1]), int(med[0]))
    else:
        fg_rgb = (0, 0, 0)

    shapes = []
    for i, c in enumerate(cnts):
        a = cv2.contourArea(c)
        if a < MIN_AREA:
            continue
        d = depth_of(hier, i)
        peri = cv2.arcLength(c, True)
        ap = cv2.approxPolyDP(c, EPS, True)
        if len(ap) < 3:
            continue
        pts = ap.reshape(-1, 2)
        M = cv2.moments(c)
        cx = int(M["m10"] / M["m00"]) if M["m00"] else int(pts[:, 0].mean())
        cy = int(M["m01"] / M["m00"]) if M["m00"] else int(pts[:, 1].mean())
        bx, by, bw, bh = cv2.boundingRect(ap)
        # 圆度: 4*pi*A/P^2, 正圆=1
        circ = 4 * math.pi * a / (peri * peri) if peri > 0 else 0
        shapes.append({
            "depth": d, "area": float(a), "vertices": len(ap),
            "center": [cx, cy], "bbox": [int(bx), int(by), int(bw), int(bh)],
            "circularity": round(circ, 3),
            "pts": pts.tolist(),
        })
    # 按深度升序绘制，保证洞被正确挖掉
    shapes.sort(key=lambda s: s["depth"])

    # ---- 生成 SVG ----
    bw, bh = big.shape[1], big.shape[0]
    paths = []
    for s in shapes:
        fill = "#%02x%02x%02x" % fg_rgb if s["depth"] % 2 == 0 else "#FFFFFF"
        d = "M" + " L".join("%.1f %.1f" % (p[0], p[1]) for p in s["pts"]) + " Z"
        paths.append('  <path d="%s" fill="%s"/>' % (d, fill))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
           'viewBox="0 0 %d %d">\n' % (bw, bh, bw, bh))
    svg += ' <g fill-rule="evenodd">\n' + "\n".join(paths) + "\n </g>\n</svg>\n"
    with open(os.path.join(out_dir, "icon.svg"), "w") as f:
        f.write(svg)

    # ---- 按同样逻辑渲染回位图，验证还原度 ----
    canvas = np.full((bh, bw, 3), 255, np.uint8)
    for s in shapes:
        col = (fg_rgb[2], fg_rgb[1], fg_rgb[0]) if s["depth"] % 2 == 0 else (255, 255, 255)
        cv2.fillPoly(canvas, [np.array(s["pts"], np.int32)], col)
    cv2.imwrite(os.path.join(out_dir, "icon_render.png"), canvas)

    inter = np.logical_and(mask, canvas.mean(axis=2) < 200).sum()
    union = np.logical_or(mask, canvas.mean(axis=2) < 200).sum()
    iou = inter / union if union else 0

    cmp_img = np.hstack([big, canvas])
    cv2.imwrite(os.path.join(out_dir, "icon_cmp.png"), cmp_img)

    return {
        "orig_size": [ow, oh],
        "fg_rgb": fg_rgb,
        "fg_area_ratio": round(fg_ratio, 4),
        "shapes": [{k: v for k, v in s.items() if k != "pts"} for s in shapes],
        "iou": round(float(iou), 4),
    }


def describe(r):
    """把几何参数翻译成人话"""
    ss = r["shapes"]
    lines = []
    lines.append("尺寸 %dx%d px   主色 RGB%s   墨迹占比 %.1f%%"
                 % (r["orig_size"][0], r["orig_size"][1],
                    tuple(r["fg_rgb"]), r["fg_area_ratio"] * 100))
    lines.append("由 %d 个闭合区域构成:" % len(ss))
    for i, s in enumerate(ss):
        w, h = s["bbox"][2], s["bbox"][3]
        c = s["circularity"]
        if c > 0.85:
            kind = "圆形/椭圆"
        elif s["vertices"] <= 4:
            kind = {3: "三角形", 4: "四边形"}.get(s["vertices"], "多边形")
        elif 5 <= s["vertices"] <= 8:
            kind = "%d边形" % s["vertices"]
        else:
            kind = "不规则曲线形(%d顶点)" % s["vertices"]
        role = "实体" if s["depth"] % 2 == 0 else "镂空(洞)"
        lines.append("  %d. %-18s %s  外接 %dx%d  圆度%.2f  中心%s"
                     % (i + 1, kind, role, w, h, c, tuple(s["center"])))
    return "\n".join(lines)


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return
    path, bbox_s = a[0], a[1]
    bbox = [float(v) for v in bbox_s.replace(",", " ").split()]
    if len(bbox) != 4:
        print("bbox 格式: x1,y1,x2,y2")
        return
    out = "icon_out"
    if "--out" in a:
        out = a[a.index("--out") + 1]
    fg = None
    if "--fg" in a:
        fg = a[a.index("--fg") + 1]

    r = analyze(path, bbox, out, fg=fg)
    print("=" * 62)
    print("外观描述")
    print("=" * 62)
    print(describe(r))
    print("\n复现精度 IoU = %.4f  (1.0 为完全一致, >0.85 肉眼基本无差)" % r["iou"])
    print("\n产物: %s/" % out)
    for f in ["icon.svg", "icon_render.png", "icon_orig.png", "icon_cmp.png"]:
        print("   %-18s %d B" % (f, os.path.getsize(os.path.join(out, f))))


if __name__ == "__main__":
    main()

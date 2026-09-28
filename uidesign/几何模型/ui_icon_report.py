#!/usr/bin/env python3
"""UI 图标符号一键解析：检出 -> 命名 -> 说长什么样 -> 画出 SVG

用法:
  python3 ui_icon_report.py <截图> [--dp 3] [--out 目录]

对每个检出的元素输出四件事:
  1. 名字     —— 模板匹配(内置25个 + 自定义库)，低分标"未在图标库中"不乱猜
  2. 文字     —— OCR
  3. 长什么样 —— 几何构成: 几个闭合区域/圆度/外接尺寸/线宽/主色
  4. 一模一样 —— SVG 矢量文件 + 渲染回位图 + IoU 复现精度

产物目录:
  report.txt        人读报告
  report.json       机读数据
  cmp_all.png       所有图标 原图|还原 对比拼图
  icon_<id>/        每个元素一套 svg/orig/render/cmp
"""
import sys, os, json, math
import cv2
import numpy as np
from PIL import Image, ImageDraw

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)


def detect(path, conf=0.05):
    import importlib.util
    spec = importlib.util.spec_from_file_location("pp", os.path.join(D, "parse.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.detect(path, conf)


def ocr_all(path):
    for c in ("/data/user_persistent_data/pylibs", D):
        if c not in sys.path:
            sys.path.append(c)
    try:
        from rapidocr_onnxruntime import RapidOCR
        res, _ = RapidOCR()(path)
        return [(r[0], r[1], float(r[2])) for r in res] if res else []
    except Exception:
        return []


def box_center(b):
    return ((b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return
    path = a[0]
    dp = 3.0
    if "--dp" in a:
        dp = float(a[a.index("--dp") + 1])
    out = "icon_report"
    if "--out" in a:
        out = a[a.index("--out") + 1]
    os.makedirs(out, exist_ok=True)

    im = Image.open(path).convert("RGB")
    W, H = im.size
    print("图像 %dx%d  dp密度%.1f" % (W, H, dp))

    dets = detect(path)
    ocrs = ocr_all(path)
    print("检出 %d 个元素, OCR %d 段文字\n" % (len(dets), len(ocrs)))

    import icon2svg, icon_match

    tiles = []
    rows = []
    for i, d in enumerate(dets):
        x1, y1, x2, y2 = [int(v) for v in d["bbox"]]
        sub = os.path.join(out, "icon_%d" % i)
        txt = " ".join(
            t for ob, t, cf in ocrs
            if x1 <= box_center(ob)[0] <= x2 and y1 <= box_center(ob)[1] <= y2).strip()

        rec = {"id": i, "bbox_px": [x1, y1, x2, y2],
               "size_dp": [round((x2 - x1) / dp, 1), round((y2 - y1) / dp, 1)],
               "conf": d["conf"], "text": txt}
        try:
            r = icon2svg.analyze(path, (x1, y1, x2, y2), sub)
            rec.update({"iou": r["iou"], "fg_rgb": r["fg_rgb"],
                        "shapes": r["shapes"]})
            names = icon_match.match(Image.open(
                os.path.join(sub, "icon_orig.png")).convert("L"), top=3)
            rec["names"] = [{"name": n, "score": round(s, 3)} for n, s in names]
            o = cv2.imread(os.path.join(sub, "icon_orig.png"))
            rr = cv2.imread(os.path.join(sub, "icon_render.png"))
            if o is not None and rr is not None:
                h = max(o.shape[0], rr.shape[0])
                pad = lambda m: cv2.copyMakeBorder(
                    m, 0, h - m.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
                tiles.append(np.hstack([pad(o), pad(rr)]))
            print("#%d  %s  IoU=%.3f  候选: %s" %
                  (i, os.path.basename(sub), r["iou"],
                   "/".join("%s(%.2f)" % (n, s) for n, s in names[:2])))
        except Exception as e:
            rec["error"] = str(e)[:80]
            print("#%d  失败: %s" % (i, str(e)[:60]))
        rows.append(rec)

    # 报告
    L = []
    L.append("UI 图标符号解析报告")
    L.append("=" * 62)
    L.append("图像: %s  %dx%d  dp=%.1f\n" % (os.path.basename(path), W, H, dp))
    for r in rows:
        L.append("-" * 62)
        nm = r.get("names", [{}])[0]
        name = nm.get("name", "?")
        score = nm.get("score", 0)
        tag = name if name != "未在图标库中" else "未在图标库中(最接近 %.2f)" % score
        L.append("#%d  识别: %s" % (r["id"], tag))
        if r.get("text"):
            L.append("     文字: %s" % r["text"])
        L.append("     位置: %s dp   尺寸: %sx%s dp   置信: %.2f"
                 % (tuple(r["bbox_px"][:2]), r["size_dp"][0], r["size_dp"][1], r["conf"]))
        if "shapes" in r and r["shapes"]:
            L.append("     外观: %s" % icon2svg.describe({
                "orig_size": [r["bbox_px"][2] - r["bbox_px"][0],
                              r["bbox_px"][3] - r["bbox_px"][1]],
                "fg_rgb": r["fg_rgb"],
                "fg_area_ratio": max(s["area"] for s in r["shapes"]) /
                                 max(1.0, (r["bbox_px"][2] - r["bbox_px"][0]) *
                                     (r["bbox_px"][3] - r["bbox_px"][1]) * 16),
                "shapes": r["shapes"]}).replace("\n", "\n     "))
            L.append("     复现: IoU=%.3f   SVG: icon_%d/icon.svg"
                     % (r["iou"], r["id"]))
        if len(r.get("names", [])) > 1:
            L.append("     其他候选: %s" % ", ".join(
                "%s %.2f" % (n["name"], n["score"]) for n in r["names"][1:]))
        L.append("")
    open(os.path.join(out, "report.txt"), "w", encoding="utf-8").write("\n".join(L))
    json.dump(rows, open(os.path.join(out, "report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    if tiles:
        w = max(t.shape[1] for t in tiles)
        tiles = [cv2.copyMakeBorder(t, 0, 0, 0, w - t.shape[1],
                                    cv2.BORDER_CONSTANT, value=(255, 255, 255))
                 for t in tiles]
        cv2.imwrite(os.path.join(out, "cmp_all.png"), np.vstack(tiles))
        print("\n对比拼图(左原图|右还原): %s/cmp_all.png" % out)
    print("报告: %s/report.txt" % out)
    print("\n" + "\n".join(L[:40]))


if __name__ == "__main__":
    main()

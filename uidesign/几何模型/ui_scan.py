#!/usr/bin/env python3
"""UI 截图一键理解：icon_detect 框元素 -> OCR 读文字 -> icon_caption 说语义
用法: python3 ui_scan.py <图片> [--caption] [--dp 3]
  --caption  开启语义描述（慢，每个元素 1~2 秒）
  --dp N     像素密度，用于换算 dp（默认 3，即 3x 图）
输出: 控制台清单 + <图片名>_scan.json + 标注图 <图片名>_boxed.png
"""
import sys, os, json, time
import numpy as np
from PIL import Image, ImageDraw

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)


def detect(path, conf=0.05):
    import importlib.util
    spec = importlib.util.spec_from_file_location("p", os.path.join(D, "parse.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.detect(path, conf)


def _append_ocr_path():
    """把持久盘 pylibs 追加到路径末尾，保证系统 numpy 优先（坏 numpy 会缺 _expired_attrs_2_0）"""
    for c in ("/data/user_persistent_data/pylibs", D):
        if c not in sys.path:
            sys.path.append(c)


def ocr_all(path):
    """返回 [(bbox4, text, conf)]，失败返回 []"""
    _append_ocr_path()
    try:
        from rapidocr_onnxruntime import RapidOCR
        eng = RapidOCR()
        res, _ = eng(path)
        if not res:
            return []
        return [(r[0], r[1], float(r[2])) for r in res]
    except Exception as e:
        print("  [OCR 不可用: %s]" % str(e)[:60])
        return []


def box_center(b):
    return ((b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2)


def in_box(pt, box, pad=0):
    x, y = pt
    x1, y1 = min(p[0] for p in box), min(p[1] for p in box)
    x2, y2 = max(p[0] for p in box), max(p[1] for p in box)
    return x1 - pad <= x <= x2 + pad and y1 - pad <= y <= y2 + pad


def match_text(bbox, ocrs):
    """找出落在该框内的文字，按左到右拼接"""
    x1, y1, x2, y2 = bbox
    hits = []
    for ob, txt, cf in ocrs:
        c = box_center(ob)
        if x1 <= c[0] <= x2 and y1 <= c[1] <= y2:
            hits.append((min(p[0] for p in ob), txt, cf))
    hits.sort()
    return " ".join(h[1] for h in hits).strip()


def main():
    args = [a for a in sys.argv[1:]]
    if not args:
        print("用法: python3 ui_scan.py <图片> [--caption] [--dp 3]")
        return
    path = args[0]
    use_cap = "--caption" in args
    dp = 3.0
    if "--dp" in args:
        dp = float(args[args.index("--dp") + 1])

    if not os.path.exists(path):
        print("文件不存在:", path)
        return

    im = Image.open(path).convert("RGB")
    W, H = im.size
    print("图像: %s  %dx%d  (dp 密度 %.1f)" % (os.path.basename(path), W, H, dp))

    t0 = time.time()
    dets = detect(path)
    print("[1/3] icon_detect 检出 %d 个元素  (%.1fs)" % (len(dets), time.time() - t0))

    t1 = time.time()
    ocrs = ocr_all(path)
    print("[2/3] OCR 读出 %d 段文字  (%.1fs)" % (len(ocrs), time.time() - t1))

    items = []
    for i, d in enumerate(dets):
        x1, y1, x2, y2 = d["bbox"]
        txt = match_text((x1, y1, x2, y2), ocrs)
        items.append({
            "id": i,
            "bbox_px": [round(x1), round(y1), round(x2), round(y2)],
            "size_px": [round(x2 - x1), round(y2 - y1)],
            "size_dp": [round((x2 - x1) / dp, 1), round((y2 - y1) / dp, 1)],
            "pos_dp": [round(x1 / dp, 1), round(y1 / dp, 1)],
            "conf": d["conf"],
            "text": txt,
        })

    if use_cap:
        print("[3/3] icon_caption 语义描述中（每个 1~2 秒）...")
        try:
            capdir = os.path.join(D, "icon_caption")
            for c in (capdir,):
                if c not in sys.path:
                    sys.path.append(c)
            from ic_run import infer as cap_run
        except Exception as e:
            print("  [icon_caption 不可用: %s]" % str(e)[:60])
            cap_run = None
        if cap_run:
            os.makedirs("/tmp/uicrop", exist_ok=True)
            for it in items:
                x1, y1, x2, y2 = it["bbox_px"]
                crop = im.crop((max(0, x1 - 4), max(0, y1 - 4), min(W, x2 + 4), min(H, y2 + 4)))
                cp = "/tmp/uicrop/c%d.png" % it["id"]
                crop.save(cp)
                try:
                    it["caption"] = str(cap_run(cp)).strip()
                except Exception as e:
                    it["caption"] = "?"
                print("   #%d -> %s" % (it["id"], it["caption"]))
    else:
        print("[3/3] 语义描述已跳过（加 --caption 开启）")

    print("\n" + "=" * 68)
    print("元素清单（共 %d 个）" % len(items))
    print("=" * 68)
    for it in items:
        w, h = it["size_dp"]
        x, y = it["pos_dp"]
        line = "%2d. %sx%s dp @(%s,%s) conf=%.2f" % (it["id"], w, h, x, y, it["conf"])
        if it.get("text"):
            line += "  文字: %s" % it["text"]
        if it.get("caption"):
            line += "  | 语义: %s" % it["caption"]
        print(line)

    # 标注图
    dr = ImageDraw.Draw(im)
    for it in items:
        x1, y1, x2, y2 = it["bbox_px"]
        dr.rectangle([x1, y1, x2, y2], outline=(255, 0, 0), width=3)
        dr.text((x1 + 4, y1 + 4), "#%d" % it["id"], fill=(255, 0, 0))
    base = os.path.splitext(path)[0]
    boxed = base + "_boxed.png"
    im.save(boxed)

    jf = base + "_scan.json"
    with open(jf, "w", encoding="utf-8") as f:
        json.dump({"image": path, "size": [W, H], "dp": dp, "items": items},
                  f, ensure_ascii=False, indent=2)
    print("\n标注图: %s" % boxed)
    print("JSON:   %s" % jf)


if __name__ == "__main__":
    main()

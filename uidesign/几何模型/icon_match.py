#!/usr/bin/env python3
"""图标识别: 归一化 mask + IoU 模板匹配（纯几何, 不靠 AI 猜测）

为什么不用 AI: 实测 icon_caption 在这组图标上 4 个只说对 1 个
（加号对，笑脸/麦克风/声音全错）。模板匹配是数学比对，可复现。

内置 24 个常见图标模板。match() 返回按相似度排序的候选。
"""
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw

N = 64  # 归一化尺寸


def _mk(draw_fn, size=256):
    im = Image.new("L", (size, size), 255)
    d = ImageDraw.Draw(im)
    draw_fn(d, size)
    return im


def _templates():
    """返回 {名称: PIL 灰度图}，白底黑图"""
    T = {}

    def add(name, fn):
        T[name] = _mk(fn)

    def circle_outline(d, s, w=None):
        w = w or max(6, s // 22)
        d.ellipse([s * .08, s * .08, s * .92, s * .92], outline=0, width=w)

    # 圆环系列
    def _cplus(d, s):
        circle_outline(d, s)
        t = max(6, s // 20)
        d.rectangle([s * .27, s * .46, s * .73, s * .54], fill=0)
        d.rectangle([s * .46, s * .27, s * .54, s * .73], fill=0)
    add("圆环加号", _cplus)

    def _cminus(d, s):
        circle_outline(d, s)
        d.rectangle([s * .27, s * .46, s * .73, s * .54], fill=0)
    add("圆环减号", _cminus)

    def _cclose(d, s):
        circle_outline(d, s)
        t = max(6, s // 20)
        d.line([s * .33, s * .33, s * .67, s * .67], fill=0, width=t)
        d.line([s * .67, s * .33, s * .33, s * .67], fill=0, width=t)
    add("圆环关闭", _cclose)

    def _cplay(d, s):
        circle_outline(d, s)
        d.polygon([(s * .40, s * .30), (s * .40, s * .70), (s * .68, s * .50)], fill=0)
    add("圆环播放", _cplay)

    # 基础符号
    def _plus(d, s):
        t = s // 7
        d.rectangle([s * .12, s * .44, s * .88, s * .56], fill=0)
        d.rectangle([s * .44, s * .12, s * .56, s * .88], fill=0)
    add("加号", _plus)

    def _minus(d, s):
        d.rectangle([s * .12, s * .44, s * .88, s * .56], fill=0)
    add("减号", _minus)

    def _close(d, s):
        t = s // 8
        d.line([s * .18, s * .18, s * .82, s * .82], fill=0, width=t)
        d.line([s * .82, s * .18, s * .18, s * .82], fill=0, width=t)
    add("关闭X", _close)

    def _check(d, s):
        t = s // 9
        d.line([s * .20, s * .52, s * .40, s * .72], fill=0, width=t)
        d.line([s * .40, s * .72, s * .82, s * .28], fill=0, width=t)
    add("对勾", _check)

    def _arrow_r(d, s):
        d.rectangle([s * .15, s * .44, s * .78, s * .56], fill=0)
        d.polygon([(s * .70, s * .26), (s * .96, s * .50), (s * .70, s * .74)], fill=0)
    add("右箭头", _arrow_r)

    def _arrow_l(d, s):
        d.rectangle([s * .22, s * .44, s * .85, s * .56], fill=0)
        d.polygon([(s * .30, s * .26), (s * .04, s * .50), (s * .30, s * .74)], fill=0)
    add("左箭头", _arrow_l)

    def _heart(d, s):
        d.ellipse([s * .10, s * .18, s * .55, s * .62], fill=0)
        d.ellipse([s * .45, s * .18, s * .90, s * .62], fill=0)
        d.polygon([(s * .12, s * .48), (s * .50, s * .92), (s * .88, s * .48)], fill=0)
    add("心形", _heart)

    def _star(d, s):
        import math
        pts = []
        for i in range(10):
            a = math.radians(-90 + i * 36)
            r = s * .46 if i % 2 == 0 else s * .19
            pts.append((s / 2 + r * math.cos(a), s / 2 + r * math.sin(a)))
        d.polygon(pts, fill=0)
    add("星形", _star)

    def _smile(d, s):
        w = max(6, s // 20)
        d.ellipse([s * .10, s * .10, s * .90, s * .90], outline=0, width=w)
        r = s * .07
        d.ellipse([s * .34 - r, s * .40 - r, s * .34 + r, s * .40 + r], fill=0)
        d.ellipse([s * .66 - r, s * .40 - r, s * .66 + r, s * .40 + r], fill=0)
        d.arc([s * .28, s * .48, s * .72, s * .80], 20, 160, fill=0, width=w)
    add("笑脸", _smile)

    def _mic(d, s):
        d.rounded_rectangle([s * .38, s * .12, s * .62, s * .58], radius=s * .12, fill=0)
        w = max(5, s // 22)
        d.arc([s * .24, s * .42, s * .76, s * .80], 0, 180, fill=0, width=w)
        d.rectangle([s * .47, s * .78, s * .53, s * .90], fill=0)
        d.rectangle([s * .34, s * .88, s * .66, s * .95], fill=0)
    add("麦克风", _mic)

    def _search(d, s):
        w = max(6, s // 18)
        d.ellipse([s * .12, s * .12, s * .62, s * .62], outline=0, width=w)
        d.line([s * .55, s * .55, s * .90, s * .90], fill=0, width=w + 3)
    add("搜索放大镜", _search)

    def _menu(d, s):
        h = max(6, s // 12)
        for i, y in enumerate([.26, .50, .74]):
            d.rectangle([s * .16, s * y - h / 2, s * .84, s * y + h / 2], fill=0)
    add("汉堡菜单", _menu)

    def _gear(d, s):
        import math
        cx = cy = s / 2
        R, r, n = s * .45, s * .34, 8
        pts = []
        for i in range(n * 2):
            a = math.radians(i * 360 / (n * 2))
            rr = R if i % 2 == 0 else r
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=0)
        d.ellipse([cx - s * .17, cy - s * .17, cx + s * .17, cy + s * .17], fill=255)
    add("齿轮设置", _gear)

    def _bell(d, s):
        d.polygon([(s * .30, s * .34), (s * .70, s * .34), (s * .78, s * .74),
                   (s * .22, s * .74)], fill=0)
        d.rectangle([s * .18, s * .72, s * .82, s * .80], fill=0)
        d.ellipse([s * .44, s * .80, s * .56, s * .92], fill=0)
    add("铃铛通知", _bell)

    def _envelope(d, s):
        w = max(5, s // 22)
        d.rectangle([s * .10, s * .24, s * .90, s * .76], outline=0, width=w)
        d.line([s * .10, s * .24, s * .50, s * .57], fill=0, width=w)
        d.line([s * .90, s * .24, s * .50, s * .57], fill=0, width=w)
    add("信封邮件", _envelope)

    def _lock(d, s):
        w = max(5, s // 20)
        d.arc([s * .28, s * .16, s * .72, s * .62], 180, 360, fill=0, width=w)
        d.rectangle([s * .20, s * .56, s * .80, s * .90], fill=0)
    add("锁", _lock)

    def _eye(d, s):
        w = max(5, s // 22)
        d.arc([s * .08, s * .34, s * .92, s * .74], 0, 180, fill=0, width=w)
        d.arc([s * .08, s * .34, s * .92, s * .74], 180, 360, fill=0, width=w)
        d.ellipse([s * .40, s * .42, s * .60, s * .62], fill=0)
    add("眼睛", _eye)

    def _home(d, s):
        d.polygon([(s * .50, s * .12), (s * .90, s * .48), (s * .82, s * .56),
                   (s * .82, s * .88), (s * .18, s * .88), (s * .18, s * .56),
                   (s * .10, s * .48)], fill=0)
        d.rectangle([s * .40, s * .66, s * .60, s * .88], fill=255)
    add("主页", _home)

    def _trash(d, s):
        w = max(5, s // 20)
        d.rectangle([s * .28, s * .14, s * .72, s * .24], fill=0)
        d.rectangle([s * .42, s * .08, s * .58, s * .16], fill=0)
        d.polygon([(s * .20, s * .26), (s * .80, s * .26), (s * .74, s * .90),
                   (s * .26, s * .90)], outline=0, width=w)
    add("垃圾桶删除", _trash)

    def _camera(d, s):
        d.rounded_rectangle([s * .10, s * .28, s * .90, s * .82], radius=s * .06,
                            outline=0, width=max(5, s // 22))
        d.polygon([(s * .38, s * .28), (s * .50, s * .16), (s * .62, s * .28)], fill=0)
        d.ellipse([s * .34, s * .42, s * .66, s * .72], outline=0, width=max(4, s // 26))
    add("相机", _camera)

    def _user(d, s):
        d.ellipse([s * .30, s * .14, s * .70, s * .54], fill=0)
        d.polygon([(s * .12, s * .92), (s * .12, s * .64), (s * .88, s * .64),
                   (s * .88, s * .92)], fill=0)
    add("用户头像", _user)

    return T


_CACHE = {}


def _norm_mask(pil_or_arr):
    """任意灰度图 -> N×N 的 0/1 mask（黑=1 前景）

    关键两步，缺一不可:
      1) 先裁到前景外框，去掉大片空白 —— 否则形状对不齐，IoU 全崩
      2) OTSU 二值化后再判方向，保证黑=前景
    """
    a = np.asarray(pil_or_arr.convert("L") if hasattr(pil_or_arr, "convert")
                   else pil_or_arr)
    _, t = cv2.threshold(a, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    m = (t < 128).astype(np.uint8)
    # 判前景方向: 看外圈一圈像素，而不是看面积占比。
    # 老写法 m.sum()>50% 就翻转，会把"锁""主页"这类实心图标整个反相 —— 实测踩到
    border = np.concatenate([a[0, :], a[-1, :], a[:, 0], a[:, -1]]).astype(float)
    if border.mean() < 128:      # 外圈是暗的 -> 暗的是背景
        m = 1 - m
    return _to_square(m)


def _to_square(m):
    """裁到前景外框 -> 居中补成正方形 -> 缩放到 N×N

    关键: 必须补成正方形再缩放，不能直接拉伸。
    实测"减号"这种细长条，直接拉伸到 64×64 会变成 100% 前景的实心方块，
    跟"方块"完全无法区分。补成正方形后宽高比得以保留。
    """
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return np.zeros((N, N), np.uint8)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = m.shape
    side = max(h, w)
    pad = np.zeros((side, side), np.uint8)
    pad[(side - h) // 2:(side - h) // 2 + h,
        (side - w) // 2:(side - w) // 2 + w] = m
    return (cv2.resize(pad * 255, (N, N), interpolation=cv2.INTER_AREA) > 100).astype(np.uint8)


UNKNOWN_THRESHOLD = 0.42   # 低于此分一律判"未在图标库中"，不许瞎猜

# 旋转搜索角度。0 放最前，保证正着的时候优先按原样匹配
ROTATIONS = [0, 15, -15, 30, -30, 45, -45]


def _rot_mask(m, deg):
    """mask 绕中心旋转 deg 度。

    注意: 只转、不裁、不改尺寸。因为 m 已经是补成正方形的 N×N，
    旋转后仍是同尺寸同尺度，这样"转过去再转回来"才能精确复原。
    早期版本转完又裁外框再拉伸，尺度会漂，导致旋转补偿失效。
    """
    if deg == 0:
        return m
    im = Image.fromarray(((1 - m) * 255).astype(np.uint8))
    r = im.rotate(deg, resample=Image.BICUBIC, expand=False)
    a = np.asarray(r)
    _, t = cv2.threshold(a, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return (t < 128).astype(np.uint8)


def _iou(a, b):
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter) / union if union else 0.0


def _hu_sim(m, tm):
    """Hu 矩形状相似度，0~1，1=完全一致。

    注意: 只看最外层轮廓，圆环类图标内部的十字/横杠会被丢弃，
    所以圆环加号/减号/关闭的距离都是 0.0000 —— 不能单独用它打分。
    """
    def biggest(x):
        cs, _ = cv2.findContours((x * 255).astype(np.uint8),
                                 cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return max(cs, key=cv2.contourArea) if cs else None
    ca, cb = biggest(m), biggest(tm)
    if ca is None or cb is None:
        return 0.0
    try:
        d = cv2.matchShapes(ca, cb, cv2.CONTOURS_MATCH_I1, 0)
    except cv2.error:
        return 0.0
    return 1.0 / (1.0 + d)


def save_template(name, image, lib=None):
    """把当前图标存进自定义图标库，下次可自动认出。返回路径"""
    lib = lib or os.path.join(os.path.dirname(os.path.abspath(__file__)), "iconlib")
    os.makedirs(lib, exist_ok=True)
    m = _norm_mask(image)
    p = os.path.join(lib, "%s.png" % name)
    cv2.imwrite(p, m * 255)
    return p


def _load_custom():
    lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), "iconlib")
    if not os.path.isdir(lib):
        return {}
    out = {}
    for f in sorted(os.listdir(lib)):
        if f.lower().endswith(".png"):
            a = cv2.imread(os.path.join(lib, f), cv2.IMREAD_GRAYSCALE)
            if a is not None:
                out[os.path.splitext(f)[0]] = (a > 100).astype(np.uint8)
    return out


def load_templates():
    if "T" not in _CACHE:
        T = _templates()
        _CACHE["T"] = {k: _norm_mask(v) for k, v in T.items()}
    return _CACHE["T"]


def match(mask_or_image, top=4, rotate=True):
    """输入 mask 或灰度图，返回 [(名称, 分数), ...] 降序

    打分 = 旋转不变 IoU（在 ROTATIONS 里取最好的那个角度）。
    比 Hu 矩(matchShapes)强在: 保留内部细节，能区分圆环加号/减号/关闭
    （Hu 矩对这三个的距离全是 0.0000，完全分不开）；
    同时又不像固定角度 IoU 那样怕旋转。

    内置库 + 自定义库一起比。最高分低于 UNKNOWN_THRESHOLD 会把第一名
    替换成 "未在图标库中"，避免低分硬套一个错误名字。
    """
    m = _norm_mask(mask_or_image)
    T = dict(load_templates())
    T.update(_load_custom())
    angles = ROTATIONS if rotate else [0]
    out = []
    for name, tm in T.items():
        best, best_deg = 0.0, 0
        for deg in angles:
            v = _iou(m if deg == 0 else _rot_mask(m, deg), tm)
            if v > best:
                best, best_deg = v, deg
        out.append((name, best, best_deg))
    out.sort(key=lambda x: -x[1])
    res = [(n, s) for n, s, _ in out[:top]]
    if res and res[0][1] < UNKNOWN_THRESHOLD:
        res = [("未在图标库中", res[0][1])] + res[:3]
    return res[:top]


def match_detail(mask_or_image, top=4):
    """同 match()，但额外给出每个候选的 IoU / Hu 相似度 / 最佳旋转角，便于排查"""
    m = _norm_mask(mask_or_image)
    T = dict(load_templates())
    T.update(_load_custom())
    out = []
    for name, tm in T.items():
        best, best_deg = 0.0, 0
        for deg in ROTATIONS:
            v = _iou(m if deg == 0 else _rot_mask(m, deg), tm)
            if v > best:
                best, best_deg = v, deg
        out.append({"name": name, "iou_rot": round(best, 4),
                    "iou_0deg": round(_iou(m, tm), 4),
                    "hu": round(_hu_sim(m, tm), 4), "rot_deg": best_deg})
    out.sort(key=lambda d: -d["iou_rot"])
    return out[:top]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python3 icon_match.py <图标图片>")
        print("内置模板:", "、".join(sorted(load_templates().keys())))
        raise SystemExit
    im = Image.open(sys.argv[1]).convert("L")
    res = match(im)
    print("识别结果（IoU 越高越像）:")
    for i, (n, s) in enumerate(res):
        bar = "█" * int(s * 30)
        print("  %d. %-12s %.3f  %s" % (i + 1, n, s, bar))

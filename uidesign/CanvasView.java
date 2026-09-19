package com.yuanbao.uidesign;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.DashPathEffect;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;

/**
 * 原型画布。
 * 设计坐标系（默认 375x667）等比缩放到 View 内居中显示（fit center）。
 * 编辑模式：点击选中、拖拽移动、右下角手柄缩放。
 * 预览模式：点击带 linkTo 的元素触发页面跳转。
 */
public class CanvasView extends View {

    private Page page;
    private Element selected;

    /** 是否预览模式 */
    private boolean previewMode = false;
    private boolean showGrid = true;
    private boolean showOutlines = true;

    private Paint paint;
    private Paint textPaint;
    private Paint selPaint;
    private Paint bgPaint;
    private Paint gridPaint;

    /** 缩放与偏移（设计坐标 → 屏幕） */
    private float scale = 1f;
    private float offX = 0f, offY = 0f;

    /** 拖拽状态 */
    private static final int MODE_NONE = 0;
    private static final int MODE_MOVE = 1;
    private static final int MODE_RESIZE = 2;
    private int mode = MODE_NONE;
    private float lastX, lastY;
    private float downX, downY;
    private static final float HANDLE = 24f;

    private int gridColor = 0xFFE8E8E8;
    private int selColor = 0xFF2196F3;

    public interface SelectionListener {
        void onSelected(Element e);
    }

    public interface NavigateListener {
        void onNavigate(int pageIndex);
    }

    private SelectionListener selListener;
    private NavigateListener navListener;

    public CanvasView(Context c, AttributeSet a) {
        super(c, a);
        init();
    }

    private void init() {
        paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        selPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        selPaint.setStyle(Paint.Style.STROKE);
        selPaint.setColor(selColor);
        selPaint.setStrokeWidth(2f);
        selPaint.setPathEffect(new DashPathEffect(new float[]{8, 6}, 0));
        bgPaint = new Paint();
        bgPaint.setColor(0xFFFFFFFF);
        gridPaint = new Paint();
        gridPaint.setColor(gridColor);
        gridPaint.setStrokeWidth(1f);
    }

    public void setPage(Page p) {
        page = p;
        selected = null;
        invalidate();
    }

    public Page getPage() {
        return page;
    }

    public void setSelected(Element e) {
        selected = e;
        invalidate();
    }

    public Element getSelected() {
        return selected;
    }

    public void setPreviewMode(boolean p) {
        previewMode = p;
        selected = null;
        invalidate();
    }

    public boolean isPreviewMode() {
        return previewMode;
    }

    public void setShowGrid(boolean g) {
        showGrid = g;
        invalidate();
    }

    public boolean isShowGrid() {
        return showGrid;
    }

    public void setSelectionListener(SelectionListener l) {
        selListener = l;
    }

    public void setNavigateListener(NavigateListener l) {
        navListener = l;
    }

    /** 计算 fit center 的缩放与偏移 */
    private void computeTransform() {
        if (page == null) {
            scale = 1f; offX = 0; offY = 0;
            return;
        }
        float vw = getWidth();
        float vh = getHeight();
        float sx = vw / (float) page.width;
        float sy = vh / (float) page.height;
        scale = Math.min(sx, sy);
        offX = (vw - page.width * scale) / 2f;
        offY = (vh - page.height * scale) / 2f;
    }

    private float toDesignX(float sx) {
        return (sx - offX) / scale;
    }

    private float toDesignY(float sy) {
        return (sy - offY) / scale;
    }

    @Override
    protected void onDraw(Canvas c) {
        super.onDraw(c);
        computeTransform();
        if (page == null) return;

        c.save();
        c.translate(offX, offY);
        c.scale(scale, scale);

        // 页面背景
        bgPaint.setColor(page.bgColor);
        c.drawRect(0, 0, page.width, page.height, bgPaint);

        if (showGrid && !previewMode) drawGrid(c);

        // 元素（按列表顺序，末尾在上）
        for (int i = 0; i < page.elements.size(); i++) {
            Element e = page.elements.get(i);
            if (!e.visible) continue;
            drawElement(c, e);
        }

        // 选中框
        if (!previewMode && selected != null && selected.visible) {
            drawSelection(c, selected);
        }
        c.restore();
    }

    private void drawGrid(Canvas c) {
        for (int x = 0; x <= page.width; x += 20) {
            c.drawLine(x, 0, x, page.height, gridPaint);
        }
        for (int y = 0; y <= page.height; y += 20) {
            c.drawLine(0, y, page.width, y, gridPaint);
        }
    }

    private void drawSelection(Canvas c, Element e) {
        selPaint.setColor(selColor);
        selPaint.setStyle(Paint.Style.STROKE);
        selPaint.setPathEffect(new DashPathEffect(new float[]{8 / scale, 6 / scale}, 0));
        selPaint.setStrokeWidth(2f / scale);
        c.drawRect(e.x, e.y, e.x + e.w, e.y + e.h, selPaint);

        // 四角手柄 + 右下缩放区
        Paint hp = new Paint(Paint.ANTI_ALIAS_FLAG);
        hp.setColor(selColor);
        hp.setStyle(Paint.Style.FILL);
        float s = 6f / scale;
        float[][] pts = {
            {e.x, e.y}, {e.x + e.w, e.y},
            {e.x, e.y + e.h}, {e.x + e.w, e.y + e.h}
        };
        for (int i = 0; i < pts.length; i++) {
            c.drawCircle(pts[i][0], pts[i][1], s, hp);
        }
    }

    private void drawElement(Canvas c, Element e) {
        c.save();
        if (e.alpha < 255) {
            c.saveLayerAlpha(e.x - 2, e.y - 2, e.x + e.w + 2, e.y + e.h + 2, e.alpha);
        }
        if (e.rotation != 0) {
            c.rotate(e.rotation, e.x + e.w / 2, e.y + e.h / 2);
        }

        RectF rf = new RectF(e.x, e.y, e.x + e.w, e.y + e.h);
        paint.setStyle(Paint.Style.FILL);
        paint.setColor(e.fill);

        switch (e.type) {
            case Element.RECT:
                if ((e.fill >>> 24) != 0) c.drawRect(rf, paint);
                break;

            case Element.RRECT:
                if ((e.fill >>> 24) != 0) c.drawRoundRect(rf, e.radius, e.radius, paint);
                break;

            case Element.OVAL:
                if ((e.fill >>> 24) != 0) c.drawOval(rf, paint);
                break;

            case Element.TRIANGLE: {
                Path p = new Path();
                p.moveTo(e.x + e.w / 2, e.y);
                p.lineTo(e.x + e.w, e.y + e.h);
                p.lineTo(e.x, e.y + e.h);
                p.close();
                if ((e.fill >>> 24) != 0) c.drawPath(p, paint);
                if (e.strokeWidth > 0 && (e.stroke >>> 24) != 0) {
                    paint.setStyle(Paint.Style.STROKE);
                    paint.setColor(e.stroke);
                    paint.setStrokeWidth(e.strokeWidth);
                    c.drawPath(p, paint);
                }
                break;
            }

            case Element.LINE:
                paint.setStyle(Paint.Style.STROKE);
                paint.setColor(e.stroke);
                paint.setStrokeWidth(Math.max(e.strokeWidth, 1f));
                c.drawLine(e.x, e.y + e.h / 2, e.x + e.w, e.y + e.h / 2, paint);
                break;

            case Element.TEXT:
                drawText(c, e, e.x + 4, e.y + e.h / 2);
                break;

            case Element.BUTTON:
                if ((e.fill >>> 24) != 0) c.drawRoundRect(rf, e.radius, e.radius, paint);
                if (e.strokeWidth > 0 && (e.stroke >>> 24) != 0) {
                    paint.setStyle(Paint.Style.STROKE);
                    paint.setColor(e.stroke);
                    paint.setStrokeWidth(e.strokeWidth);
                    c.drawRoundRect(rf, e.radius, e.radius, paint);
                }
                drawText(c, e, e.x, e.y + e.h / 2);
                break;

            case Element.INPUT:
                if ((e.fill >>> 24) != 0) c.drawRoundRect(rf, e.radius, e.radius, paint);
                if (e.strokeWidth > 0 && (e.stroke >>> 24) != 0) {
                    paint.setStyle(Paint.Style.STROKE);
                    paint.setColor(e.stroke);
                    paint.setStrokeWidth(e.strokeWidth);
                    c.drawRoundRect(rf, e.radius, e.radius, paint);
                }
                drawText(c, e, e.x + 12, e.y + e.h / 2);
                break;

            case Element.IMAGE:
                if ((e.fill >>> 24) != 0) c.drawRect(rf, paint);
                if (e.strokeWidth > 0 && (e.stroke >>> 24) != 0) {
                    paint.setStyle(Paint.Style.STROKE);
                    paint.setColor(e.stroke);
                    paint.setStrokeWidth(e.strokeWidth);
                    c.drawRect(rf, paint);
                }
                // 对角叉
                paint.setStyle(Paint.Style.STROKE);
                paint.setColor(e.textColor);
                paint.setStrokeWidth(1.5f);
                c.drawLine(e.x, e.y, e.x + e.w, e.y + e.h, paint);
                c.drawLine(e.x + e.w, e.y, e.x, e.y + e.h, paint);
                drawText(c, e, e.x, e.y + e.h / 2);
                break;

            case Element.CHECKBOX: {
                float box = Math.min(e.h * 0.6f, 22f);
                float by = e.y + (e.h - box) / 2;
                RectF bf = new RectF(e.x + 4, by, e.x + 4 + box, by + box);
                paint.setStyle(Paint.Style.FILL);
                paint.setColor(e.fill);
                c.drawRoundRect(bf, 4, 4, paint);
                paint.setStyle(Paint.Style.STROKE);
                paint.setColor(e.stroke);
                paint.setStrokeWidth(e.strokeWidth);
                c.drawRoundRect(bf, 4, 4, paint);
                // 勾
                paint.setStyle(Paint.Style.STROKE);
                paint.setColor(e.stroke);
                paint.setStrokeWidth(2.5f);
                c.drawLine(e.x + 8, by + box * 0.5f, e.x + 8 + box * 0.3f, by + box * 0.75f, paint);
                c.drawLine(e.x + 8 + box * 0.3f, by + box * 0.75f, e.x + 4 + box - 6, by + box * 0.28f, paint);
                drawText(c, e, e.x + box + 14, e.y + e.h / 2);
                break;
            }

            case Element.SWITCH: {
                float r = e.h / 2f;
                paint.setStyle(Paint.Style.FILL);
                paint.setColor(e.fill);
                c.drawRoundRect(rf, r, r, paint);
                if (e.strokeWidth > 0 && (e.stroke >>> 24) != 0) {
                    paint.setStyle(Paint.Style.STROKE);
                    paint.setColor(e.stroke);
                    paint.setStrokeWidth(e.strokeWidth);
                    c.drawRoundRect(rf, r, r, paint);
                }
                Paint kp = new Paint(Paint.ANTI_ALIAS_FLAG);
                kp.setColor(0xFFFFFFFF);
                kp.setStyle(Paint.Style.FILL);
                float kr = r * 0.72f;
                c.drawCircle(e.x + e.w - r, e.y + r, kr, kp);
                break;
            }

            case Element.HOTSPOT:
                paint.setStyle(Paint.Style.FILL);
                paint.setColor(e.fill);
                c.drawRect(rf, paint);
                paint.setStyle(Paint.Style.STROKE);
                paint.setColor(e.stroke);
                paint.setStrokeWidth(e.strokeWidth);
                paint.setPathEffect(new DashPathEffect(new float[]{6, 4}, 0));
                c.drawRect(rf, paint);
                paint.setPathEffect(null);
                break;

            case Element.ICON: {
                // 简化图标：圆形底 + 十字
                paint.setStyle(Paint.Style.FILL);
                paint.setColor(e.fill);
                float cx = e.x + e.w / 2, cy = e.y + e.h / 2;
                c.drawCircle(cx, cy, Math.min(e.w, e.h) / 2, paint);
                Paint ip = new Paint(Paint.ANTI_ALIAS_FLAG);
                ip.setColor(0xFFFFFFFF);
                ip.setStyle(Paint.Style.STROKE);
                ip.setStrokeWidth(3f);
                float d = Math.min(e.w, e.h) * 0.22f;
                c.drawLine(cx - d, cy, cx + d, cy, ip);
                c.drawLine(cx, cy - d, cx, cy + d, ip);
                break;
            }
        }

        // 通用描边（矩形/圆角/椭圆）
        if (e.strokeWidth > 0 && (e.stroke >>> 24) != 0) {
            if (e.type == Element.RECT || e.type == Element.RRECT || e.type == Element.OVAL) {
                paint.setStyle(Paint.Style.STROKE);
                paint.setColor(e.stroke);
                paint.setStrokeWidth(e.strokeWidth);
                if (e.type == Element.RECT) c.drawRect(rf, paint);
                else if (e.type == Element.RRECT) c.drawRoundRect(rf, e.radius, e.radius, paint);
                else c.drawOval(rf, paint);
            }
        }

        c.restore();
        if (e.alpha < 255) c.restore();
    }

    private void drawText(Canvas c, Element e, float tx, float ty) {
        if (e.text == null || e.text.length() == 0) return;
        textPaint.setStyle(Paint.Style.FILL);
        textPaint.setColor(e.textColor);
        textPaint.setTextSize(e.textSize);
        Paint.Align al = Paint.Align.CENTER;
        float x = tx;
        if (e.textAlign == 0) {
            al = Paint.Align.LEFT;
        } else if (e.textAlign == 2) {
            al = Paint.Align.RIGHT;
            x = e.x + e.w - 4;
        } else {
            x = e.x + e.w / 2;
        }
        textPaint.setTextAlign(al);
        Paint.FontMetrics fm = textPaint.getFontMetrics();
        float base = ty - (fm.ascent + fm.descent) / 2;
        c.drawText(e.text, x, base, textPaint);
    }

    /** 命中测试：从上层往下找 */
    private Element hitTest(float dx, float dy) {
        if (page == null) return null;
        for (int i = page.elements.size() - 1; i >= 0; i--) {
            Element e = page.elements.get(i);
            if (!e.visible) continue;
            if (dx >= e.x && dx <= e.x + e.w && dy >= e.y && dy <= e.y + e.h) {
                return e;
            }
        }
        return null;
    }

    @Override
    public boolean onTouchEvent(MotionEvent ev) {
        if (page == null) return true;
        float sx = ev.getX(), sy = ev.getY();
        float dx = toDesignX(sx), dy = toDesignY(sy);

        switch (ev.getAction()) {
            case MotionEvent.ACTION_DOWN:
                downX = dx; downY = dy;
                lastX = dx; lastY = dy;
                if (previewMode) {
                    mode = MODE_NONE;
                    return true;
                }
                if (selected != null && !selected.locked) {
                    // 右下角缩放区
                    float hx = selected.x + selected.w;
                    float hy = selected.y + selected.h;
                    if (Math.abs(dx - hx) < HANDLE && Math.abs(dy - hy) < HANDLE) {
                        mode = MODE_RESIZE;
                        return true;
                    }
                }
                Element hit = hitTest(dx, dy);
                selected = hit;
                if (selListener != null) selListener.onSelected(selected);
                if (hit != null && !hit.locked) {
                    mode = MODE_MOVE;
                    // 选中的提到最上层？保持原层级，仅移动
                } else {
                    mode = MODE_NONE;
                }
                invalidate();
                return true;

            case MotionEvent.ACTION_MOVE:
                if (previewMode) return true;
                if (selected == null || selected.locked) return true;
                if (mode == MODE_MOVE) {
                    selected.x += dx - lastX;
                    selected.y += dy - lastY;
                } else if (mode == MODE_RESIZE) {
                    float nw = dx - selected.x;
                    float nh = dy - selected.y;
                    if (nw > 12) selected.w = nw;
                    if (nh > 12) selected.h = nh;
                }
                lastX = dx; lastY = dy;
                invalidate();
                return true;

            case MotionEvent.ACTION_UP:
                if (previewMode) {
                    float ddx = Math.abs(dx - downX);
                    float ddy = Math.abs(dy - downY);
                    if (ddx < 8 && ddy < 8) {
                        // 从上层往下找带跳转的元素
                        for (int i = page.elements.size() - 1; i >= 0; i--) {
                            Element e = page.elements.get(i);
                            if (!e.visible) continue;
                            if (e.linkTo >= 0
                                && dx >= e.x && dx <= e.x + e.w
                                && dy >= e.y && dy <= e.y + e.h) {
                                if (navListener != null) navListener.onNavigate(e.linkTo);
                                return true;
                            }
                        }
                    }
                    return true;
                }
                mode = MODE_NONE;
                invalidate();
                return true;
        }
        return true;
    }

    /** 导出当前页为 PNG */
    public Bitmap exportBitmap() {
        if (page == null) return null;
        Bitmap bmp = Bitmap.createBitmap(page.width, page.height, Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(bmp);
        boolean oldGrid = showGrid;
        boolean oldPreview = previewMode;
        Element oldSel = selected;
        showGrid = false;
        previewMode = true;
        selected = null;
        // 直接按 1:1 绘制
        bgPaint.setColor(page.bgColor);
        c.drawRect(0, 0, page.width, page.height, bgPaint);
        for (int i = 0; i < page.elements.size(); i++) {
            Element e = page.elements.get(i);
            if (e.visible) drawElement(c, e);
        }
        showGrid = oldGrid;
        previewMode = oldPreview;
        selected = oldSel;
        return bmp;
    }
}

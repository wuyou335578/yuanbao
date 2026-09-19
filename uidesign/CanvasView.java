package com.yuanbao.uidesign;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;

import java.util.ArrayList;

public class CanvasView extends View {

    public static final int T_PATH = 0;
    public static final int T_RECT = 1;
    public static final int T_OVAL = 2;
    public static final int T_LINE = 3;
    public static final int T_TEXT = 4;
    public static final int T_ERASE = 5;

    public static class Shape {
        int type;
        int color;
        float width;
        float sx, sy, ex, ey;
        Path path;
        String text;
    }

    private ArrayList<Shape> shapes = new ArrayList<Shape>();
    private Shape current;
    private int tool = T_PATH;
    private int color;
    private float strokeWidth = 6f;
    private Paint paint;
    private Paint bgPaint;
    private boolean gridOn = true;

    /** 以下三项从 res/values 读取，避免在代码里硬编码 */
    private int gridSize;
    private int gridColor;
    private int bgColor;

    public CanvasView(Context c, AttributeSet a) {
        super(c, a);
        init();
    }

    private void init() {
        gridSize = getResources().getDimensionPixelSize(R.dimen.grid_size);
        gridColor = getResources().getColor(R.color.canvas_grid);
        bgColor = getResources().getColor(R.color.canvas_bg);
        color = getResources().getColor(R.color.swatch_blue);

        paint = new Paint();
        paint.setAntiAlias(true);
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeCap(Paint.Cap.ROUND);
        paint.setStrokeJoin(Paint.Join.ROUND);
        bgPaint = new Paint();
        bgPaint.setColor(bgColor);
    }

    public void setTool(int t) { tool = t; }
    public int getTool() { return tool; }
    public void setColor(int c) { color = c; }
    public int getColor() { return color; }
    public void setStrokeWidth(float w) { strokeWidth = w; }
    public float getStrokeWidth() { return strokeWidth; }
    public void setGrid(boolean g) { gridOn = g; invalidate(); }
    public boolean getGrid() { return gridOn; }

    public void undo() {
        if (shapes.size() > 0) {
            shapes.remove(shapes.size() - 1);
            invalidate();
        }
    }

    public void clear() {
        shapes.clear();
        current = null;
        invalidate();
    }

    public int getShapeCount() { return shapes.size(); }

    public void addText(String s, float x, float y) {
        Shape sh = new Shape();
        sh.type = T_TEXT;
        sh.color = color;
        sh.width = strokeWidth;
        sh.text = s;
        sh.sx = x;
        sh.sy = y;
        shapes.add(sh);
        invalidate();
    }

    @Override
    public boolean onTouchEvent(MotionEvent e) {
        float x = e.getX();
        float y = e.getY();
        switch (e.getAction()) {
            case MotionEvent.ACTION_DOWN:
                if (tool == T_ERASE) {
                    removeNear(x, y);
                    return true;
                }
                if (tool == T_TEXT) {
                    if (textListener != null) textListener.onTextPoint(x, y);
                    return true;
                }
                current = new Shape();
                current.type = tool;
                current.color = color;
                current.width = strokeWidth;
                current.sx = x;
                current.sy = y;
                current.ex = x;
                current.ey = y;
                if (tool == T_PATH) {
                    current.path = new Path();
                    current.path.moveTo(x, y);
                }
                invalidate();
                return true;

            case MotionEvent.ACTION_MOVE:
                if (current == null) return true;
                current.ex = x;
                current.ey = y;
                if (tool == T_PATH && current.path != null) {
                    current.path.lineTo(x, y);
                }
                invalidate();
                return true;

            case MotionEvent.ACTION_UP:
                if (current != null) {
                    // 忽略过小的误触（文本除外）
                    float dx = Math.abs(current.ex - current.sx);
                    float dy = Math.abs(current.ey - current.sy);
                    if (current.type == T_PATH || dx > 4 || dy > 4) {
                        shapes.add(current);
                    }
                    current = null;
                    invalidate();
                }
                return true;
        }
        return true;
    }

    private void removeNear(float x, float y) {
        for (int i = shapes.size() - 1; i >= 0; i--) {
            Shape s = shapes.get(i);
            float cx = (s.sx + s.ex) / 2;
            float cy = (s.sy + s.ey) / 2;
            if (Math.abs(cx - x) < 40 && Math.abs(cy - y) < 40) {
                shapes.remove(i);
                invalidate();
                return;
            }
        }
    }

    @Override
    protected void onDraw(Canvas c) {
        super.onDraw(c);
        c.drawRect(0, 0, getWidth(), getHeight(), bgPaint);
        if (gridOn) drawGrid(c);
        for (int i = 0; i < shapes.size(); i++) {
            drawShape(c, shapes.get(i));
        }
        if (current != null) drawShape(c, current);
    }

    private void drawGrid(Canvas c) {
        Paint g = new Paint();
        g.setColor(gridColor);
        g.setStrokeWidth(1);
        for (int x = 0; x < getWidth(); x += gridSize) {
            c.drawLine(x, 0, x, getHeight(), g);
        }
        for (int y = 0; y < getHeight(); y += gridSize) {
            c.drawLine(0, y, getWidth(), y, g);
        }
    }

    private void drawShape(Canvas c, Shape s) {
        paint.setColor(s.color);
        paint.setStrokeWidth(s.width);
        if (s.type == T_TEXT) {
            paint.setStyle(Paint.Style.FILL);
            paint.setTextSize(s.width * 6f + 20f);
            c.drawText(s.text == null ? "" : s.text, s.sx, s.sy, paint);
            paint.setStyle(Paint.Style.STROKE);
            return;
        }
        if (s.type == T_PATH) {
            paint.setStyle(Paint.Style.STROKE);
            if (s.path != null) c.drawPath(s.path, paint);
            return;
        }
        float l = Math.min(s.sx, s.ex);
        float t = Math.min(s.sy, s.ey);
        float r = Math.max(s.sx, s.ex);
        float b = Math.max(s.sy, s.ey);
        RectF rf = new RectF(l, t, r, b);
        if (s.type == T_RECT) {
            c.drawRect(rf, paint);
        } else if (s.type == T_OVAL) {
            c.drawOval(rf, paint);
        } else if (s.type == T_LINE) {
            c.drawLine(s.sx, s.sy, s.ex, s.ey, paint);
        }
    }

    public Bitmap exportBitmap() {
        Bitmap bmp = Bitmap.createBitmap(getWidth(), getHeight(), Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(bmp);
        c.drawRect(0, 0, getWidth(), getHeight(), bgPaint);
        if (gridOn) drawGridOn(c);
        for (int i = 0; i < shapes.size(); i++) {
            drawShape(c, shapes.get(i));
        }
        return bmp;
    }

    private void drawGridOn(Canvas c) {
        Paint g = new Paint();
        g.setColor(gridColor);
        g.setStrokeWidth(1);
        for (int x = 0; x < getWidth(); x += gridSize) c.drawLine(x, 0, x, getHeight(), g);
        for (int y = 0; y < getHeight(); y += gridSize) c.drawLine(0, y, getWidth(), y, g);
    }

    public interface TextPointListener {
        void onTextPoint(float x, float y);
    }

    private TextPointListener textListener;

    public void setTextPointListener(TextPointListener l) {
        textListener = l;
    }
}

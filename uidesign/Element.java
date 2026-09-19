package com.yuanbao.uidesign;

import org.json.JSONObject;

/**
 * 原型元素数据模型。
 * 纯数据类，绘制逻辑在 CanvasView 中按 type 分发。
 */
public class Element {

    /** 元素类型常量 */
    public static final int RECT = 0;
    public static final int RRECT = 1;
    public static final int OVAL = 2;
    public static final int TRIANGLE = 3;
    public static final int LINE = 4;
    public static final int TEXT = 5;
    public static final int BUTTON = 6;
    public static final int INPUT = 7;
    public static final int IMAGE = 8;
    public static final int CHECKBOX = 9;
    public static final int SWITCH = 10;
    public static final int HOTSPOT = 11;
    public static final int ICON = 12;

    public static final String[] TYPE_NAMES = {
        "矩形", "圆角矩形", "椭圆", "三角形", "直线",
        "文本", "按钮", "输入框", "图片", "复选框",
        "开关", "热区", "图标"
    };

    public int type = RECT;
    public String name = "元素";

    /** 位置与尺寸（画布坐标） */
    public float x = 100, y = 100, w = 160, h = 80;

    /** 填充色（ARGB） */
    public int fill = 0xFF2196F3;
    /** 描边色（ARGB） */
    public int stroke = 0xFF1976D2;
    public float strokeWidth = 2f;
    /** 圆角半径 */
    public float radius = 8f;
    /** 不透明度 0-255 */
    public int alpha = 255;
    /** 旋转角度 */
    public float rotation = 0f;

    /** 文本属性 */
    public String text = "";
    public float textSize = 16f;
    public int textColor = 0xFF212121;
    /** 0=左 1=中 2=右 */
    public int textAlign = 1;

    /** 是否显示、是否锁定 */
    public boolean visible = true;
    public boolean locked = false;

    /** 点击跳转目标页索引，-1 表示无交互 */
    public int linkTo = -1;

    public Element() {
    }

    public Element(int type) {
        this.type = type;
        this.name = typeName(type);
        applyDefault(type);
    }

    /** 各类型默认样式 */
    private void applyDefault(int t) {
        switch (t) {
            case RECT:
                fill = 0xFFBBDEFB; stroke = 0xFF2196F3; w = 160; h = 100; radius = 0;
                break;
            case RRECT:
                fill = 0xFFE3F2FD; stroke = 0xFF2196F3; w = 160; h = 90; radius = 16;
                break;
            case OVAL:
                fill = 0xFFFFCDD2; stroke = 0xFFF44336; w = 120; h = 120; radius = 0;
                break;
            case TRIANGLE:
                fill = 0xFFC8E6C9; stroke = 0xFF4CAF50; w = 120; h = 110; radius = 0;
                break;
            case LINE:
                fill = 0x00000000; stroke = 0xFF616161; w = 200; h = 4;
                strokeWidth = 3; radius = 0;
                break;
            case TEXT:
                fill = 0x00000000; stroke = 0x00000000;
                text = "文本内容"; textSize = 18; w = 180; h = 40; radius = 0;
                break;
            case BUTTON:
                fill = 0xFF2196F3; stroke = 0xFF1976D2;
                text = "按钮"; textColor = 0xFFFFFFFF; textSize = 16;
                w = 140; h = 48; radius = 24; strokeWidth = 0;
                break;
            case INPUT:
                fill = 0xFFFFFFFF; stroke = 0xFFBDBDBD;
                text = "请输入"; textColor = 0xFF757575; textSize = 15;
                textAlign = 0; w = 200; h = 48; radius = 6; strokeWidth = 2;
                break;
            case IMAGE:
                fill = 0xFFE0E0E0; stroke = 0xFF9E9E9E;
                text = "图片"; textColor = 0xFF9E9E9E; textSize = 14;
                w = 160; h = 120; radius = 4; strokeWidth = 1;
                break;
            case CHECKBOX:
                fill = 0xFFFFFFFF; stroke = 0xFF2196F3;
                text = "选项"; textColor = 0xFF212121; textSize = 15;
                textAlign = 0; w = 140; h = 40; radius = 4; strokeWidth = 2;
                break;
            case SWITCH:
                fill = 0xFF4CAF50; stroke = 0xFF388E3C;
                w = 64; h = 32; radius = 16; strokeWidth = 0;
                break;
            case HOTSPOT:
                fill = 0x33F44336; stroke = 0xFFFF0000;
                strokeWidth = 2; radius = 4; w = 140; h = 60;
                break;
            case ICON:
                fill = 0xFF757575; stroke = 0x00000000;
                w = 48; h = 48; radius = 0; strokeWidth = 0;
                break;
        }
    }

    public static String typeName(int t) {
        if (t >= 0 && t < TYPE_NAMES.length) return TYPE_NAMES[t];
        return "元素";
    }

    /** 是否带文本 */
    public boolean hasText() {
        return type == TEXT || type == BUTTON || type == INPUT
            || type == IMAGE || type == CHECKBOX;
    }

    /** 复制 */
    public Element copy() {
        Element e = new Element();
        e.type = type; e.name = name;
        e.x = x; e.y = y; e.w = w; e.h = h;
        e.fill = fill; e.stroke = stroke; e.strokeWidth = strokeWidth;
        e.radius = radius; e.alpha = alpha; e.rotation = rotation;
        e.text = text; e.textSize = textSize; e.textColor = textColor;
        e.textAlign = textAlign;
        e.visible = visible; e.locked = locked; e.linkTo = linkTo;
        return e;
    }

    public JSONObject toJson() {
        JSONObject o = new JSONObject();
        try {
            o.put("type", type);
            o.put("name", name);
            o.put("x", (double) x);
            o.put("y", (double) y);
            o.put("w", (double) w);
            o.put("h", (double) h);
            o.put("fill", fill);
            o.put("stroke", stroke);
            o.put("strokeWidth", (double) strokeWidth);
            o.put("radius", (double) radius);
            o.put("alpha", alpha);
            o.put("rotation", (double) rotation);
            o.put("text", text);
            o.put("textSize", (double) textSize);
            o.put("textColor", textColor);
            o.put("textAlign", textAlign);
            o.put("visible", visible);
            o.put("locked", locked);
            o.put("linkTo", linkTo);
        } catch (Exception e) {
        }
        return o;
    }

    public static Element fromJson(JSONObject o) {
        Element e = new Element();
        e.type = o.optInt("type", RECT);
        e.name = o.optString("name", typeName(e.type));
        e.x = (float) o.optDouble("x", 100);
        e.y = (float) o.optDouble("y", 100);
        e.w = (float) o.optDouble("w", 160);
        e.h = (float) o.optDouble("h", 80);
        e.fill = o.optInt("fill", 0xFF2196F3);
        e.stroke = o.optInt("stroke", 0xFF1976D2);
        e.strokeWidth = (float) o.optDouble("strokeWidth", 2);
        e.radius = (float) o.optDouble("radius", 8);
        e.alpha = o.optInt("alpha", 255);
        e.rotation = (float) o.optDouble("rotation", 0);
        e.text = o.optString("text", "");
        e.textSize = (float) o.optDouble("textSize", 16);
        e.textColor = o.optInt("textColor", 0xFF212121);
        e.textAlign = o.optInt("textAlign", 1);
        e.visible = o.optBoolean("visible", true);
        e.locked = o.optBoolean("locked", false);
        e.linkTo = o.optInt("linkTo", -1);
        return e;
    }
}

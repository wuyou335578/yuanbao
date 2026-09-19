package com.yuanbao.uidesign;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;

/**
 * 页面：持有元素列表，元素按列表顺序决定层级（末尾为最上层）。
 */
public class Page {

    public String name = "页面 1";
    /** 画布尺寸（设计稿基准） */
    public int width = 375;
    public int height = 667;
    /** 背景色 */
    public int bgColor = 0xFFFFFFFF;
    public ArrayList<Element> elements = new ArrayList<Element>();

    public Page() {
    }

    public Page(String name) {
        this.name = name;
    }

    public JSONObject toJson() {
        JSONObject o = new JSONObject();
        try {
            o.put("name", name);
            o.put("width", width);
            o.put("height", height);
            o.put("bgColor", bgColor);
            JSONArray arr = new JSONArray();
            for (int i = 0; i < elements.size(); i++) {
                arr.put(elements.get(i).toJson());
            }
            o.put("elements", arr);
        } catch (Exception e) {
        }
        return o;
    }

    public static Page fromJson(JSONObject o) {
        Page p = new Page();
        p.name = o.optString("name", "页面");
        p.width = o.optInt("width", 375);
        p.height = o.optInt("height", 667);
        p.bgColor = o.optInt("bgColor", 0xFFFFFFFF);
        JSONArray arr = o.optJSONArray("elements");
        if (arr != null) {
            for (int i = 0; i < arr.length(); i++) {
                JSONObject eo = arr.optJSONObject(i);
                if (eo != null) p.elements.add(Element.fromJson(eo));
            }
        }
        return p;
    }
}

package com.yuanbao.uidesign;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.util.ArrayList;

/**
 * 项目：多页面容器，负责 JSON 存档与 HTML 导出。
 */
public class Project {

    public String name = "未命名项目";
    public ArrayList<Page> pages = new ArrayList<Page>();

    public Project() {
        pages.add(new Page("页面 1"));
    }

    public JSONObject toJson() {
        JSONObject o = new JSONObject();
        try {
            o.put("name", name);
            JSONArray arr = new JSONArray();
            for (int i = 0; i < pages.size(); i++) {
                arr.put(pages.get(i).toJson());
            }
            o.put("pages", arr);
        } catch (Exception e) {
        }
        return o;
    }

    public static Project fromJson(JSONObject o) {
        Project p = new Project();
        p.pages.clear();
        p.name = o.optString("name", "未命名项目");
        JSONArray arr = o.optJSONArray("pages");
        if (arr != null) {
            for (int i = 0; i < arr.length(); i++) {
                JSONObject po = arr.optJSONObject(i);
                if (po != null) p.pages.add(Page.fromJson(po));
            }
        }
        if (p.pages.size() == 0) p.pages.add(new Page("页面 1"));
        return p;
    }

    /**
     * 导出离线 HTML：所有页面渲染为绝对定位 div，
     * 带 linkTo 的元素可点击跳转。
     */
    public String toHtml() {
        StringBuilder sb = new StringBuilder();
        sb.append("<!DOCTYPE html><html><head><meta charset=\"utf-8\">");
        sb.append("<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">");
        sb.append("<title>").append(esc(name)).append("</title>");
        sb.append("<style>");
        sb.append("body{margin:0;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;background:#f5f5f5}");
        sb.append(".page{position:relative;margin:0 auto;overflow:hidden;display:none}");
        sb.append(".page.active{display:block}");
        sb.append(".el{position:absolute;box-sizing:border-box;display:flex;align-items:center;justify-content:center}");
        sb.append(".nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #ddd;");
        sb.append("display:flex;overflow-x:auto;padding:6px 0;z-index:99}");
        sb.append(".nav button{flex:0 0 auto;margin:0 3px;padding:8px 12px;border:1px solid #2196F3;");
        sb.append("background:#fff;color:#2196F3;border-radius:6px;font-size:13px;cursor:pointer}");
        sb.append(".nav button.on{background:#2196F3;color:#fff}");
        sb.append("</style></head><body>");

        for (int i = 0; i < pages.size(); i++) {
            Page pg = pages.get(i);
            sb.append("<div class=\"page").append(i == 0 ? " active" : "");
            sb.append("\" id=\"p").append(i).append("\" style=\"width:").append(pg.width);
            sb.append("px;height:").append(pg.height).append("px;background:");
            sb.append(cssColor(pg.bgColor)).append("\">");
            for (int j = 0; j < pg.elements.size(); j++) {
                Element e = pg.elements.get(j);
                if (!e.visible) continue;
                sb.append(htmlElement(e, i));
            }
            sb.append("</div>");
        }

        sb.append("<div class=\"nav\">");
        for (int i = 0; i < pages.size(); i++) {
            sb.append("<button onclick=\"go(").append(i).append(")\" id=\"b").append(i);
            sb.append("\">").append(esc(pages.get(i).name)).append("</button>");
        }
        sb.append("</div>");

        sb.append("<script>");
        sb.append("function go(i){for(var k=0;k<").append(pages.size()).append(";k++){");
        sb.append("document.getElementById('p'+k).className='page';");
        sb.append("document.getElementById('b'+k).className='';}");
        sb.append("document.getElementById('p'+i).className='page active';");
        sb.append("document.getElementById('b'+i).className='on';}");
        sb.append("</script></body></html>");
        return sb.toString();
    }

    private String htmlElement(Element e, int pageIdx) {
        StringBuilder s = new StringBuilder();
        s.append("<div class=\"el\" style=\"");
        s.append("left:").append(e.x).append("px;top:").append(e.y).append("px;");
        s.append("width:").append(e.w).append("px;height:").append(e.h).append("px;");
        if (e.alpha < 255) s.append("opacity:").append(e.alpha / 255f).append(";");
        if ((e.fill & 0xFF000000) != 0) s.append("background:").append(cssColor(e.fill)).append(";");
        if (e.strokeWidth > 0 && (e.stroke & 0xFF000000) != 0) {
            s.append("border:").append(e.strokeWidth).append("px solid ").append(cssColor(e.stroke)).append(";");
        }
        if (e.radius > 0) s.append("border-radius:").append(e.radius).append("px;");
        if (e.rotation != 0) s.append("transform:rotate(").append(e.rotation).append("deg);");

        String ta = "center";
        if (e.textAlign == 0) ta = "flex-start";
        else if (e.textAlign == 2) ta = "flex-end";
        s.append("align-items:center;justify-content:").append(ta).append(";");

        if (e.linkTo >= 0 && e.linkTo < pages.size()) {
            s.append("cursor:pointer;\" onclick=\"go(").append(e.linkTo).append(")");
        }
        s.append("\">");
        if (e.hasText() && e.text != null && e.text.length() > 0) {
            s.append("<span style=\"color:").append(cssColor(e.textColor));
            s.append(";font-size:").append(e.textSize).append("px;padding:0 8px\">");
            s.append(esc(e.text)).append("</span>");
        }
        s.append("</div>");
        return s.toString();
    }

    private static String cssColor(int argb) {
        int a = (argb >>> 24) & 0xFF;
        int r = (argb >>> 16) & 0xFF;
        int g = (argb >>> 8) & 0xFF;
        int b = argb & 0xFF;
        if (a == 255) return String.format("#%02X%02X%02X", r, g, b);
        return String.format("rgba(%d,%d,%d,%.2f)", r, g, b, a / 255f);
    }

    private static String esc(String s) {
        if (s == null) return "";
        return s.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace("\"", "&quot;");
    }

    public boolean saveHtml(File f) {
        try {
            FileOutputStream out = new FileOutputStream(f);
            out.write(toHtml().getBytes("UTF-8"));
            out.flush();
            out.close();
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}

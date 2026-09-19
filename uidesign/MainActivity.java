package com.yuanbao.uidesign;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.Dialog;
import android.content.DialogInterface;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.os.Environment;
import android.text.InputType;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.util.ArrayList;

/**
 * 墨刀风格原型工具主界面。
 * 布局在 activity_main.xml；各面板（组件库/图层/属性/页面/文件）用 Dialog 动态构建。
 */
public class MainActivity extends Activity {

    private Project project;
    private int curPage = 0;
    private CanvasView canvas;
    private TextView tvTitle;
    private TextView tvStatus;

    /** 预设色板 */
    private static final int[] PALETTE = {
        0xFF2196F3, 0xFF1976D2, 0xFFF44336, 0xFFE53935,
        0xFF4CAF50, 0xFF388E3C, 0xFFFFC107, 0xFFFF9800,
        0xFF9C27B0, 0xFF673AB7, 0xFF00BCD4, 0xFF009688,
        0xFF212121, 0xFF757575, 0xFFBDBDBD, 0xFFFFFFFF,
        0x00000000
    };
    private static final String[] PALETTE_NAMES = {
        "蓝", "深蓝", "红", "深红", "绿", "深绿", "黄", "橙",
        "紫", "深紫", "青", "蓝绿", "黑", "灰", "浅灰", "白", "透明"
    };

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        setContentView(R.layout.activity_main);

        project = new Project();
        canvas = (CanvasView) findViewById(R.id.canvas_view);
        tvTitle = (TextView) findViewById(R.id.tv_title);
        tvStatus = (TextView) findViewById(R.id.tv_status);

        canvas.setPage(project.pages.get(curPage));
        canvas.setSelectionListener(new CanvasView.SelectionListener() {
            public void onSelected(Element e) {
                updateStatus();
            }
        });
        canvas.setNavigateListener(new CanvasView.NavigateListener() {
            public void onNavigate(int pageIndex) {
                if (pageIndex >= 0 && pageIndex < project.pages.size()) {
                    curPage = pageIndex;
                    canvas.setPage(project.pages.get(curPage));
                    updateStatus();
                    Toast.makeText(MainActivity.this,
                        "跳转 → " + project.pages.get(curPage).name,
                        Toast.LENGTH_SHORT).show();
                }
            }
        });

        bind(R.id.btn_add, new View.OnClickListener() {
            public void onClick(View v) { showComponentPanel(); }
        });
        bind(R.id.btn_layer, new View.OnClickListener() {
            public void onClick(View v) { showLayerPanel(); }
        });
        bind(R.id.btn_prop, new View.OnClickListener() {
            public void onClick(View v) { showPropPanel(); }
        });
        bind(R.id.btn_page, new View.OnClickListener() {
            public void onClick(View v) { showPagePanel(); }
        });
        bind(R.id.btn_preview, new View.OnClickListener() {
            public void onClick(View v) { togglePreview(); }
        });
        bind(R.id.btn_file, new View.OnClickListener() {
            public void onClick(View v) { showFilePanel(); }
        });
        bind(R.id.btn_export, new View.OnClickListener() {
            public void onClick(View v) { showExportPanel(); }
        });

        updateStatus();
    }

    private void bind(int id, View.OnClickListener l) {
        View v = findViewById(id);
        if (v != null) v.setOnClickListener(l);
    }

    private Page page() {
        return project.pages.get(curPage);
    }

    private int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density);
    }

    private void updateStatus() {
        Element sel = canvas.getSelected();
        String selName = sel != null ? sel.name : "无";
        tvTitle.setText(project.name);
        tvStatus.setText(page().name + " · " + page().elements.size()
            + " 元素 · 选中:" + selName
            + (canvas.isPreviewMode() ? " · 预览中" : ""));
    }

    private void togglePreview() {
        boolean p = !canvas.isPreviewMode();
        canvas.setPreviewMode(p);
        updateStatus();
        Toast.makeText(this, p ? "预览模式：点击热区跳转，返回键退出"
            : "编辑模式", Toast.LENGTH_SHORT).show();
    }

    @Override
    public void onBackPressed() {
        if (canvas.isPreviewMode()) {
            canvas.setPreviewMode(false);
            updateStatus();
            return;
        }
        super.onBackPressed();
    }

    // ============ 组件库面板 ============
    private void showComponentPanel() {
        Dialog d = new Dialog(this);
        d.setTitle("插入组件");
        ScrollView sv = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(12), dp(8), dp(12), dp(8));

        for (int i = 0; i < Element.TYPE_NAMES.length; i++) {
            final int t = i;
            Button b = new Button(this);
            b.setText(Element.TYPE_NAMES[i]);
            b.setLayoutParams(new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(44)));
            b.setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) {
                    insert(t);
                }
            });
            root.addView(b);
        }
        sv.addView(root);
        d.setContentView(sv);
        d.show();
    }

    private void insert(int type) {
        Element e = new Element(type);
        Page p = page();
        // 居中放置，带偏移避免完全重叠
        int n = p.elements.size();
        e.x = 40 + (n % 5) * 18;
        e.y = 60 + (n % 8) * 22;
        if (e.x + e.w > p.width) e.x = p.width - e.w - 10;
        if (e.y + e.h > p.height) e.y = p.height - e.h - 10;
        p.elements.add(e);
        canvas.setSelected(e);
        canvas.invalidate();
        updateStatus();
        Toast.makeText(this, "已插入 " + e.name, Toast.LENGTH_SHORT).show();
    }

    // ============ 图层面板 ============
    private void showLayerPanel() {
        final Dialog d = new Dialog(this);
        d.setTitle("图层（上层在前）");
        ScrollView sv = new ScrollView(this);
        final LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(12), dp(8), dp(12), dp(8));
        sv.addView(root);
        d.setContentView(sv);

        rebuildLayers(root, d);
        d.show();
    }

    private void rebuildLayers(final LinearLayout root, final Dialog d) {
        root.removeAllViews();
        final Page p = page();
        for (int i = p.elements.size() - 1; i >= 0; i--) {
            final int idx = i;
            final Element e = p.elements.get(i);

            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.VERTICAL);
            row.setPadding(0, dp(4), 0, dp(4));

            TextView name = new TextView(this);
            String flag = (e.visible ? "" : " [隐藏]") + (e.locked ? " [锁定]" : "");
            name.setText((i + 1) + ". " + e.name + flag);
            name.setTextSize(14);
            row.addView(name);

            HorizontalScrollView hs = new HorizontalScrollView(this);
            LinearLayout btns = new LinearLayout(this);
            btns.setOrientation(LinearLayout.HORIZONTAL);

            btns.addView(mini("选中", new View.OnClickListener() {
                public void onClick(View v) {
                    canvas.setSelected(e);
                    canvas.invalidate();
                    updateStatus();
                    d.dismiss();
                }
            }));
            btns.addView(mini("上移", new View.OnClickListener() {
                public void onClick(View v) {
                    if (idx < p.elements.size() - 1) {
                        p.elements.remove(idx);
                        p.elements.add(idx + 1, e);
                        rebuildLayers(root, d);
                        canvas.invalidate();
                    }
                }
            }));
            btns.addView(mini("下移", new View.OnClickListener() {
                public void onClick(View v) {
                    if (idx > 0) {
                        p.elements.remove(idx);
                        p.elements.add(idx - 1, e);
                        rebuildLayers(root, d);
                        canvas.invalidate();
                    }
                }
            }));
            btns.addView(mini("置顶", new View.OnClickListener() {
                public void onClick(View v) {
                    p.elements.remove(idx);
                    p.elements.add(e);
                    rebuildLayers(root, d);
                    canvas.invalidate();
                }
            }));
            btns.addView(mini("置底", new View.OnClickListener() {
                public void onClick(View v) {
                    p.elements.remove(idx);
                    p.elements.add(0, e);
                    rebuildLayers(root, d);
                    canvas.invalidate();
                }
            }));
            btns.addView(mini(e.visible ? "隐藏" : "显示", new View.OnClickListener() {
                public void onClick(View v) {
                    e.visible = !e.visible;
                    rebuildLayers(root, d);
                    canvas.invalidate();
                }
            }));
            btns.addView(mini(e.locked ? "解锁" : "锁定", new View.OnClickListener() {
                public void onClick(View v) {
                    e.locked = !e.locked;
                    rebuildLayers(root, d);
                }
            }));
            btns.addView(mini("改名", new View.OnClickListener() {
                public void onClick(View v) {
                    askText("重命名", e.name, new TextCallback() {
                        public void onResult(String s) {
                            e.name = s;
                            rebuildLayers(root, d);
                            updateStatus();
                        }
                    });
                }
            }));
            btns.addView(mini("复制", new View.OnClickListener() {
                public void onClick(View v) {
                    Element c = e.copy();
                    c.x += 16; c.y += 16;
                    p.elements.add(c);
                    rebuildLayers(root, d);
                    canvas.invalidate();
                    updateStatus();
                }
            }));
            btns.addView(mini("删除", new View.OnClickListener() {
                public void onClick(View v) {
                    p.elements.remove(idx);
                    if (canvas.getSelected() == e) canvas.setSelected(null);
                    rebuildLayers(root, d);
                    canvas.invalidate();
                    updateStatus();
                }
            }));

            hs.addView(btns);
            row.addView(hs);
            root.addView(row);
        }
    }

    private Button mini(String text, View.OnClickListener l) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextSize(11);
        b.setPadding(dp(8), dp(2), dp(8), dp(2));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.WRAP_CONTENT, dp(36));
        lp.setMargins(dp(2), 0, dp(2), 0);
        b.setLayoutParams(lp);
        b.setOnClickListener(l);
        return b;
    }

    // ============ 属性面板 ============
    private void showPropPanel() {
        final Element e = canvas.getSelected();
        if (e == null) {
            Toast.makeText(this, "请先选中一个元素", Toast.LENGTH_SHORT).show();
            return;
        }
        final Dialog d = new Dialog(this);
        d.setTitle("属性：" + e.name);
        ScrollView sv = new ScrollView(this);
        final LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(12), dp(8), dp(12), dp(12));
        sv.addView(root);
        d.setContentView(sv);

        // 位置尺寸
        root.addView(section("位置与尺寸"));
        LinearLayout r1 = row4(
            numBtn("X", (int) e.x, new NumCallback() {
                public void onResult(int v) { e.x = v; refresh(); }
            }),
            numBtn("Y", (int) e.y, new NumCallback() {
                public void onResult(int v) { e.y = v; refresh(); }
            }),
            numBtn("宽", (int) e.w, new NumCallback() {
                public void onResult(int v) { e.w = v; refresh(); }
            }),
            numBtn("高", (int) e.h, new NumCallback() {
                public void onResult(int v) { e.h = v; refresh(); }
            }));
        root.addView(r1);

        LinearLayout r2 = row4(
            numBtn("圆角", (int) e.radius, new NumCallback() {
                public void onResult(int v) { e.radius = v; refresh(); }
            }),
            numBtn("旋转", (int) e.rotation, new NumCallback() {
                public void onResult(int v) { e.rotation = v; refresh(); }
            }),
            numBtn("透明", e.alpha, new NumCallback() {
                public void onResult(int v) { e.alpha = Math.max(0, Math.min(255, v)); refresh(); }
            }),
            numBtn("描边宽", (int) e.strokeWidth, new NumCallback() {
                public void onResult(int v) { e.strokeWidth = v; refresh(); }
            }));
        root.addView(r2);

        // 填充色
        root.addView(section("填充色"));
        root.addView(paletteRow(new ColorCallback() {
            public void onColor(int c) { e.fill = c; refresh(); }
        }));
        // 描边色
        root.addView(section("描边色"));
        root.addView(paletteRow(new ColorCallback() {
            public void onColor(int c) { e.stroke = c; refresh(); }
        }));

        // 文本（若支持）
        if (e.hasText()) {
            root.addView(section("文本"));
            Button tb = new Button(this);
            tb.setText("内容：" + e.text);
            tb.setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) {
                    askText("文本内容", e.text, new TextCallback() {
                        public void onResult(String s) { e.text = s; refresh(); d.dismiss(); }
                    });
                }
            });
            root.addView(tb);

            LinearLayout r3 = row4(
                numBtn("字号", (int) e.textSize, new NumCallback() {
                    public void onResult(int v) { e.textSize = v; refresh(); }
                }),
                alignBtn(e, d),
                dummyBtn(),
                dummyBtn());
            root.addView(r3);

            root.addView(section("文字颜色"));
            root.addView(paletteRow(new ColorCallback() {
                public void onColor(int c) { e.textColor = c; refresh(); }
            }));
        }

        // 交互
        root.addView(section("交互（点击跳转）"));
        root.addView(linkRow(e, d));

        // 显示/锁定
        LinearLayout r4 = new LinearLayout(this);
        r4.setOrientation(LinearLayout.HORIZONTAL);
        Button vb = mini(e.visible ? "可见 ✓" : "隐藏", new View.OnClickListener() {
            public void onClick(View v) { e.visible = !e.visible; refresh(); d.dismiss(); }
        });
        Button lb = mini(e.locked ? "锁定 ✓" : "未锁定", new View.OnClickListener() {
            public void onClick(View v) { e.locked = !e.locked; refresh(); d.dismiss(); }
        });
        r4.addView(vb);
        r4.addView(lb);
        root.addView(r4);

        d.show();
    }

    private void refresh() {
        canvas.invalidate();
        updateStatus();
    }

    private TextView section(String t) {
        TextView tv = new TextView(this);
        tv.setText(t);
        tv.setTextSize(13);
        tv.setPadding(0, dp(10), 0, dp(4));
        return tv;
    }

    private LinearLayout row4(View a, View b, View c, View dd) {
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.HORIZONTAL);
        l.addView(a); l.addView(b); l.addView(c); l.addView(dd);
        return l;
    }

    private Button dummyBtn() {
        Button b = new Button(this);
        b.setVisibility(View.INVISIBLE);
        b.setLayoutParams(new LinearLayout.LayoutParams(0, dp(40), 1f));
        return b;
    }

    private Button numBtn(final String label, final int cur, final NumCallback cb) {
        Button b = new Button(this);
        b.setText(label + ":" + cur);
        b.setTextSize(11);
        b.setLayoutParams(new LinearLayout.LayoutParams(0, dp(40), 1f));
        b.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                askNum(label, cur, cb);
            }
        });
        return b;
    }

    private Button alignBtn(final Element e, final Dialog d) {
        Button b = new Button(this);
        String[] names = {"左", "居中", "右"};
        b.setText("对齐:" + names[e.textAlign]);
        b.setTextSize(11);
        b.setLayoutParams(new LinearLayout.LayoutParams(0, dp(40), 1f));
        b.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                final String[] names = {"左对齐", "居中", "右对齐"};
                new AlertDialog.Builder(MainActivity.this)
                    .setTitle("文本对齐")
                    .setItems(names, new DialogInterface.OnClickListener() {
                        public void onClick(DialogInterface dg, int w) {
                            e.textAlign = w;
                            refresh();
                            d.dismiss();
                        }
                    }).show();
            }
        });
        return b;
    }

    private HorizontalScrollView paletteRow(final ColorCallback cb) {
        HorizontalScrollView hs = new HorizontalScrollView(this);
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.HORIZONTAL);
        for (int i = 0; i < PALETTE.length; i++) {
            final int c = PALETTE[i];
            Button b = new Button(this);
            b.setText(PALETTE_NAMES[i]);
            b.setTextSize(9);
            b.setBackgroundColor(c);
            if ((c & 0xFFFFFF) == 0xFFFFFF || c == 0) {
                b.setTextColor(0xFF333333);
            } else {
                b.setTextColor(0xFFFFFFFF);
            }
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dp(46), dp(38));
            lp.setMargins(dp(2), 0, dp(2), 0);
            b.setLayoutParams(lp);
            b.setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) {
                    cb.onColor(c);
                }
            });
            l.addView(b);
        }
        hs.addView(l);
        return hs;
    }

    private View linkRow(final Element e, final Dialog d) {
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.HORIZONTAL);
        Button b = new Button(this);
        String target = (e.linkTo >= 0 && e.linkTo < project.pages.size())
            ? project.pages.get(e.linkTo).name : "无";
        b.setText("跳转 → " + target);
        b.setTextSize(11);
        b.setLayoutParams(new LinearLayout.LayoutParams(0, dp(40), 1f));
        b.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                ArrayList<String> names = new ArrayList<String>();
                names.add("（无）");
                for (int i = 0; i < project.pages.size(); i++) {
                    names.add(project.pages.get(i).name);
                }
                final String[] arr = names.toArray(new String[0]);
                new AlertDialog.Builder(MainActivity.this)
                    .setTitle("点击跳转到")
                    .setItems(arr, new DialogInterface.OnClickListener() {
                        public void onClick(DialogInterface dg, int w) {
                            e.linkTo = w - 1;
                            refresh();
                            d.dismiss();
                        }
                    }).show();
            }
        });
        l.addView(b);

        Button hs = new Button(this);
        hs.setText("加热区");
        hs.setTextSize(11);
        hs.setLayoutParams(new LinearLayout.LayoutParams(0, dp(40), 1f));
        hs.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                Element hot = new Element(Element.HOTSPOT);
                hot.x = e.x; hot.y = e.y; hot.w = e.w; hot.h = e.h;
                hot.linkTo = e.linkTo;
                hot.name = e.name + " 热区";
                page().elements.add(hot);
                refresh();
                d.dismiss();
                Toast.makeText(MainActivity.this, "已添加热区", Toast.LENGTH_SHORT).show();
            }
        });
        l.addView(hs);
        return l;
    }

    // ============ 页面面板 ============
    private void showPagePanel() {
        final Dialog d = new Dialog(this);
        d.setTitle("页面管理");
        ScrollView sv = new ScrollView(this);
        final LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(12), dp(8), dp(12), dp(8));
        sv.addView(root);
        d.setContentView(sv);
        rebuildPages(root, d);
        d.show();
    }

    private void rebuildPages(final LinearLayout root, final Dialog d) {
        root.removeAllViews();
        for (int i = 0; i < project.pages.size(); i++) {
            final int idx = i;
            final Page p = project.pages.get(i);
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);

            TextView tv = new TextView(this);
            tv.setText((i == curPage ? "▶ " : "") + p.name
                + " (" + p.elements.size() + ")");
            tv.setTextSize(14);
            tv.setLayoutParams(new LinearLayout.LayoutParams(0, dp(40), 1f));
            row.addView(tv);

            row.addView(mini("切换", new View.OnClickListener() {
                public void onClick(View v) {
                    curPage = idx;
                    canvas.setPage(project.pages.get(curPage));
                    updateStatus();
                    d.dismiss();
                }
            }));
            row.addView(mini("改名", new View.OnClickListener() {
                public void onClick(View v) {
                    askText("页面名", p.name, new TextCallback() {
                        public void onResult(String s) {
                            p.name = s;
                            rebuildPages(root, d);
                            updateStatus();
                        }
                    });
                }
            }));
            row.addView(mini("复制", new View.OnClickListener() {
                public void onClick(View v) {
                    Page np = Page.fromJson(p.toJson());
                    np.name = p.name + " 副本";
                    project.pages.add(np);
                    rebuildPages(root, d);
                }
            }));
            row.addView(mini("删除", new View.OnClickListener() {
                public void onClick(View v) {
                    if (project.pages.size() <= 1) {
                        Toast.makeText(MainActivity.this, "至少保留一页", Toast.LENGTH_SHORT).show();
                        return;
                    }
                    project.pages.remove(idx);
                    if (curPage >= project.pages.size()) curPage = project.pages.size() - 1;
                    canvas.setPage(project.pages.get(curPage));
                    rebuildPages(root, d);
                    updateStatus();
                }
            }));
            root.addView(row);
        }

        Button add = new Button(this);
        add.setText("＋ 新建页面");
        add.setLayoutParams(new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, dp(44)));
        add.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                project.pages.add(new Page("页面 " + (project.pages.size() + 1)));
                rebuildPages(root, d);
            }
        });
        root.addView(add);

        Button size = new Button(this);
        size.setText("画布尺寸 " + page().width + "×" + page().height
            + "（点击切换常用尺寸）");
        size.setTextSize(11);
        size.setLayoutParams(new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, dp(44)));
        size.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                final String[] opts = {"375×667 iPhone", "360×640 Android",
                    "414×896 iPhone XR", "768×1024 iPad", "1920×1080 PC"};
                final int[][] sizes = {{375, 667}, {360, 640},
                    {414, 896}, {768, 1024}, {1920, 1080}};
                new AlertDialog.Builder(MainActivity.this)
                    .setTitle("画布尺寸")
                    .setItems(opts, new DialogInterface.OnClickListener() {
                        public void onClick(DialogInterface dg, int w) {
                            page().width = sizes[w][0];
                            page().height = sizes[w][1];
                            canvas.invalidate();
                            d.dismiss();
                        }
                    }).show();
            }
        });
        root.addView(size);

        Button bg = new Button(this);
        bg.setText("页面背景色");
        bg.setLayoutParams(new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, dp(44)));
        bg.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                Dialog cd = new Dialog(MainActivity.this);
                cd.setTitle("背景色");
                HorizontalScrollView hs = paletteRow(new ColorCallback() {
                    public void onColor(int c) {
                        page().bgColor = c;
                        canvas.invalidate();
                    }
                });
                cd.setContentView(hs);
                cd.show();
            }
        });
        root.addView(bg);
    }

    // ============ 文件面板（保存/打开） ============
    private void showFilePanel() {
        final String[] opts = {"保存项目", "打开项目", "重命名项目", "新建项目"};
        new AlertDialog.Builder(this)
            .setTitle("文件")
            .setItems(opts, new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface dg, int w) {
                    if (w == 0) saveProject();
                    else if (w == 1) openProject();
                    else if (w == 2) {
                        askText("项目名", project.name, new TextCallback() {
                            public void onResult(String s) {
                                project.name = s;
                                updateStatus();
                            }
                        });
                    } else {
                        project = new Project();
                        curPage = 0;
                        canvas.setPage(project.pages.get(0));
                        updateStatus();
                        Toast.makeText(MainActivity.this, "已新建", Toast.LENGTH_SHORT).show();
                    }
                }
            }).show();
    }

    private File projDir() {
        File d = getExternalFilesDir("projects");
        if (d != null && !d.exists()) d.mkdirs();
        if (d == null) d = getFilesDir();
        return d;
    }

    private void saveProject() {
        try {
            File f = new File(projDir(), safe(project.name) + ".json");
            FileOutputStream out = new FileOutputStream(f);
            out.write(project.toJson().toString(2).getBytes("UTF-8"));
            out.flush();
            out.close();
            Toast.makeText(this, "已保存：" + f.getAbsolutePath(), Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            Toast.makeText(this, "保存失败：" + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private static String safe(String s) {
        if (s == null || s.length() == 0) return "project";
        return s.replaceAll("[\\\\/:*?\"<>|]", "_");
    }

    private void openProject() {
        File dir = projDir();
        File[] fs = dir.listFiles();
        final ArrayList<File> list = new ArrayList<File>();
        if (fs != null) {
            for (int i = 0; i < fs.length; i++) {
                if (fs[i].getName().endsWith(".json")) list.add(fs[i]);
            }
        }
        if (list.size() == 0) {
            Toast.makeText(this, "暂无存档", Toast.LENGTH_SHORT).show();
            return;
        }
        String[] names = new String[list.size()];
        for (int i = 0; i < list.size(); i++) names[i] = list.get(i).getName();
        new AlertDialog.Builder(this)
            .setTitle("打开项目")
            .setItems(names, new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface dg, int w) {
                    try {
                        byte[] b = readAll(list.get(w));
                        org.json.JSONObject o = new org.json.JSONObject(new String(b, "UTF-8"));
                        project = Project.fromJson(o);
                        curPage = 0;
                        canvas.setPage(project.pages.get(0));
                        updateStatus();
                        Toast.makeText(MainActivity.this, "已打开：" + project.name,
                            Toast.LENGTH_SHORT).show();
                    } catch (Exception e) {
                        Toast.makeText(MainActivity.this, "读取失败：" + e.getMessage(),
                            Toast.LENGTH_LONG).show();
                    }
                }
            }).show();
    }

    private static byte[] readAll(File f) throws Exception {
        java.io.FileInputStream in = new java.io.FileInputStream(f);
        java.io.ByteArrayOutputStream bo = new java.io.ByteArrayOutputStream();
        byte[] buf = new byte[8192];
        int n;
        while ((n = in.read(buf)) > 0) bo.write(buf, 0, n);
        in.close();
        return bo.toByteArray();
    }

    // ============ 导出 ============
    private void showExportPanel() {
        final String[] opts = {"导出当前页 PNG", "导出全部页 PNG", "导出 HTML 离线包", "导出项目 JSON"};
        new AlertDialog.Builder(this)
            .setTitle("导出")
            .setItems(opts, new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface dg, int w) {
                    File dir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
                    if (dir != null && !dir.exists()) dir.mkdirs();
                    if (w == 0 || w == 1) {
                        int cnt = 0;
                        for (int i = 0; i < project.pages.size(); i++) {
                            if (w == 0 && i != curPage) continue;
                            canvas.setPage(project.pages.get(i));
                            Bitmap bmp = canvas.exportBitmap();
                            if (bmp != null) {
                                File f = new File(dir, safe(project.name) + "_"
                                    + project.pages.get(i).name + ".png");
                                try {
                                    FileOutputStream o = new FileOutputStream(f);
                                    bmp.compress(Bitmap.CompressFormat.PNG, 100, o);
                                    o.flush(); o.close();
                                    cnt++;
                                } catch (Exception e) {
                                }
                            }
                        }
                        canvas.setPage(project.pages.get(curPage));
                        Toast.makeText(MainActivity.this, "已导出 " + cnt + " 张 PNG",
                            Toast.LENGTH_LONG).show();
                    } else if (w == 2) {
                        File f = new File(dir, safe(project.name) + ".html");
                        boolean ok = project.saveHtml(f);
                        Toast.makeText(MainActivity.this,
                            ok ? "HTML 已导出：" + f.getAbsolutePath() : "导出失败",
                            Toast.LENGTH_LONG).show();
                    } else {
                        File f = new File(dir, safe(project.name) + ".json");
                        try {
                            FileOutputStream o = new FileOutputStream(f);
                            o.write(project.toJson().toString(2).getBytes("UTF-8"));
                            o.flush(); o.close();
                            Toast.makeText(MainActivity.this, "JSON 已导出：" + f.getAbsolutePath(),
                                Toast.LENGTH_LONG).show();
                        } catch (Exception e) {
                            Toast.makeText(MainActivity.this, "失败：" + e.getMessage(),
                                Toast.LENGTH_LONG).show();
                        }
                    }
                }
            }).show();
    }

    // ============ 输入辅助 ============
    private void askText(String title, String def, final TextCallback cb) {
        final EditText et = new EditText(this);
        et.setInputType(InputType.TYPE_CLASS_TEXT);
        et.setText(def == null ? "" : def);
        new AlertDialog.Builder(this)
            .setTitle(title)
            .setView(et)
            .setPositiveButton("确定", new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface d, int w) {
                    cb.onResult(et.getText().toString());
                }
            })
            .setNegativeButton("取消", null)
            .show();
    }

    private void askNum(String title, int def, final NumCallback cb) {
        final EditText et = new EditText(this);
        et.setInputType(InputType.TYPE_CLASS_NUMBER
            | InputType.TYPE_NUMBER_FLAG_SIGNED);
        et.setText(String.valueOf(def));
        new AlertDialog.Builder(this)
            .setTitle(title)
            .setView(et)
            .setPositiveButton("确定", new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface d, int w) {
                    try {
                        cb.onResult(Integer.parseInt(et.getText().toString()));
                    } catch (Exception e) {
                    }
                }
            })
            .setNegativeButton("取消", null)
            .show();
    }

    public interface TextCallback {
        void onResult(String s);
    }

    public interface NumCallback {
        void onResult(int v);
    }

    public interface ColorCallback {
        void onColor(int c);
    }
}

package com.yuanbao.uidesign;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.os.Environment;
import android.text.InputType;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;

/**
 * UI设计器主界面。
 * 布局完全由 res/layout/activity_main.xml 定义，本类只负责绑定控件与业务逻辑。
 */
public class MainActivity extends Activity implements View.OnClickListener {

    /** 工具按钮 id 与 CanvasView 工具常量的对应关系 */
    private static final int[] TOOL_BTN_IDS = {
        R.id.btn_tool_path,
        R.id.btn_tool_rect,
        R.id.btn_tool_oval,
        R.id.btn_tool_line,
        R.id.btn_tool_text,
        R.id.btn_tool_erase
    };
    private static final int[] TOOL_NAME_IDS = {
        R.string.tool_path,
        R.string.tool_rect,
        R.string.tool_oval,
        R.string.tool_line,
        R.string.tool_text,
        R.string.tool_erase
    };

    /** 色块按钮 id 与颜色的对应关系 */
    private static final int[] SWATCH_IDS = {
        R.id.sw_blue, R.id.sw_red, R.id.sw_green, R.id.sw_amber,
        R.id.sw_purple, R.id.sw_black, R.id.sw_white, R.id.sw_grey
    };
    private static final int[] SWATCH_COLORS = {
        R.color.swatch_blue, R.color.swatch_red, R.color.swatch_green, R.color.swatch_amber,
        R.color.swatch_purple, R.color.swatch_black, R.color.swatch_white, R.color.swatch_grey
    };

    private CanvasView canvas;
    private TextView tvStatus;
    private Button[] toolBtns;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        canvas = (CanvasView) findViewById(R.id.canvas_view);
        tvStatus = (TextView) findViewById(R.id.tv_status);

        bindToolButtons();
        bindSwatches();
        bindWidthButtons();
        bindActionButtons();

        canvas.setTextPointListener(new CanvasView.TextPointListener() {
            public void onTextPoint(float x, float y) {
                showTextDialog(x, y);
            }
        });

        updateStatus();
    }

    private void bindToolButtons() {
        toolBtns = new Button[TOOL_BTN_IDS.length];
        for (int i = 0; i < TOOL_BTN_IDS.length; i++) {
            toolBtns[i] = (Button) findViewById(TOOL_BTN_IDS[i]);
            final int idx = i;
            toolBtns[i].setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) {
                    canvas.setTool(idx);
                    refreshToolSelection();
                    updateStatus();
                }
            });
        }
        refreshToolSelection();
    }

    /** 用 selected 状态驱动 selector，符合标准做法 */
    private void refreshToolSelection() {
        int cur = canvas.getTool();
        for (int i = 0; i < toolBtns.length; i++) {
            toolBtns[i].setSelected(i == cur);
        }
    }

    private void bindSwatches() {
        for (int i = 0; i < SWATCH_IDS.length; i++) {
            final int colorRes = SWATCH_COLORS[i];
            View v = findViewById(SWATCH_IDS[i]);
            v.setOnClickListener(new View.OnClickListener() {
                public void onClick(View view) {
                    canvas.setColor(getResources().getColor(colorRes));
                    updateStatus();
                }
            });
        }
    }

    private void bindWidthButtons() {
        bindOne(R.id.btn_w_thin, new View.OnClickListener() {
            public void onClick(View v) { canvas.setStrokeWidth(3f); updateStatus(); }
        });
        bindOne(R.id.btn_w_mid, new View.OnClickListener() {
            public void onClick(View v) { canvas.setStrokeWidth(6f); updateStatus(); }
        });
        bindOne(R.id.btn_w_bold, new View.OnClickListener() {
            public void onClick(View v) { canvas.setStrokeWidth(12f); updateStatus(); }
        });
    }

    private void bindActionButtons() {
        bindOne(R.id.btn_undo, new View.OnClickListener() {
            public void onClick(View v) { canvas.undo(); updateStatus(); }
        });
        bindOne(R.id.btn_grid, new View.OnClickListener() {
            public void onClick(View v) {
                canvas.setGrid(!canvas.getGrid());
                Toast.makeText(MainActivity.this,
                    canvas.getGrid() ? R.string.grid_on : R.string.grid_off,
                    Toast.LENGTH_SHORT).show();
            }
        });
        bindOne(R.id.btn_clear, new View.OnClickListener() {
            public void onClick(View v) { canvas.clear(); updateStatus(); }
        });
        bindOne(R.id.btn_export, new View.OnClickListener() {
            public void onClick(View v) { exportPng(); }
        });
    }

    private void bindOne(int id, View.OnClickListener l) {
        View v = findViewById(id);
        if (v != null) v.setOnClickListener(l);
    }

    private void showTextDialog(final float x, final float y) {
        final EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_TEXT);
        input.setHint(R.string.dialog_text_hint);
        new AlertDialog.Builder(this)
            .setTitle(R.string.dialog_text_title)
            .setView(input)
            .setPositiveButton(R.string.dialog_ok, new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface d, int w) {
                    String s = input.getText().toString();
                    if (s.length() > 0) {
                        canvas.addText(s, x, y);
                        updateStatus();
                    }
                }
            })
            .setNegativeButton(R.string.dialog_cancel, null)
            .show();
    }

    private void exportPng() {
        if (canvas.getShapeCount() == 0) {
            Toast.makeText(this, R.string.toast_nothing, Toast.LENGTH_SHORT).show();
            return;
        }
        try {
            Bitmap bmp = canvas.exportBitmap();
            File dir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
            if (dir != null && !dir.exists()) {
                dir.mkdirs();
            }
            File f = new File(dir, "ui_design_" + System.currentTimeMillis() + ".png");
            FileOutputStream out = new FileOutputStream(f);
            bmp.compress(Bitmap.CompressFormat.PNG, 100, out);
            out.flush();
            out.close();
            Toast.makeText(this,
                getString(R.string.toast_saved, f.getAbsolutePath()),
                Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            Toast.makeText(this,
                getString(R.string.toast_save_failed, e.getMessage()),
                Toast.LENGTH_LONG).show();
        }
    }

    private void updateStatus() {
        int toolIdx = canvas.getTool();
        String toolName = toolIdx >= 0 && toolIdx < TOOL_NAME_IDS.length
            ? getString(TOOL_NAME_IDS[toolIdx]) : "";
        tvStatus.setText(getString(R.string.status_fmt,
            canvas.getShapeCount(), (int) canvas.getStrokeWidth(), toolName));
    }

    /** 本类自身也实现 OnClickListener，统一入口（当前未直接绑定） */
    public void onClick(View v) {
        // 各按钮已分别绑定，此处保留统一接口
    }
}

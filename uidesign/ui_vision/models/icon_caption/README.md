# icon_caption 部署说明（OmniParser 图标语义理解）

## 状态：已跑通 ✅

纯 CPU、无 torch、无 GPU。2026-09-26 实测。

## 文件位置

```
/data/user_persistent_data/uiparse/icon_caption/
  vision_encoder.onnx        365,965,528 B
  embed_tokens.onnx          157,560,107 B
  encoder_model.onnx         173,409,090 B
  decoder_model_merged.onnx  388,046,167 B
  ic_run.py                  单图推理
  ui_understand.py           完整闭环（icon_detect + caption）
```

## 用法

```bash
# 单图描述
python3 ic_run.py <图片> "What does the image describe?" 24

# UI 闭环：检出元素 + 逐个语义描述 + dp 换算
python3 ui_understand.py <UI截图> [像素密度]
```

## 实测结果

Blueprint 渲染的 Welcome Back 登录页（390×780，3x 密度）：

```
#  尺寸(dp)   位置        conf  描述
0  89x13     @(19,109)  0.82  Email
1  90x12     @(19,125)  0.82  Password
2  90x12     @(19,144)  0.71  Lognit
3  93x80     @(17,  2)  0.15  a blank space for text or image.
```

总耗时 15.2s（含模型加载 10s，之后每个元素约 1~2s）。

## 对比：Florence-2 base（未微调）在 UI 上的表现

| 实际元素 | base 输出 |
|---|---|
| 微信 Logo | green leaves（绿叶） |
| 眼睛图标 | a wiper blade in a circle（雨刷器） |
| 时间 9:41 | written in a foreign language |

**icon_caption 是微调版，能给出正确 UI 语义（Email / Password / Log in）。**
两者是不同模型，不要混用。

## 四个必须知道的坑

### 1. pre 与 dec 必须复用同一个 Session
`decoder_model_merged.onnx` 一个文件承担 prefill 和 decode。
若建两个 Session 会双双驻留内存（1.4GB），超出可用内存触发 swap 抖动，
表现为"卡住无任何输出"。修复：`_S["pre"] = _S["dec"]`。

### 2. merged 模型 prefill 也要传 past_key_values（零初始化）
即使 `use_cache_branch=False`。形状：
- `.decoder.key/value` → `(1, 12, 0, 64)`
- `.encoder.key/value` → `(1, 12, enc_len, 64)`

12 heads，head_dim 64，6 层。

### 3. 没有 encoder_attention_mask 输入
该模型只有 3 个非 KV 输入：
`encoder_hidden_states` / `inputs_embeds` / `use_cache_branch`。
传 `encoder_attention_mask` 会报 Invalid input name。

### 4. prompt 必须用展开文本，不能用 "<CAPTION>" 字面量
tokenizer 未把 `<CAPTION>` 注册为特殊 token，会被 BPE 切碎导致输出垃圾（实测输出 "TION"）。
正确写法：`"What does the image describe?"`。

## 其他依赖

- tokenizer 复用 Florence-2-base：`/data/user_persistent_data/vlm_florence/processor/tokenizer.json`
- tokenizers 库在 `/data/user_persistent_data/toklibs`（需 sys.path.insert）
- icon_detect：`/data/user_persistent_data/uiparse/icon_detect.onnx`
- 复制大文件前先 `ulimit -f unlimited`，否则超过 200MB 报 File size limit exceeded

## 已知不足

- 短文本近似：实测 "Log in" 输出为 "Lognit"（置信度 0.71 的元素）
- 模型加载 10s，不适合高频调用；建议常驻进程批量处理

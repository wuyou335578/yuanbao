#!/usr/bin/env python3
"""OmniParser icon_caption (Florence-2 微调) ONNX 推理 — 纯 CPU，无 torch

用法:
  python3 ic_run.py <图片> ["<CAPTION>"] [max_new]
"""
import sys, os, time
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = "/data/user_persistent_data/vlm_florence/processor"
sys.path.insert(0, "/data/user_persistent_data/toklibs")

import onnxruntime as ort
from tokenizers import Tokenizer

_so = ort.SessionOptions()
_so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
_so.log_severity_level = 3
_CPU = ["CPUExecutionProvider"]

_S = {}
_TOK = None


def _load():
    global _TOK
    if _S:
        return
    # 关键: dec 与 pre 复用同一个 Session(仅一个 merged 文件),
    # 若重复加载会双双驻留内存 -> 1.4GB 超出可用内存触发 swap 抖动
    for k, f in [("vision", "vision_encoder.onnx"), ("embed", "embed_tokens.onnx"),
                 ("enc", "encoder_model.onnx"), ("dec", "decoder_model_merged.onnx")]:
        _S[k] = ort.InferenceSession(os.path.join(HERE, f), _so, providers=_CPU)
    _S["pre"] = _S["dec"]
    _TOK = Tokenizer.from_file(os.path.join(PROC, "tokenizer.json"))
    extra = ['<od>', '</od>', '<ocr>', '</ocr>'] + [f'<loc_{x}>' for x in range(1000)] + [
        '<cap>', '</cap>', '<ncap>', '</ncap>', '<dcap>', '</dcap>', '<grounding>', '</grounding>',
        '<seg>', '</seg>', '<sep>', '<region_cap>', '</region_cap>', '<region_to_desciption>',
        '</region_to_desciption>', '<proposal>', '</proposal>', '<poly>', '</poly>', '<and>']
    _TOK.add_special_tokens(extra)


def preprocess(img_path, size=384):
    im = Image.open(img_path).convert("RGB").resize((size, size), Image.BICUBIC)
    a = np.asarray(im, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    a = (a - mean) / std
    return np.transpose(a, (2, 0, 1))[None].astype(np.float32)


def infer(img_path, prompt="<CAPTION>", max_new=64):
    _load()
    ids = _TOK.encode(prompt).ids
    input_ids = np.array([ids], dtype=np.int64)
    pv = preprocess(img_path)

    img_feat = _S["vision"].run(None, {"pixel_values": pv})[0]
    txt_emb = _S["embed"].run(None, {"input_ids": input_ids})[0]
    enc_emb = np.concatenate([img_feat, txt_emb], axis=1).astype(np.float32)
    attn = np.ones((1, enc_emb.shape[1]), dtype=np.int64)
    enc_out = _S["enc"].run(None, {"inputs_embeds": enc_emb, "attention_mask": attn})[0]

    d = _S["dec"]
    pre = _S["pre"]
    names = [i.name for i in d.get_inputs() if i.name.startswith("past_key_values")]
    pre_in = [i.name for i in pre.get_inputs()]
    feed = {"inputs_embeds": enc_emb[:, -1:],
            "encoder_hidden_states": enc_out}
    if "use_cache_branch" in pre_in:
        feed["use_cache_branch"] = np.array([False], dtype=np.bool_)
    # merged 模型即使 prefill 也要求传 past_key_values(零初始化):
    # decoder 侧长度 0, encoder 侧长度 = encoder 输出长度
    enc_len = enc_out.shape[1]
    for n in names:
        if ".decoder." in n:
            feed[n] = np.zeros((1, 12, 0, 64), dtype=np.float32)
        else:
            feed[n] = np.zeros((1, 12, enc_len, 64), dtype=np.float32)
    outs = pre.run(None, feed)
    enc_kv = outs[1:]

    toks = []
    last_dkv = None
    for _ in range(max_new):
        nt = int(np.argmax(outs[0][:, -1, :], axis=-1)[0])
        toks.append(nt)
        if nt == 2:
            break
        ne = _S["embed"].run(None, {"input_ids": np.array([[nt]], dtype=np.int64)})[0]
        feed = {"inputs_embeds": ne, "encoder_hidden_states": enc_out}
        if "use_cache_branch" in [i.name for i in d.get_inputs()]:
            feed["use_cache_branch"] = np.array([True], dtype=np.bool_)
        dkv = None if len(toks) == 1 else last_dkv
        for i, n in enumerate(names):
            if n.endswith(".encoder.key") or n.endswith(".encoder.value"):
                feed[n] = enc_kv[i]
            else:
                feed[n] = (enc_kv[i] if dkv is None else last_dkv[i])
        outs = d.run(None, feed)
        last_dkv = outs[1:]
    return _TOK.decode(toks, skip_special_tokens=True).strip()


if __name__ == "__main__":
    img = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "<CAPTION>"
    max_new = int(sys.argv[3]) if len(sys.argv) > 3 else 64
    t0 = time.time()
    print(f"输入 {img} ({Image.open(img).size})  prompt={prompt!r}", flush=True)
    print("输出:", infer(img, prompt, max_new), flush=True)
    print(f"[用时 {time.time()-t0:.1f}s]", flush=True)

#!/bin/bash
# icon_caption 权重的分片 / 合并脚本
# 目标仓库路径: wuyou335578/yuanbao -> uidesign/ui_vision/models/icon_caption/
#
# 用法:
#   bash icon_caption_split.sh split <源目录> <输出目录> [每片MB]
#   bash icon_caption_split.sh merge <分片目录> <输出文件>

set -u
MODE="${1:-}"
SRC="${2:-}"
DST="${3:-}"
SIZE_MB="${4:-95}"

FILES="vision_encoder.onnx embed_tokens.onnx encoder_model.onnx decoder_model_merged.onnx"

do_split() {
    local src="$1" dst="$2" mb="$3"
    mkdir -p "$dst"
    for f in $FILES; do
        if [ ! -f "$src/$f" ]; then
            echo "跳过(不存在): $f"
            continue
        fi
        echo "切片: $f"
        split -b "${mb}m" -d -a 2 "$src/$f" "$dst/$f.part"
    done
    echo ""
    echo "产出分片清单:"
    ls -la "$dst" | awk '{printf "  %-45s %.1f MB\n", $9, $5/1048576}' | grep part
}

do_merge() {
    local dir="$1" out="$2"
    for f in $FILES; do
        local parts=$(ls "$dir/$f.part"* 2>/dev/null | sort)
        if [ -z "$parts" ]; then
            echo "无分片: $f"
            continue
        fi
        echo "合并: $f"
        cat $parts > "$out/$f"
        echo "  -> $(stat -c%s "$out/$f") bytes"
    done
}

case "$MODE" in
    split)
        [ -z "$SRC" ] && SRC="/data/user_persistent_data/uiparse/icon_caption"
        [ -z "$DST" ] && DST="/data/workspace/icon_caption_parts"
        do_split "$SRC" "$DST" "$SIZE_MB"
        ;;
    merge)
        [ -z "$DST" ] && DST="/data/user_persistent_data/uiparse/icon_caption"
        do_merge "$SRC" "$DST"
        ;;
    *)
        echo "用法:"
        echo "  bash $0 split <源目录> <输出目录> [每片MB]"
        echo "  bash $0 merge <分片目录> <输出目录>"
        exit 1
        ;;
esac

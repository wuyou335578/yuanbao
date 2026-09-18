#!/bin/bash
# 垂直扩容：把 cgroup CPU 配额提到与可见核心数一致
# 背景：沙盒默认 cpu.cfs_quota_us=200000（=2核），低于实际可见核心数
# 用法: bash boost_cpu.sh
QF=/sys/fs/cgroup/cpu/cpu.cfs_quota_us
[ -f "$QF" ] || { echo "找不到 cgroup cpu 配额文件"; exit 1; }

N=$(nproc)
WANT=$((N * 100000))
OLD=$(cat $QF)

echo "可见核心数: $N"
echo "当前配额:   $OLD (= $(awk "BEGIN{printf \"%.1f\", $OLD/100000}") 核)"
echo "$WANT" > "$QF" 2>/dev/null || { echo "❌ 写入失败（只读）"; exit 1; }

NEW=$(cat $QF)
echo "新配额:     $NEW (= $(awk "BEGIN{printf \"%.1f\", $NEW/100000}") 核)"

if [ "$NEW" = "$WANT" ]; then
  echo "✅ 已提升到 ${N} 核配额"
else
  echo "⚠️ 写入未生效"
fi

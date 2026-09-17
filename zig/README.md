# zig/ —— Zig 0.16.0 完整版（分卷存放）

> 这目录是 **5 个分卷**，不是 5 个独立文件。必须按序合并。

## 这是什么

**Zig 0.16.0 完整版**，含 libc / libcxx / libcxxabi / libunwind / std，
**能编译 C 和 C++**（普通残缺版只能编 Zig 和简单 C）。

| 项 | 值 |
|---|---|
| 合并后文件 | `zig完整版.zip` |
| 大小 | **105.45 MB** |
| **合并后 md5** | `bf0ce2bce4e543e02c7833792bb8f17f` |
| 解压后 | `zig`（164.6 MB）+ `lib/`（19541 个文件） |

## 分卷清单（按序）

| 文件 | 大小 |
|---|---|
| `zpaa` | 25.0 MB |
| `zpab` | 25.0 MB |
| `zpac` | 25.0 MB |
| `zpad` | 25.0 MB |
| `zpae` | 5.4 MB |

## 怎么恢复

```bash
# 1. 按字母顺序合并（顺序错了会解压失败）
cat zpaa zpab zpac zpad zpae > zig完整版.zip

# 2. 校验
md5sum zig完整版.zip
# 应输出: bf0ce2bce4e543e02c7833792bb8f17f

# 3. 解压
unzip zig完整版.zip

# 4. 验证
chmod +x zig
./zig version        # 应输出 0.16.0

# 5. 实测 C++ 能不能编（关键，验证 libcxx 确实在）
cat > t.cpp <<'EOF'
#include <iostream>
#include <vector>
int main(){ std::vector<int> v{1,2,3}; for(int i:v) std::cout<<i<<" "; std::cout<<"| C++ ok"<<std::endl; }
EOF
./zig c++ -Wno-nullability-completeness -o t t.cpp
./t                  # 应输出: 1 2 3 | C++ ok
```

> ⚠️ `zig c++` **必须带** `-Wno-nullability-completeness`，
> 否则 119 条 libcxx 警告会盖住真实错误。

## 目录结构（解压后）

```
zig          编译器二进制
lib/
  std        Zig 标准库（552 文件）
  libc       16658 文件
  libcxx     1308 文件    ← 有它才能编 C++
  libcxxabi  33 文件
  libunwind  32 文件
  compiler_rt.zig / c.zig / fuzzer.zig / ubsan_rt.zig / zig.h
```

> ⚠️ 注意：那 5 个 `.zig` / `.h` 文件要**直接放在 `lib/` 下**，
> 不能放进 `lib/compiler_rt/` 子目录，否则报
> `unable to find zig installation directory` 或
> `failed to check cache: lib/compiler_rt.zig FileNotFound`。

## 版本配套

**zls（语言服务器）必须同为 0.16.0**，版本不一致会连不上。
zls 不在这个包里，单独在 `yuanbao-relay` 主仓库，或在持久区。

## 已验证能力

- ✅ `zig version` → 0.16.0
- ✅ C++ 编译运行（iostream + vector）
- ✅ 交叉编译 `x86_64-windows-gnu` 生成 DLL
  （导出表干净，只有显式 `dllexport` 的函数）

## 更省事的替代

网络通时可直接：

```bash
pip install ziglang -i https://mirrors.cloud.tencent.com/pypi/simple
```

但这个默认给的是**残缺版**（无 libcxx，编不了 C++）。
要完整版还得补组件，所以这份备份价值更高。

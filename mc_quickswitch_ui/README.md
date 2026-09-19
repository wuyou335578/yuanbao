# 快捷切换 · QuickSwitch

网易《我的世界》中国版 · 移动端 · 带悬浮窗开关面板的附加包

---

## 一、长什么样

游戏内**右上角**有一个蓝色圆形悬浮球，写着「切」。

- **点一下** → 展开控制面板（默认收起，不挡视线）
- 面板里有 4 个按钮：

| 按钮 | 作用 |
|---|---|
| **自动换工具: 开/关** | 挖方块自动切镐/斧/铲/剑/剪刀 |
| **战斗切武器: 开/关** | 受伤时自动切武器 |
| **整理快捷栏** | 同类物品归拢、空格排到末尾 |
| **收起面板** | 把面板收回去 |

界面是 **HUD 模式**（`isHud=1`），**不屏蔽移动、视角和挖掘**——你可以一边挖矿一边点开关，不会像箱子界面那样把游戏卡住。

面板默认收起，只有那个小圆球常驻，不占地方。

---

## 二、导入方式（重点）

我已经打包成 **`.mcaddon`**，这是基岩版标准格式，**手机直接点就能装**。

### 安卓

1. 把 `QuickSwitch.mcaddon` 传到手机（微信/QQ/数据线都行）
2. 打开文件管理器，找到它，**点击**
3. 选择「用 **我的世界** 打开」（如果弹出的是中国版，长按 → 打开方式 → 选基岩版/中国版）
4. 提示「导入成功」后进游戏

### 苹果

Safari 下载 → 点下载图标 → 分享 → 「拷贝到我的世界」

### ⚠️ 导入后必须做的两步

1. **新建世界** → 往下翻 → **「启用实验性功能」全部打开**（不开脚本不生效，这是最常见的坑）
2. **行为包** 和 **资源包** **两个都要激活**：
   - 行为包：`QuickSwitch 快捷切换`
   - 资源包：`QuickSwitch 资源包`
   - 两个包互相依赖，少一个界面就出不来

> 如果打开世界提示版本不兼容，把 `manifest.json` 里的 `min_engine_version` 改成比你游戏低的版本（比如 `[1,18,0]`）。

---

## 三、界面怎么实现的（技术依据）

| 环节 | 做法 |
|---|---|
| 界面定义 | `resource_pack/ui/quickswitch.json`（JSON UI，官方格式） |
| 声明加载 | `resource_pack/ui/_ui_defs.json` |
| 贴图 | `resource_pack/textures/ui/*.png`（**我自己生成的纯色图，不依赖原版贴图**） |
| 创建 | `clientApi.CreateUI(..., {"isHud": 1})` — 官方文档明确：isHud=1 表示**不屏蔽游戏操作** |
| 注册 | `clientApi.RegisterUI(名空间, key, 类路径, "quickswitch.main")` |
| 按钮 | `asButton()` + `AddTouchEventParams({"isSwallow": True})` + `SetButtonTouchUpCallback()` |
| 时机 | 监听 `UiInitFinished` 后再创建，**不能在 `__init__` 里直接建** |

开关状态存在**服务端**（按玩家 ID 分别保存），客户端点按钮 → `NotifyToServer` → 服务端改状态 → `NotifyToClient` 回传 → 界面刷新。所以重进世界也记得你的设置。

---

## 四、和上一版的区别

| | 上一版 | 这一版 |
|---|---|---|
| 开关 | 只能聊天输 `#qs tool` | **悬浮窗点按钮** |
| 部署 | 要开 MC Studio 建组件、手动拷脚本目录 | **打包 .mcaddon，手机点一下** |
| 状态 | 全局一个开关 | **每个玩家独立**，且持久化 |
| 界面 | 无 | 悬浮球 + 面板，可收起 |

---

## 五、目录结构

```
QuickSwitch.mcaddon
├── behavior_pack/
│   ├── manifest.json
│   └── QuickSwitchScripts/          ← 必须以 Scripts 结尾，引擎才扫描
│       ├── modMain.py
│       └── QuickSwitchScripts/
│           ├── __init__.py
│           ├── ToolRules.py           方块→工具规则
│           ├── QuickSwitchServerSystem.py  核心逻辑
│           ├── QuickSwitchClientSystem.py  UI 注册/通信
│           └── QuickSwitchScreen.py        悬浮窗按钮回调
└── resource_pack/
    ├── manifest.json
    ├── ui/quickswitch.json
    ├── ui/_ui_defs.json
    └── textures/ui/*.png              8 张按钮/面板贴图
```

---

## 六、改规则

方块 → 工具的映射全在 `ToolRules.py`，改完重新打包：

```python
PICKAXE_BLOCKS = ["stone", "ore", "deepslate", ...]
AXE_BLOCKS     = ["log", "wood", "planks", ...]
SHOVEL_BLOCKS  = ["dirt", "sand", "gravel", ...]
```

子串匹配，`minecraft:diamond_ore` 命中 `"ore"` → 用镐。加模组方块就往里加关键字。

---

## 七、我没法验证的部分

**沙盒里没有《我的世界》运行环境**，所有代码依据官方文档编写，**未经真机实测**。已做的验证：

- 6 个 .py 全部 `py_compile` 通过
- 4 个 JSON 全部合法
- UI 控件路径与脚本引用**逐条比对一致**
- 核心逻辑用纯 Python 跑过（挖石头选中钻石镐、没有斧头时返回 -1 不乱切）

真机上如果出问题，按这个顺序排查：

1. **悬浮球没出现** → 检查资源包是否也激活了；看日志有没有 `[QuickSwitch] 悬浮窗已挂载`
2. **按钮点了没反应** → 看日志 `[QuickSwitch] 绑定失败`，确认 UI 路径
3. **自动切换不生效** → 确认开了实验性功能；确认在**生存模式**（创造模式引擎不触发挖掘事件）
4. **面板挡操作** → 说明 `SetIsHud(1)` 没生效，检查 `CreateUI` 的 `isHud` 参数

---

## 八、备用入口

万一 UI 出问题，聊天指令还在：

```
#qs tool      开自动换工具
#qs tooloff   关
#qs weapon    开战斗切武器
#qs weaponoff 关
#qs sort      整理快捷栏
```

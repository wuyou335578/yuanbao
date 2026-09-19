# 快捷切换模组 · QuickSwitch

网易《我的世界》中国版 · 移动端 · Mod SDK（Python）

---

## 一、功能

| 功能 | 说明 | 触发 |
|---|---|---|
| **挖方块自动换工具** | 挖石头自动拿镐、挖木头拿斧、挖土拿铲 | 自动 |
| **战斗自动切武器** | 受伤时自动切到伤害最高的剑/斧/三叉戟 | 自动 |
| **一键整理快捷栏** | 同类物品归拢、空格排到末尾 | 聊天发 `#qs sort` |

同类工具里**自动挑材质最好的**（下界合金 > 钻石 > 铁 > 金 > 石 > 木）。
手上已经是对的工具时**不会乱切**。

---

## 二、聊天指令

```
#qs            查看帮助
#qs tool       开启自动换工具
#qs tooloff    关闭自动换工具
#qs weapon     开启战斗切武器
#qs weaponoff  关闭战斗切武器
#qs sort       整理快捷栏
```

---

## 三、技术依据（接口都查过官方文档，不是猜的）

### 用到的接口

| 接口 | 归属 | 说明 |
|---|---|---|
| `CreateItem(playerId).GetPlayerItem(posType, slotPos)` | 服务端 | 背包槽位 0–35，其中 0–8 是快捷栏 |
| `CreateItem(playerId).GetSelectSlotId()` | 服务端 | 当前选中槽位，错误返回 -1 |
| `CreateItem(playerId).SetInvItemExchange(pos1, pos2)` | 服务端 | 交换背包两格 |
| **`CreatePlayer(playerId).ChangeSelectSlot(slot)`** | 服务端 | **切换选中快捷栏，slot 0–8** |

`ChangeSelectSlot` 是这个模组的地基——中国版 Mod SDK 直接提供了切换接口，不需要像国际版 SAPI 那样绕道 `container.moveItem`。

### 用到的事件

| 事件 | 触发时机 | 关键参数 |
|---|---|---|
| `StartDestroyBlockServerEvent` | 玩家开始挖方块（**创造模式不触发**） | `playerId`, `blockName`, `x/y/z` |
| `ActuallyHurtServerEvent` | 实体实际受伤 | `entityId`, `srcId`, `damage`, `cause` |
| `ServerChatEvent` | 玩家聊天 | `playerId`, `message` |

---

## 四、部署步骤

### 1. 用开发者编辑器建组件

1. 打开 **我的世界开发者工作台**（MC Studio）
2. 新建 **基岩版组件** → 选「空白」或「玩法组件」
3. 在作品里找到脚本目录，把 `Script_QuickSwitch/` 整个放进去
4. `modMain.py` 放到脚本根目录

目录长这样：

```
你的组件/
├── behavior_pack/
│   └── manifest.json      ← 编辑器会自动生成
└── Script_QuickSwitch/    ← 本包的脚本目录
    ├── modMain.py
    └── Script_QuickSwitch/
        ├── __init__.py
        ├── ToolRules.py
        ├── QuickSwitchServerSystem.py
        └── QuickSwitchClientSystem.py
```

⚠️ `modMain.py` 里的注册路径是
`Script_QuickSwitch.QuickSwitchServerSystem.QuickSwitchServerSystem`
——**必须和你实际的目录结构一致**，否则引擎加载不到 System。

### 2. 测试

在编辑器里点「运行测试」，用 PC 开发包进游戏验证：

- 手上拿面包去挖石头 → 应该自动切成镐
- 聊天发 `#qs sort` → 快捷栏自动归拢
- 看控制台 `[QuickSwitch]` 开头的日志

### 3. 导出到手机

编辑器 → 作品库 → 基岩版组件 → 【更多】→【导出】→ 得到 **.zip**

手机导入两种方式：

**方式 A（推荐）**
1. zip 传手机
2. 文件管理器点它 → 选「用我的世界打开」
3. 游戏内提示导入成功
4. 新建世界 → **勾选「启用实验性功能」**（关键！很多脚本功能不开这个不生效）
5. 行为包列表里激活它

**方式 B（手动放目录）**
```
Android/data/com.netease.mc.mi/files/games/com.netease/behavior_packs/
```
（包名因下载渠道不同可能不是 `com.netease.mc.mi`，用 MT 管理器看实际路径）

---

## 五、自己改规则

方块 → 工具的映射全在 `ToolRules.py`，改这个文件就行，不用碰主逻辑：

```python
PICKAXE_BLOCKS = ["stone", "ore", "deepslate", ...]
AXE_BLOCKS     = ["log", "wood", "planks", ...]
SHOVEL_BLOCKS  = ["dirt", "sand", "gravel", ...]
```

用的是**子串匹配**，`minecraft:diamond_ore` 命中 `"ore"` → 用镐。

想加模组物品（比如暮色森林的方块），往对应列表里加关键字即可。

---

## 六、可调开关

在 `QuickSwitchServerSystem.py` 顶部：

```python
AUTO_TOOL = True            # 挖方块自动换工具
AUTO_WEAPON = True          # 战斗自动切武器
SWITCH_SHIELD_FIRST = False # 受伤先切盾牌（默认关）
HOTBAR_SIZE = 9
```

---

## 七、我没法验证的部分

**沙盒里没有《我的世界》运行环境**，以上代码是依据官方文档写的，
**未经真机/开发包实测**。

有几处请重点确认：

1. `ChangeSelectSlot` 的 slot 上限 —— 文档一处写 0–8、一处写最大为 8，代码按 0–8（9 格）写，若报错改 `HOTBAR_SIZE`
2. `_isPlayer()` 里的 `CreateEngineType` / `GetPlayerList` —— 不同版本接口名可能有出入，拿不到时会退化成「当玩家处理」
3. 事件参数若与你的版本不符，在回调里加 `print(args)` 看实际字段

---

## 八、已知限制

- **创造模式不触发**挖掘事件（引擎行为），自动换工具在生存/冒险模式才生效
- 战斗切换只在**玩家受伤**时触发；想要「看到怪就切武器」需要改判定条件（代码里有注释标了位置）
- 快捷栏整理是冒泡交换，格子少所以很快，但会真实改动背包顺序

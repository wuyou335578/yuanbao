# -*- coding: utf-8 -*-
"""
快捷切换模组 —— 服务端系统

功能：
  1. 挖方块时自动切到最佳工具（镐/斧/铲/剑/剪刀）
  2. 受伤/战斗时自动切到武器
  3. 聊天指令：整理快捷栏、开关功能

用到的官方接口（均已查证）：
  CreateItem(playerId).GetPlayerItem(posType, slotPos)  -> dict / None
  CreateItem(playerId).GetSelectSlotId()                -> int
  CreateItem(playerId).SetInvItemExchange(pos1, pos2)   -> bool
  CreatePlayer(playerId).ChangeSelectSlot(slot)         -> bool   (0~8)

用到的官方事件（均已查证）：
  StartDestroyBlockServerEvent  玩家开始挖方块（创造模式不触发）
  ActuallyHurtServerEvent       实体实际受伤（含 srcId 伤害源）
  ServerChatEvent               玩家聊天
"""

import mod.server.extraServerApi as serverApi
from mod.server.system.serverSystem import ServerSystem

from Script_QuickSwitch.ToolRules import (
    PICKAXE, AXE, SHOVEL, SWORD, SHEARS,
    TOOL_SUFFIX, MATERIAL_RANK,
    PICKAXE_BLOCKS, AXE_BLOCKS, SHOVEL_BLOCKS, SWORD_BLOCKS, SHEARS_BLOCKS,
    WEAPON_KEYWORDS, SHIELD_KEYWORDS,
)

# ---------- 可调开关 ----------
AUTO_TOOL = True        # 挖方块自动换工具
AUTO_WEAPON = True      # 战斗自动切武器
SWITCH_SHIELD_FIRST = False   # 受伤时优先切盾牌（副手逻辑不同，默认关）
HOTBAR_SIZE = 9         # 快捷栏格数
INVENTORY_SIZE = 36     # 背包总槽位


class QuickSwitchServerSystem(ServerSystem):

    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)

        # 运行期开关（可用聊天指令改）
        self.autoTool = AUTO_TOOL
        self.autoWeapon = AUTO_WEAPON

        engineNs = serverApi.GetEngineNamespace()
        engineSys = serverApi.GetEngineSystemName()

        # 监听：开始挖方块
        self.ListenForEvent(engineNs, engineSys,
                            "StartDestroyBlockServerEvent",
                            self, self.OnStartDestroyBlock)

        # 监听：实体实际受伤
        self.ListenForEvent(engineNs, engineSys,
                            "ActuallyHurtServerEvent",
                            self, self.OnActuallyHurt)

        # 监听：聊天指令
        self.ListenForEvent(engineNs, engineSys,
                            "ServerChatEvent",
                            self, self.OnChat)

        print("[QuickSwitch] 服务端系统已启动")

    # ============================================================
    #  基础工具方法
    # ============================================================

    def _itemComp(self, playerId):
        return serverApi.GetEngineCompFactory().CreateItem(playerId)

    def _playerComp(self, playerId):
        return serverApi.GetEngineCompFactory().CreatePlayer(playerId)

    def GetHotbar(self, playerId):
        """读取快捷栏 9 格，返回 list，元素为 dict 或 None"""
        comp = self._itemComp(playerId)
        posType = serverApi.GetMinecraftEnum().ItemPosType.INVENTORY
        result = []
        for slot in range(HOTBAR_SIZE):
            try:
                item = comp.GetPlayerItem(posType, slot)
            except Exception:
                item = None
            result.append(item)
        return result

    @staticmethod
    def ItemName(item):
        """安全取物品名，空返回 ''"""
        if not item:
            return ""
        name = item.get("itemName") or item.get("newItemName") or ""
        return str(name)

    @staticmethod
    def ClassifyTool(itemName):
        """判定物品属于哪种工具，非工具返回 None"""
        if not itemName:
            return None
        low = itemName.lower()
        for suffix, toolType in TOOL_SUFFIX:
            if suffix in low:
                return toolType
        return None

    @staticmethod
    def MaterialRank(itemName):
        """取材质等级，用于同类工具里挑最好的"""
        low = (itemName or "").lower()
        best = 0
        for mat, rank in MATERIAL_RANK.items():
            if mat in low:
                best = max(best, rank)
        return best

    def FindBestSlot(self, playerId, wantType):
        """
        在快捷栏里找 wantType 类型、材质最好的那一格
        返回槽位 index，找不到返回 -1
        """
        hotbar = self.GetHotbar(playerId)
        bestSlot = -1
        bestRank = -1
        for slot in range(len(hotbar)):
            item = hotbar[slot]
            name = self.ItemName(item)
            if not name:
                continue
            toolType = self.ClassifyTool(name)
            if toolType != wantType:
                continue
            rank = self.MaterialRank(name)
            if rank > bestRank:
                bestRank = rank
                bestSlot = slot
        return bestSlot

    def SwitchTo(self, playerId, slot):
        """切换选中槽位"""
        if slot < 0 or slot >= HOTBAR_SIZE:
            return False
        try:
            comp = self._playerComp(playerId)
            return bool(comp.ChangeSelectSlot(slot))
        except Exception as e:
            print("[QuickSwitch] ChangeSelectSlot 失败: %s" % str(e))
            return False

    def AlreadyHolding(self, playerId, wantType):
        """当前手上的已经是目标工具吗"""
        comp = self._itemComp(playerId)
        try:
            cur = comp.GetSelectSlotId()
        except Exception:
            return False
        if cur < 0 or cur >= HOTBAR_SIZE:
            return False
        hotbar = self.GetHotbar(playerId)
        name = self.ItemName(hotbar[cur])
        return self.ClassifyTool(name) == wantType

    # ============================================================
    #  功能 1：挖方块自动换工具
    # ============================================================

    @staticmethod
    def BlockToTool(blockName):
        """方块名 -> 需要的工具类型"""
        if not blockName:
            return None
        b = blockName.lower()
        # 去掉命名空间前缀也能匹配，这里统一用子串
        for key in PICKAXE_BLOCKS:
            if key in b:
                return PICKAXE
        for key in AXE_BLOCKS:
            if key in b:
                return AXE
        for key in SHOVEL_BLOCKS:
            if key in b:
                return SHOVEL
        for key in SWORD_BLOCKS:
            if key in b:
                return SWORD
        for key in SHEARS_BLOCKS:
            if key in b:
                return SHEARS
        return None

    def OnStartDestroyBlock(self, args):
        """玩家开始挖方块"""
        if not self.autoTool:
            return
        playerId = args.get("playerId")
        blockName = args.get("blockName", "")
        if not playerId:
            return

        wantType = self.BlockToTool(blockName)
        if not wantType:
            return  # 这个方块不需要特定工具，保持手上物品

        # 已经拿着对的就别动
        if self.AlreadyHolding(playerId, wantType):
            return

        slot = self.FindBestSlot(playerId, wantType)
        if slot >= 0:
            self.SwitchTo(playerId, slot)
            print("[QuickSwitch] %s -> 切到 %s (槽位 %d)" % (blockName, wantType, slot))

    # ============================================================
    #  功能 2：战斗自动切武器
    # ============================================================

    def OnActuallyHurt(self, args):
        """实体实际受伤"""
        if not self.autoWeapon:
            return
        entityId = args.get("entityId")
        srcId = args.get("srcId", "")
        if not entityId:
            return

        # 只处理「玩家受伤」；如果你想改成「玩家打怪时切武器」，
        # 判断条件换成 entityId != playerId 且 srcId == playerId
        # 玩家 id 列表用 serverApi.GetPlayerList()（接口名以你版本文档为准）

        # 受伤的是玩家 -> 切到武器自卫
        if self._isPlayer(entityId):
            if SWITCH_SHIELD_FIRST:
                slot = self._findKeywordSlot(entityId, SHIELD_KEYWORDS)
                if slot >= 0:
                    self.SwitchTo(entityId, slot)
                    return
            slot = self._findWeaponSlot(entityId)
            if slot >= 0:
                self.SwitchTo(entityId, slot)
                print("[QuickSwitch] 玩家受伤 -> 切武器 (槽位 %d)" % slot)

    def _isPlayer(self, entityId):
        """判断是否是玩家。用引擎类型判断，拿不到就当玩家处理"""
        try:
            comp = serverApi.GetEngineCompFactory().CreateEngineType(entityId)
            t = comp.GetEngineTypeStr()
            return (t == "minecraft:player")
        except Exception:
            # 拿不到类型时，退化为「在线玩家列表」判断
            try:
                return entityId in serverApi.GetPlayerList()
            except Exception:
                return True

    def _findWeaponSlot(self, playerId):
        """找快捷栏里最好的武器"""
        hotbar = self.GetHotbar(playerId)
        bestSlot = -1
        bestRank = -1
        for slot in range(len(hotbar)):
            name = self.ItemName(hotbar[slot]).lower()
            if not name:
                continue
            hit = False
            for kw in WEAPON_KEYWORDS:
                if kw in name:
                    hit = True
                    break
            if not hit:
                continue
            rank = self.MaterialRank(name)
            if rank > bestRank:
                bestRank = rank
                bestSlot = slot
        return bestSlot

    def _findKeywordSlot(self, playerId, keywords):
        """按关键字找物品（如盾牌）"""
        hotbar = self.GetHotbar(playerId)
        for slot in range(len(hotbar)):
            name = self.ItemName(hotbar[slot]).lower()
            if not name:
                continue
            for kw in keywords:
                if kw in name:
                    return slot
        return -1

    # ============================================================
    #  功能 3：整理快捷栏
    # ============================================================

    def SortHotbar(self, playerId):
        """
        整理快捷栏：同类物品归拢，空格移到末尾。
        引擎只提供「交换两格」接口，所以用冒泡排序实现。
        """
        comp = self._itemComp(playerId)
        hotbar = self.GetHotbar(playerId)

        # 排序键：空=排最后(1)，否则按 itemName(0)
        def sortKey(item):
            name = self.ItemName(item)
            return (1, "") if not name else (0, name)

        # 冒泡：只动必要的交换
        n = len(hotbar)
        moved = 0
        for i in range(n):
            for j in range(0, n - 1 - i):
                a = hotbar[j]
                b = hotbar[j + 1]
                if sortKey(a) > sortKey(b):
                    ok = comp.SetInvItemExchange(j, j + 1)
                    if ok:
                        hotbar[j], hotbar[j + 1] = b, a
                        moved += 1
        print("[QuickSwitch] 整理快捷栏完成，交换 %d 次" % moved)
        return moved

    # ============================================================
    #  聊天指令
    # ============================================================

    def OnChat(self, args):
        playerId = args.get("playerId")
        message = (args.get("message") or "").strip()
        if not playerId or not message:
            return

        cmd = message.lower()

        if cmd in ("#qs", "#qs help", "#切换"):
            self._help(playerId)
        elif cmd in ("#qs tool", "#工具开"):
            self.autoTool = True
        elif cmd in ("#qs tooloff", "#工具关"):
            self.autoTool = False
        elif cmd in ("#qs weapon", "#武器开"):
            self.autoWeapon = True
        elif cmd in ("#qs weaponoff", "#武器关"):
            self.autoWeapon = False
        elif cmd in ("#qs sort", "#整理"):
            self.SortHotbar(playerId)

    def _help(self, playerId):
        lines = [
            "===== 快捷切换 =====",
            "#qs tool     开启自动换工具",
            "#qs tooloff  关闭自动换工具",
            "#qs weapon   开启战斗切武器",
            "#qs weaponoff 关闭战斗切武器",
            "#qs sort     整理快捷栏",
        ]
        for line in lines:
            print("[QuickSwitch] %s" % line)

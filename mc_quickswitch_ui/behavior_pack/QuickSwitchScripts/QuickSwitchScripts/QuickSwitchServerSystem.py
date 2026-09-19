# -*- coding: utf-8 -*-
"""
快捷切换模组 —— 服务端系统

功能：
  1. 挖方块时自动切到最佳工具（镐/斧/铲/剑/剪刀）
  2. 受伤时自动切到武器
  3. 一键整理快捷栏
  4. 接收悬浮窗开关，按玩家分别保存状态

官方接口（均已查证）：
  CreateItem(playerId).GetPlayerItem(posType, slotPos)  -> dict / None
  CreateItem(playerId).GetSelectSlotId()                -> int
  CreateItem(playerId).SetInvItemExchange(pos1, pos2)   -> bool
  CreatePlayer(playerId).ChangeSelectSlot(slot)         -> bool  (0~8)

官方事件（均已查证）：
  StartDestroyBlockServerEvent  玩家开始挖方块（创造模式不触发）
  ActuallyHurtServerEvent       实体实际受伤
  ServerChatEvent               玩家聊天（备用指令）
"""

import mod.server.extraServerApi as serverApi
from mod.server.system.serverSystem import ServerSystem

try:
    from QuickSwitchScripts.ToolRules import (
        PICKAXE, AXE, SHOVEL, SWORD, SHEARS,
        TOOL_SUFFIX, MATERIAL_RANK,
        PICKAXE_BLOCKS, AXE_BLOCKS, SHOVEL_BLOCKS, SWORD_BLOCKS, SHEARS_BLOCKS,
        WEAPON_KEYWORDS, SHIELD_KEYWORDS,
    )
except ImportError:
    from ToolRules import (
        PICKAXE, AXE, SHOVEL, SWORD, SHEARS,
        TOOL_SUFFIX, MATERIAL_RANK,
        PICKAXE_BLOCKS, AXE_BLOCKS, SHOVEL_BLOCKS, SWORD_BLOCKS, SHEARS_BLOCKS,
        WEAPON_KEYWORDS, SHIELD_KEYWORDS,
    )

MOD_NAME = "QuickSwitch"
SERVER_SYSTEM = "QuickSwitchServer"
CLIENT_SYSTEM = "QuickSwitchClient"

EVT_TOGGLE = "QuickSwitchToggle"
EVT_QUERY = "QuickSwitchQuery"
EVT_SYNC = "QuickSwitchSync"

HOTBAR_SIZE = 9
DEFAULT_AUTO_TOOL = True
DEFAULT_AUTO_WEAPON = True


class QuickSwitchServerSystem(ServerSystem):

    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)

        # 每个玩家一套开关，默认全开
        self.mAutoTool = {}
        self.mAutoWeapon = {}

        engineNs = serverApi.GetEngineNamespace()
        engineSys = serverApi.GetEngineSystemName()

        self.ListenForEvent(engineNs, engineSys,
                            "StartDestroyBlockServerEvent",
                            self, self.OnStartDestroyBlock)
        self.ListenForEvent(engineNs, engineSys,
                            "ActuallyHurtServerEvent",
                            self, self.OnActuallyHurt)
        self.ListenForEvent(engineNs, engineSys,
                            "ServerChatEvent",
                            self, self.OnChat)

        # 悬浮窗发来的开关
        self.ListenForEvent(MOD_NAME, CLIENT_SYSTEM, EVT_TOGGLE,
                            self, self.OnToggle)
        self.ListenForEvent(MOD_NAME, CLIENT_SYSTEM, EVT_QUERY,
                            self, self.OnQuery)

        self.DefineEvent(EVT_SYNC)

        print("[QuickSwitch] 服务端系统已启动")

    # ============================================================
    #  开关状态
    # ============================================================

    def _autoTool(self, playerId):
        return self.mAutoTool.get(playerId, DEFAULT_AUTO_TOOL)

    def _autoWeapon(self, playerId):
        return self.mAutoWeapon.get(playerId, DEFAULT_AUTO_WEAPON)

    def _sync(self, playerId):
        """把当前开关状态推给该玩家的悬浮窗"""
        self.NotifyToClient(playerId, EVT_SYNC, {
            "autoTool": self._autoTool(playerId),
            "autoWeapon": self._autoWeapon(playerId),
        })

    def OnQuery(self, args):
        playerId = args.get("playerId")
        if playerId:
            self._sync(playerId)

    def OnToggle(self, args):
        playerId = args.get("playerId")
        key = args.get("key")
        value = args.get("value")
        if not playerId:
            return

        if key == "autoTool":
            self.mAutoTool[playerId] = bool(value)
        elif key == "autoWeapon":
            self.mAutoWeapon[playerId] = bool(value)
        elif key == "sort":
            self.SortHotbar(playerId)

        self._sync(playerId)

    # ============================================================
    #  基础方法
    # ============================================================

    def _itemComp(self, playerId):
        return serverApi.GetEngineCompFactory().CreateItem(playerId)

    def _playerComp(self, playerId):
        return serverApi.GetEngineCompFactory().CreatePlayer(playerId)

    def GetHotbar(self, playerId):
        comp = self._itemComp(playerId)
        posType = serverApi.GetMinecraftEnum().ItemPosType.INVENTORY
        out = []
        for slot in range(HOTBAR_SIZE):
            try:
                out.append(comp.GetPlayerItem(posType, slot))
            except Exception:
                out.append(None)
        return out

    @staticmethod
    def ItemName(item):
        if not item:
            return ""
        return str(item.get("itemName") or item.get("newItemName") or "")

    @staticmethod
    def ClassifyTool(itemName):
        if not itemName:
            return None
        low = itemName.lower()
        for suffix, toolType in TOOL_SUFFIX:
            if suffix in low:
                return toolType
        return None

    @staticmethod
    def MaterialRank(itemName):
        low = (itemName or "").lower()
        best = 0
        for mat, rank in MATERIAL_RANK.items():
            if mat in low:
                best = max(best, rank)
        return best

    def FindBestSlot(self, playerId, wantType):
        hotbar = self.GetHotbar(playerId)
        bestSlot, bestRank = -1, -1
        for slot in range(len(hotbar)):
            name = self.ItemName(hotbar[slot])
            if not name or self.ClassifyTool(name) != wantType:
                continue
            rank = self.MaterialRank(name)
            if rank > bestRank:
                bestRank, bestSlot = rank, slot
        return bestSlot

    def SwitchTo(self, playerId, slot):
        if slot < 0 or slot >= HOTBAR_SIZE:
            return False
        try:
            return bool(self._playerComp(playerId).ChangeSelectSlot(slot))
        except Exception as e:
            print("[QuickSwitch] ChangeSelectSlot 失败: %s" % str(e))
            return False

    def AlreadyHolding(self, playerId, wantType):
        try:
            cur = self._itemComp(playerId).GetSelectSlotId()
        except Exception:
            return False
        if cur < 0 or cur >= HOTBAR_SIZE:
            return False
        return self.ClassifyTool(self.ItemName(self.GetHotbar(playerId)[cur])) == wantType

    # ============================================================
    #  功能 1：挖方块自动换工具
    # ============================================================

    @staticmethod
    def BlockToTool(blockName):
        if not blockName:
            return None
        b = blockName.lower()
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
        playerId = args.get("playerId")
        blockName = args.get("blockName", "")
        if not playerId or not self._autoTool(playerId):
            return

        wantType = self.BlockToTool(blockName)
        if not wantType or self.AlreadyHolding(playerId, wantType):
            return

        slot = self.FindBestSlot(playerId, wantType)
        if slot >= 0:
            self.SwitchTo(playerId, slot)

    # ============================================================
    #  功能 2：战斗自动切武器
    # ============================================================

    def OnActuallyHurt(self, args):
        entityId = args.get("entityId")
        if not entityId or not self._autoWeapon(entityId):
            return
        if not self._isPlayer(entityId):
            return
        slot = self._findWeaponSlot(entityId)
        if slot >= 0:
            self.SwitchTo(entityId, slot)

    def _isPlayer(self, entityId):
        try:
            comp = serverApi.GetEngineCompFactory().CreateEngineType(entityId)
            return comp.GetEngineTypeStr() == "minecraft:player"
        except Exception:
            try:
                return entityId in serverApi.GetPlayerList()
            except Exception:
                return True

    def _findWeaponSlot(self, playerId):
        hotbar = self.GetHotbar(playerId)
        bestSlot, bestRank = -1, -1
        for slot in range(len(hotbar)):
            name = self.ItemName(hotbar[slot]).lower()
            if not name:
                continue
            if not any(kw in name for kw in WEAPON_KEYWORDS):
                continue
            rank = self.MaterialRank(name)
            if rank > bestRank:
                bestRank, bestSlot = rank, slot
        return bestSlot

    def _findKeywordSlot(self, playerId, keywords):
        hotbar = self.GetHotbar(playerId)
        for slot in range(len(hotbar)):
            name = self.ItemName(hotbar[slot]).lower()
            if name and any(kw in name for kw in keywords):
                return slot
        return -1

    # ============================================================
    #  功能 3：整理快捷栏
    # ============================================================

    def SortHotbar(self, playerId):
        comp = self._itemComp(playerId)
        hotbar = self.GetHotbar(playerId)

        def sortKey(item):
            name = self.ItemName(item)
            return (1, "") if not name else (0, name)

        moved = 0
        n = len(hotbar)
        for i in range(n):
            for j in range(0, n - 1 - i):
                if sortKey(hotbar[j]) > sortKey(hotbar[j + 1]):
                    if comp.SetInvItemExchange(j, j + 1):
                        hotbar[j], hotbar[j + 1] = hotbar[j + 1], hotbar[j]
                        moved += 1
        return moved

    # ============================================================
    #  聊天指令（悬浮窗的备用入口）
    # ============================================================

    def OnChat(self, args):
        playerId = args.get("playerId")
        cmd = (args.get("message") or "").strip().lower()
        if not playerId or not cmd:
            return

        if cmd == "#qs tool":
            self.mAutoTool[playerId] = True
        elif cmd == "#qs tooloff":
            self.mAutoTool[playerId] = False
        elif cmd == "#qs weapon":
            self.mAutoWeapon[playerId] = True
        elif cmd == "#qs weaponoff":
            self.mAutoWeapon[playerId] = False
        elif cmd == "#qs sort":
            self.SortHotbar(playerId)
        else:
            return
        self._sync(playerId)

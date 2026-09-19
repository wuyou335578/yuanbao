# -*- coding: utf-8 -*-
"""
快捷切换模组 —— 客户端系统

职责：
  1. 监听 UiInitFinished，注册并创建悬浮窗（HUD 模式）
  2. 把悬浮窗上的按钮操作转发给服务端
  3. 接收服务端下发的状态，刷新界面显示
"""

import mod.client.extraClientApi as clientApi
from mod.client.system.clientSystem import ClientSystem

MOD_NAME = "QuickSwitch"
SERVER_SYSTEM = "QuickSwitchServer"
CLIENT_SYSTEM = "QuickSwitchClient"

UI_KEY = "QuickSwitchMain"
UI_SCREEN_PATH = "QuickSwitchScripts.QuickSwitchScreen.QuickSwitchScreen"
UI_DEF = "quickswitch.main"          # 命名空间.画布名，对应 resource_pack/ui/quickswitch.json

EVT_TOGGLE = "QuickSwitchToggle"     # 客户端 -> 服务端
EVT_QUERY = "QuickSwitchQuery"       # 客户端 -> 服务端（要一次当前状态）
EVT_SYNC = "QuickSwitchSync"         # 服务端 -> 客户端


class QuickSwitchClientSystem(ClientSystem):

    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self.mUiNode = None

        engineNs = clientApi.GetEngineNamespace()
        engineSys = clientApi.GetEngineSystemName()

        # UI 框架初始化完成后才能创建界面
        self.ListenForEvent(engineNs, engineSys, "UiInitFinished",
                            self, self.OnUiInitFinished)

        # 接收服务端下发的开关状态
        self.ListenForEvent(MOD_NAME, SERVER_SYSTEM, EVT_SYNC,
                            self, self.OnSync)

        self.DefineEvent(EVT_TOGGLE)
        self.DefineEvent(EVT_QUERY)

        print("[QuickSwitch] 客户端系统已启动")

    # ---------------- UI 创建 ----------------

    def OnUiInitFinished(self, args):
        try:
            clientApi.RegisterUI(MOD_NAME, UI_KEY, UI_SCREEN_PATH, UI_DEF)
        except Exception as e:
            print("[QuickSwitch] RegisterUI 失败: %s" % str(e))
            return

        try:
            # isHud=1：界面不屏蔽游戏操作，能边挖边点
            self.mUiNode = clientApi.CreateUI(MOD_NAME, UI_KEY, {"isHud": 1})
        except Exception as e:
            print("[QuickSwitch] CreateUI 失败: %s" % str(e))
            return

        if self.mUiNode:
            self.mUiNode.mClient = self
            print("[QuickSwitch] 悬浮窗已挂载（HUD 模式）")
            # 向服务端要一次当前开关状态
            self.NotifyToServer(EVT_QUERY, {"playerId": clientApi.GetLocalPlayerId()})
        else:
            print("[QuickSwitch] 悬浮窗创建返回 None")

    # ---------------- 按钮 -> 服务端 ----------------

    def RequestToggle(self, key, value):
        playerId = clientApi.GetLocalPlayerId()
        self.NotifyToServer(EVT_TOGGLE, {
            "playerId": playerId,
            "key": key,
            "value": value,
        })

    # ---------------- 服务端 -> 界面 ----------------

    def OnSync(self, args):
        if self.mUiNode:
            self.mUiNode.SyncState(args or {})

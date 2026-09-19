# -*- coding: utf-8 -*-
"""
快捷切换模组 - 主入口
网易《我的世界》中国版 · Mod SDK（Python）

目录结构（行为包内）：
    behavior_pack/
    └── QuickSwitchScripts/          ← 必须以 Scripts 结尾，引擎才会扫描
        ├── modMain.py
        └── QuickSwitchScripts/      ← 子包
            ├── __init__.py
            ├── ToolRules.py
            ├── QuickSwitchServerSystem.py
            ├── QuickSwitchClientSystem.py
            └── QuickSwitchScreen.py
"""

from mod.common.mod import Mod
import mod.server.extraServerApi as serverApi
import mod.client.extraClientApi as clientApi

MOD_NAME = "QuickSwitch"
SERVER_SYSTEM = "QuickSwitchServer"
CLIENT_SYSTEM = "QuickSwitchClient"


@Mod.Binding(name=MOD_NAME, version="1.0.0")
class QuickSwitchMod(object):

    def __init__(self):
        pass

    @Mod.InitServer()
    def initServer(self):
        serverApi.RegisterSystem(
            MOD_NAME, SERVER_SYSTEM,
            "QuickSwitchScripts.QuickSwitchScripts.QuickSwitchServerSystem.QuickSwitchServerSystem"
        )

    @Mod.InitClient()
    def initClient(self):
        clientApi.RegisterSystem(
            MOD_NAME, CLIENT_SYSTEM,
            "QuickSwitchScripts.QuickSwitchScripts.QuickSwitchClientSystem.QuickSwitchClientSystem"
        )

    @Mod.DestroyServer()
    def destroyServer(self):
        pass

    @Mod.DestroyClient()
    def destroyClient(self):
        pass

# -*- coding: utf-8 -*-
"""
快捷切换模组 - 主入口
网易《我的世界》中国版 Mod SDK（Python）

目录约定（放进组件的脚本目录）：
    QuickSwitch/
    ├── modMain.py
    └── Script_QuickSwitch/
        ├── __init__.py
        ├── QuickSwitchServerSystem.py
        └── QuickSwitchClientSystem.py

注册路径与目录名必须一致，否则引擎找不到 System。
"""

from mod.common.mod import Mod
import mod.server.extraServerApi as serverApi
import mod.client.extraClientApi as clientApi


@Mod.Binding(name="QuickSwitch", version="1.0.0")
class QuickSwitchMod(object):

    def __init__(self):
        pass

    @Mod.InitServer()
    def initServer(self):
        serverApi.RegisterSystem(
            "QuickSwitch",
            "QuickSwitchServer",
            "Script_QuickSwitch.QuickSwitchServerSystem.QuickSwitchServerSystem"
        )

    @Mod.InitClient()
    def initClient(self):
        clientApi.RegisterSystem(
            "QuickSwitch",
            "QuickSwitchClient",
            "Script_QuickSwitch.QuickSwitchClientSystem.QuickSwitchClientSystem"
        )

    @Mod.DestroyServer()
    def destroyServer(self):
        pass

    @Mod.DestroyClient()
    def destroyClient(self):
        pass

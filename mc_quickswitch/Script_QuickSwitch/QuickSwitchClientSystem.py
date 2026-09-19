# -*- coding: utf-8 -*-
"""
快捷切换模组 —— 客户端系统

本模组的核心逻辑全在服务端，客户端这里只做初始化占位。
如果你想加 UI 提示（比如切换时弹一条 tip），在这里扩展即可，
但注意：客户端只能操作「本地玩家」的背包数据。
"""

import mod.client.extraClientApi as clientApi
from mod.client.system.clientSystem import ClientSystem


class QuickSwitchClientSystem(ClientSystem):

    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        print("[QuickSwitch] 客户端系统已启动")

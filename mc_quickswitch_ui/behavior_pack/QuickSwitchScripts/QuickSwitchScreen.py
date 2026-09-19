# -*- coding: utf-8 -*-
"""
快捷切换模组 —— 悬浮窗界面（客户端）

用 CreateUI(..., {"isHud": 1}) 创建，不屏蔽游戏操作，可以一边挖矿一边点开关。
右上角一个「切」字悬浮球，点开是控制面板。
"""

import mod.client.extraClientApi as clientApi

ScreenNode = clientApi.GetScreenNodeCls()

# 控件路径（与 resource_pack/ui/quickswitch.json 对应）
PATH_PANEL = "/control_panel"
PATH_FAB = "/fab"
PATH_TOOL = "/control_panel/tool_btn"
PATH_WEAPON = "/control_panel/weapon_btn"
PATH_SORT = "/control_panel/sort_btn"
PATH_HIDE = "/control_panel/hide_btn"
PATH_TOOL_LABEL = PATH_TOOL + "/button_label"
PATH_WEAPON_LABEL = PATH_WEAPON + "/button_label"
PATH_SORT_LABEL = PATH_SORT + "/button_label"
PATH_HIDE_LABEL = PATH_HIDE + "/button_label"


class QuickSwitchScreen(ScreenNode):

    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        self.mPanelOpen = False
        self.mAutoTool = True
        self.mAutoWeapon = True
        self.mClient = None          # 客户端系统实例，由外部注入

    # ---------------- 生命周期 ----------------

    def Create(self):
        """UI 创建成功时由引擎调用"""
        # 设为 HUD 模式：不屏蔽移动、视角、挖掘
        self.SetIsHud(1)

        self._bindButton(PATH_FAB, self.OnFabClick)
        self._bindButton(PATH_TOOL, self.OnToolClick)
        self._bindButton(PATH_WEAPON, self.OnWeaponClick)
        self._bindButton(PATH_SORT, self.OnSortClick)
        self._bindButton(PATH_HIDE, self.OnHideClick)

        self.SetText(PATH_TOOL_LABEL, "自动换工具: 开")
        self.SetText(PATH_WEAPON_LABEL, "战斗切武器: 开")
        self.SetText(PATH_SORT_LABEL, "整理快捷栏")
        self.SetText(PATH_HIDE_LABEL, "收起面板")

        # 面板默认收起
        self._setPanelVisible(False)

        print("[QuickSwitch] 悬浮窗已创建")

    # ---------------- 基础设施 ----------------

    def _bindButton(self, path, callback):
        """绑定按钮点击（移动端触摸）"""
        try:
            btn = self.GetBaseUIControl(path).asButton()
            if not btn:
                print("[QuickSwitch] 按钮不存在: %s" % path)
                return False
            btn.AddTouchEventParams({"isSwallow": True})
            btn.SetButtonTouchUpCallback(callback)
            return True
        except Exception as e:
            print("[QuickSwitch] 绑定失败 %s: %s" % (path, str(e)))
            return False

    def SetText(self, path, text):
        """改控件文字，失败不影响主流程"""
        try:
            ctrl = self.GetBaseUIControl(path)
            if ctrl:
                ctrl.asLabel().SetText(text)
                return True
        except Exception as e:
            print("[QuickSwitch] SetText 失败 %s: %s" % (path, str(e)))
        return False

    def _setPanelVisible(self, visible):
        """显示/隐藏控制面板"""
        try:
            ctrl = self.GetBaseUIControl(PATH_PANEL)
            if ctrl:
                ctrl.SetVisible(visible)
                self.mPanelOpen = visible
                return True
        except Exception as e:
            print("[QuickSwitch] SetVisible 失败: %s" % str(e))
        return False

    # ---------------- 按钮回调 ----------------

    def OnFabClick(self, args):
        """点悬浮球：展开/收起面板"""
        self._setPanelVisible(not self.mPanelOpen)

    def OnHideClick(self, args):
        self._setPanelVisible(False)

    def OnToolClick(self, args):
        self.mAutoTool = not self.mAutoTool
        self._notify("autoTool", self.mAutoTool)

    def OnWeaponClick(self, args):
        self.mAutoWeapon = not self.mAutoWeapon
        self._notify("autoWeapon", self.mAutoWeapon)

    def OnSortClick(self, args):
        self._notify("sort", True)

    def _notify(self, key, value):
        """把开关变化发给服务端"""
        if self.mClient:
            self.mClient.RequestToggle(key, value)

    # ---------------- 状态同步 ----------------

    def SyncState(self, data):
        """收到服务端状态后刷新界面"""
        if "autoTool" in data:
            self.mAutoTool = bool(data["autoTool"])
        if "autoWeapon" in data:
            self.mAutoWeapon = bool(data["autoWeapon"])
        self.SetText(PATH_TOOL_LABEL, "自动换工具: %s" % ("开" if self.mAutoTool else "关"))
        self.SetText(PATH_WEAPON_LABEL, "战斗切武器: %s" % ("开" if self.mAutoWeapon else "关"))

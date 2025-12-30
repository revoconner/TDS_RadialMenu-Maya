from .TDS_buildRadialMenu_UI import buildRadialMenu_UI

from . import radialWidget
radialWidget.set_live_reload(False)

import importlib
importlib.reload(TDS_buildRadialMenu_UI)

def show_window():
    TDS_buildRadialMenu_UI.show_window()

def run_menu():
    import radialMenu_main

# radialMenu_main.py (or wherever your RMB-hold callback lives)
import sys, importlib
from PySide6 import QtWidgets
import maya.OpenMayaUI as omui
from shiboken6 import wrapInstance

PKGS_TO_RELOAD = [
    "TDS_radialMenu.radialWidget",   # your widget/paint code
    # add more module paths if your look is split across files
]

def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QMainWindow)

def _fresh_radial_cls():
    """Reload menu modules and return a fresh RadialMenuWidget class."""
    # reload children first (reverse depth), then parents
    for name in sorted([n for n in sys.modules if any(n.startswith(p) for p in PKGS_TO_RELOAD)], reverse=True):
        try:
            importlib.reload(sys.modules[name])
        except Exception:
            pass

    # ensure the main widget module is imported and return class
    mod = importlib.import_module("TDS_radialMenu.radialWidget")
    return mod.RadialMenuWidget

# ==== RMB HOLD CALLBACK ====
_ACTIVE_MENU = None  # kill previous ephemeral menu if detector fires again

def on_rmb_hold_show_menu(screen_pos):
    global _ACTIVE_MENU
    try:
        if _ACTIVE_MENU is not None:
            _ACTIVE_MENU.close()
            _ACTIVE_MENU = None
    except Exception:
        pass

    RadialMenuWidget = _fresh_radial_cls()   # <-- hot reload happens here
    w = RadialMenuWidget(parent=_maya_main_window())
    # position at cursor (adjust for your sizing)
    w.move(int(screen_pos.x() - w.width()/2), int(screen_pos.y() - w.height()/2))
    w.show()
    QtWidgets.QApplication.processEvents()
    _ACTIVE_MENU = w


# # Install and activate the radial menu
# from TDS_radialMenu import radialMenu_main
# radialMenu_main.launch_or_toggle_radial()
# Once installed, hold down the right mouse button to open the radial menu. Other commands:

# # Open the editor UI
# from TDS_radialMenu import TDS_buildRadialMenu_UI
# TDS_buildRadialMenu_UI.show_window()

# # Toggle radial menu on/off
# from TDS_radialMenu import radialMenu_main
# radialMenu_main.toggle_radial_menu()

# # Toggle smart preset mode
# radialMenu_main.toggle_smart_preset()

# # Uninstall the radial menu
# radialMenu_main.uninstall_radial_menu()
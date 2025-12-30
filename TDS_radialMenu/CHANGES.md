# TDS Radial Menu - PySide6 Migration for Maya 2026

## Overview
This document outlines all changes made to upgrade TDS Radial Menu from PySide2 (Maya 2024 and earlier) to PySide6 (Maya 2025/2026), including crash mitigation fixes.

## 1. Module Import Changes

### PySide2 to PySide6
All PySide2 imports updated to PySide6:

**Before:**
```python
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance, isValid
```

**After:**
```python
from PySide6 import QtWidgets, QtCore, QtGui
from shiboken6 import wrapInstance, isValid
```

**Files Changed:**
- `__init__.py` (lines 17, 19)
- `radialMenu_main.py` (line 2)
- `radialWidget.py` (lines 1, 3, 2732, 2734)
- `TDS_buildRadialMenu_UI.py` (lines 1, 2, 7)

### NOTE: Import Path Changes

Updated import paths to match folder structure in Maya scripts directory.

**Before:**
```python
from TDS_library.TDS_radialMenu import radialWidget
from TDS_library.TDS_radialMenu.radialWidget import RightClickHoldDetector
```

**After:**
```python
from TDS_radialMenu import radialWidget
from TDS_radialMenu.radialWidget import RightClickHoldDetector
```

**Reason:** Script is installed directly in `maya/scripts/TDS_radialMenu/` without parent `TDS_library` folder during tests


#### Font Scaling for 4K Monitors

Increased default text scale from 1.0 to 2.0 for better visibility on high-DPI displays.

**Files Changed:**
- `radialWidget.py` (lines 574, 1967)
- `TDS_buildRadialMenu_UI.py` (line 238)

Text scale can still be adjusted via the editor UI (range: 0.5 to 10.0).

## 4. Crash Mitigation Fixes

### Issue: Maya Exit Crashes
The original code caused crashes when exiting Maya due to improper cleanup of widgets parented to `wrapInstance` objects.

### Root Causes

1. **setParent(None) before deleteLater()**
   - Detaching widgets from wrapInstance parent during cleanup
   - Created inconsistency between Python and C++ object states

2. **destroyed signal connection**
   - Lambda connected to widget's destroyed signal
   - Signal fired during Maya shutdown when Python objects partially destroyed

3. **Event filter processing during shutdown**
   - Event filter continued processing events during Maya quit
   - Caused crashes when accessing destroyed objects

### Fixes Applied

#### 4.1 Removed setParent(None) Calls

**Before:**
```python
_ACTIVE_MENU.close()
_ACTIVE_MENU.setParent(None)
_ACTIVE_MENU.deleteLater()
```

**After:**
```python
_ACTIVE_MENU.close()
_ACTIVE_MENU = None
```

**Files Changed:**
- `__init__.py` (line 51)
- `radialWidget.py` (line 2758)

#### 4.2 Removed Unsafe deleteLater() Calls

**Before:**
```python
_simple_window_instance.close()
_simple_window_instance.deleteLater()
```

**After:**
```python
_simple_window_instance.close()
```

**Files Changed:**
- `TDS_buildRadialMenu_UI.py` (line 933)
- `radialMenu_main.py` (line 104)

**Reason:** Widgets parented to wrapInstance should be closed and references cleared. Maya handles the actual Qt object cleanup.

#### 4.3 Added scriptJob for Cleanup on Quit

Following Maya 2026 best practices, added scriptJob to ensure proper cleanup order.

**Added to radialMenu_main.py:**
```python
# Track scriptJob ID
_rmb_detector_ref = {"instance": None, "scriptJob": None}

# Register cleanup on Maya quit
_rmb_detector_ref["scriptJob"] = cmds.scriptJob(
    event=["quitApplication", uninstall_radial_menu]
)
```

**Files Changed:**
- `radialMenu_main.py` (lines 10, 85, 127-132)

**Reason:** Prevents crashes by cleaning up before Maya's C++ shutdown sequence.

#### 4.4 Removed destroyed Signal Connection

**Before:**
```python
self._radial = RadialMenuClass(get_main_window())
self._radial.destroyed.connect(lambda *_: setattr(self, "_radial", None))
self._radial.show()
```

**After:**
```python
self._radial = RadialMenuClass(get_main_window())
self._radial.show()
```

**Files Changed:**
- `radialWidget.py` (line 2785)

**Reason:** The lambda callback caused crashes when destroyed signal fired during Maya shutdown with partially destroyed Python objects.

#### 4.5 Added Shutdown Flag and Cleanup Method

Added proper shutdown handling to RightClickHoldDetector class.

**Added to radialWidget.py:**
```python
class RightClickHoldDetector(QtCore.QObject):
    def __init__(self, radial_enabled, parent=None):
        super().__init__(parent)
        self._shutting_down = False  # Prevent event processing during shutdown

    def cleanup(self):
        """Call this before Maya quits to prevent crash."""
        self._shutting_down = True
        if self._radial:
            try:
                self._radial.close()
                self._radial = None
            except:
                pass

    def eventFilter(self, obj, event):
        # Don't process events during shutdown
        if self._shutting_down or not self.radial_enabled["state"]:
            return False
        # ... rest of event handling
```

**Files Changed:**
- `radialWidget.py` (lines 2741, 2743-2751, 2755)

**Reason:** Prevents event filter from processing events during Maya shutdown, avoiding access to destroyed objects.

#### 4.6 Updated Uninstall to Call Cleanup

**Added to radialMenu_main.py:**
```python
def uninstall_radial_menu():
    if _rmb_detector_ref["instance"] is not None:
        try:
            # Call cleanup to prevent crash during shutdown
            _rmb_detector_ref["instance"].cleanup()
            app.removeEventFilter(_rmb_detector_ref["instance"])
            _rmb_detector_ref["instance"] = None
        except Exception:
            pass

    # Clean up scriptJob
    if _rmb_detector_ref["scriptJob"]:
        try:
            cmds.scriptJob(kill=_rmb_detector_ref["scriptJob"], force=True)
        except:
            pass
        _rmb_detector_ref["scriptJob"] = None
```

**Files Changed:**

## 5. Maya 2026 Best Practices Applied

Based on official Maya 2026 documentation and working examples:

1. **wrapInstance Usage:** Correct pattern maintained
   ```python
   from maya import OpenMayaUI as omui
   from shiboken6 import wrapInstance

   mw_ptr = omui.MQtUtil.mainWindow()
   mayaMainWindow = wrapInstance(int(mw_ptr), QMainWindow)
   ```

2. **Widget Parenting:** Widgets properly parented to prevent garbage collection

3. **Cleanup on Quit:** scriptJob ensures cleanup before Maya's C++ shutdown

4. **No setParent(None):** Avoided detaching from wrapInstance parent

## 6. Testing Recommendations

After migration:

1. Test radial menu activation (RMB hold)
2. Test preset switching
3. Test editor UI
4. **Test Maya exit multiple times** - should not crash
5. Test on 4K monitor - fonts should be readable
6. Test hot reload functionality

## 7. References

- Maya Qt6 Migration: https://help.autodesk.com/cloudhelp/2026/ENU/Maya-DEVHELP/files/Whats-New-Whats-Changed/2025-Whats-New-in-API/Qt6Migration.html
- Working with PySide in Maya: https://help.autodesk.com/cloudhelp/2025/ENU/Maya-DEVHELP/files/Maya-Python-API/Maya_DEVHELP_Maya_Python_API_Working_with_PySide_in_Maya_html.html
- PySide6 Documentation: https://doc.qt.io/qtforpython-6/

## 8. Summary

**Total Files Modified:** 4
- `__init__.py`
- `radialMenu_main.py`
- `radialWidget.py`
- `TDS_buildRadialMenu_UI.py`

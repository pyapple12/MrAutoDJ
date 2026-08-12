# 全局 SHIFT 修饰状态：键盘 SHIFT / 虚拟按钮均可切换，各控件查询后发第二功能信号

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class ShiftState(QObject):
    # 全局 SHIFT 修饰状态（单例由 MainWindow 持有，各控件共享）
    changed = Signal(bool)

    def __init__(self, parent=None):
        # 初始化：SHIFT 未按下
        super().__init__(parent)
        self._active = False

    def set_active(self, on: bool) -> None:
        # 设置 SHIFT 状态（变化才发信号；G3.1：changed 已接线到 SHIFT 按钮灯态）
        on = bool(on)
        if on != self._active:
            self._active = on
            self.changed.emit(on)

    def is_shift(self) -> bool:
        # 查询当前是否按住（控件判断第二功能用）
        return self._active


# ===== ui/shift_state.py 模块说明 =====
# 类型：
#   ShiftState(QObject)：全局 SHIFT 修饰状态
# 信号：
#   changed(bool)：状态变化（G3.1 起接线到 SHIFT 按钮 LED 灯态）
# 方法：
#   set_active(on)：设置状态（变化才发信号）
#   is_shift()：查询当前是否按住（G3.1 删除零调用 toggle()/active，保留单一查询接口）
# 设计理由：FLX4 的 SHIFT 是全局修饰键，所有控件共享同一状态；
#   QObject 信号驱动按钮灯态联动
# 关联配置：无

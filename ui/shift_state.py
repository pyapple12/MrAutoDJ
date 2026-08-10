# 全局 SHIFT 修饰状态：键盘 SHIFT / 虚拟按钮均可切换，各控件查询后发第二功能信号
# 参考：w.study.md B13-3.15（SHIFT 按钮语义：按住时其他按钮触发第二功能）

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
        # 设置 SHIFT 状态（变化才发信号）
        on = bool(on)
        if on != self._active:
            self._active = on
            self.changed.emit(on)

    def toggle(self) -> bool:
        # 切换并返回新状态
        self.set_active(not self._active)
        return self._active

    @property
    def active(self) -> bool:
        # 当前是否按住 SHIFT
        return self._active

    def is_shift(self) -> bool:
        # 语义别名（控件查询用）
        return self._active


# ===== ui/shift_state.py 模块说明 =====
# 类型：
#   ShiftState(QObject)：全局 SHIFT 修饰状态
# 信号：
#   changed(bool)：状态变化（按钮灯态可订阅）
# 方法：
#   set_active(on)：设置状态（变化才发信号）
#   toggle()：切换并返回新状态
#   is_shift()/active：查询当前是否按住
# 设计理由：FLX4 的 SHIFT 是全局修饰键（B13-3.15），所有控件共享同一状态；
#   用 QObject 信号便于按钮灯态联动
# 关联配置：无

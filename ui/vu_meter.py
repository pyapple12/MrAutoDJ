# VU 电平表组件：从引擎 vu_levels() 读取（100ms 定时器），条状显示
# 参考：w.study.md B13-4.5（通道电平指示）、E1.5 方案 C

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from config.static.static_config import get_static_config

# 静态配置解包（颜色）
_SC = get_static_config()
_UI_COLORS = _SC.ui.get("colors", {})


class VUMeter(QWidget):
    # 垂直 VU 条：set_level(0-1) 驱动；分段变色（绿/黄/红）
    def __init__(self, label: str = "", parent=None):
        # 初始化：标签、电平 0、固定宽度
        super().__init__(parent)
        self._label = label
        self._level = 0.0
        self.setFixedSize(18, 90)

    def set_level(self, level: float) -> None:
        # 设置电平（0-1 钳制；变化才重绘）
        level = max(0.0, min(1.0, float(level)))
        if abs(level - self._level) > 0.001:
            self._level = level
            self.update()

    def paintEvent(self, event) -> None:
        # 绘制：背景槽 + 电平条（≤60% 绿、≤80% 黄、>80% 红）
        painter = QPainter(self)
        w, h = self.width(), self.height()
        bg = QColor("#1a1a1a")
        painter.fillRect(self.rect(), bg)
        bar_h = int(self._level * (h - 2))
        if bar_h > 0:
            pct = self._level
            if pct > 0.8:
                color = QColor(str(_UI_COLORS.get("danger", "#ff4444")))
            elif pct > 0.6:
                color = QColor(str(_UI_COLORS.get("warning", "#ffcc00")))
            else:
                color = QColor(str(_UI_COLORS.get("accent", "#00ff41")))
            painter.fillRect(1, h - 1 - bar_h, w - 2, bar_h, color)
        if self._label:
            painter.setPen(QColor(str(_UI_COLORS.get("accent", "#00ff41"))))
            painter.drawText(self.rect(), Qt.AlignCenter, self._label)
        painter.end()


# ===== ui/vu_meter.py 模块说明 =====
# 类型：
#   VUMeter(QWidget)：垂直 VU 条
# 方法：
#   set_level(level)：设置电平 0-1（变化才重绘）
#   paintEvent：分段着色（≤60% 绿 / ≤80% 黄 / >80% 红）
# 设计理由：E1.5 方案 C 的 UI 端（定时器读引擎预分配数组）；
#   简单条状可视化（B13-4.5 通道电平指示）
# 关联配置：config/static/ui.json（colors.accent/warning/danger）

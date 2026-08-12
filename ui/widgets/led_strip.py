# LedStrip LED 灯柱：分段亮起（绿→黄→红分带），只读电平指示
# 接口：set_level(0..1) 触发重绘；阈值参数进 ui.json

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from config.static.static_config import get_static_config

# 静态配置解包（LED 配色与分带阈值）
_SC = get_static_config()
_UI = _SC.ui
_PANEL_INSET = QColor(_UI.get("panel_inset", "#101215"))
_GREEN = QColor(_UI.get("glow_green", "#2fe37a"))
_YELLOW = QColor(_UI.get("warning", "#ffcc00"))
_RED = QColor(_UI.get("danger", "#ff4444"))
_GREEN_TH = float(_UI.get("led_green_threshold", 0.6))  # 0-60% 绿
_YELLOW_TH = float(_UI.get("led_yellow_threshold", 0.85))  # 60-85% 黄，以上红
_SEGMENTS = 12  # 默认分段数


class LedStrip(QWidget):
    # LED 灯柱：set_level 设置 0..1，亮起段数 = level×SEGMENTS，颜色按阈值分带
    def __init__(
        self,
        segments: int = _SEGMENTS,
        orientation: Qt.Orientation = Qt.Vertical,
        parent=None,
    ):
        # 初始化：分段数/方向；垂直 14 宽、水平 14 高
        super().__init__(parent)
        self._segments = max(4, int(segments))
        self._orientation = orientation
        self._level = 0.0
        if orientation == Qt.Vertical:
            self.setFixedSize(14, 90)
        else:
            self.setFixedSize(90, 14)

    def set_level(self, level: float) -> None:
        # 设置电平（0..1 钳制，变化才重绘）
        level = max(0.0, min(1.0, float(level)))
        if abs(level - self._level) < 1e-6:
            return
        self._level = level
        self.update()

    def _segment_color(self, i: int, lit_total: int) -> QColor:
        # 段颜色：按亮起位置分带（绿→黄→红）；未亮 = inset
        if i >= lit_total:
            return QColor(_PANEL_INSET)
        ratio = (i + 1) / self._segments
        if ratio <= _GREEN_TH:
            return QColor(_GREEN)
        if ratio <= _YELLOW_TH:
            return QColor(_YELLOW)
        return QColor(_RED)

    def paintEvent(self, event) -> None:
        # 绘制灯柱：从底部（垂直）起亮，段间留缝
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        vertical = self._orientation == Qt.Vertical
        lit = int(round(self._level * self._segments))
        w, h = self.width(), self.height()
        gap = 2.0
        if vertical:
            seg_h = (h - gap * (self._segments - 1)) / self._segments
            for i in range(self._segments):
                y = h - gap - (i + 1) * seg_h - i * gap
                p.setBrush(self._segment_color(self._segments - 1 - i, lit))
                p.setPen(Qt.NoPen)
                p.drawRoundedRect(QRectF(1.0, y, w - 2.0, seg_h - 1), 1, 1)
        else:
            seg_w = (w - gap * (self._segments - 1)) / self._segments
            for i in range(self._segments):
                x = gap + i * (seg_w + gap)
                p.setBrush(self._segment_color(i, lit))
                p.setPen(Qt.NoPen)
                p.drawRoundedRect(QRectF(x, 1.0, seg_w - 1, h - 2.0), 1, 1)
        p.end()


# ===== ui/widgets/led_strip.py 模块说明 =====
# 类：LedStrip(QWidget)——LED 电平灯柱（VU 表替换/拍数指示）
#   set_level(0..1)：亮起段数 = level×segments；_segment_color 按位置分带
#   绘制：垂直从底部起亮（水平从左），段间留缝模拟 LED 颗粒
# 设计理由：分段灯柱比连续渐变更像硬件 VU（M1.6 规格单）；
#   分带阈值/段数参数化（ui.json led_green_threshold/led_yellow_threshold）
# 关联配置：config/static/ui.json（glow_green/warning/danger/panel_inset）

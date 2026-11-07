# LedStrip LED 灯柱：分段亮起（绿→黄→红分带），只读电平指示
# 接口：set_level(0..1) 触发重绘；阈值参数进 ui.json

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from config.static.static_config import get_static_config
from ui import palette
from ui.palette import ThemeAware
from ui.scale import s

# 静态配置解包（LED 阈值/段数；配色改 paint 时经 palette 现取，J2 批次 2）
_UI = get_static_config().ui
_GREEN_TH = float(_UI.get("led_green_threshold", 0.6))  # 0-60% 绿
_YELLOW_TH = float(_UI.get("led_yellow_threshold", 0.85))  # 60-85% 黄，以上红
_SEGMENTS = int(_UI.get("led_segments", 12))  # 默认分段数（I2.3：进配置）


class LedStrip(ThemeAware, QWidget):
    # LED 灯柱：set_level 设置 0..1，亮起段数 = level×SEGMENTS，颜色按阈值分带
    def __init__(
        self,
        segments: int = _SEGMENTS,
        orientation: Qt.Orientation = Qt.Vertical,
        parent=None,
    ):
        # 初始化：分段数/方向；垂直 14 宽、水平 14 高；主题感知（J2）
        super().__init__(parent)
        self._segments = max(4, int(segments))
        self._orientation = orientation
        self._level = 0.0
        # J4：宽/高基准 × ui_scale
        if orientation == Qt.Vertical:
            self.setFixedSize(s(14), s(90))
        else:
            self.setFixedSize(s(90), s(14))
        self.bind_theme()  # J2

    def set_level(self, level: float) -> None:
        # 设置电平（0..1 钳制，变化才重绘）
        level = max(0.0, min(1.0, float(level)))
        if abs(level - self._level) < 1e-6:
            return
        self._level = level
        self.update()

    def _segment_color(self, i: int, lit_total: int) -> QColor:
        # 段颜色：按亮起位置分带（绿→黄→红）；未亮 = panel_edge（PL001.8：
        # 空态保留框架——暗面板上灯柱轮廓可见，原 panel_inset 几乎不可见）
        if i >= lit_total:
            return palette.color("panel_edge", "#26292f")
        ratio = (i + 1) / self._segments
        if ratio <= _GREEN_TH:
            return palette.color("glow_green", "#2fe37a")
        if ratio <= _YELLOW_TH:
            return palette.color("warning", "#ffcc00")
        return palette.color("danger", "#ff4444")

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
                # FIX004.13：i=0 即底部段（y 公式决定），色带按 i 正序（底部绿/
                # 顶部红、低电平底部先亮——原 -1-i 翻转致方向/色带整体镜像）
                color = self._segment_color(i, lit)
                p.setBrush(color)
                p.setPen(Qt.NoPen)
                p.drawRoundedRect(QRectF(1.0, y, w - 2.0, seg_h - 1), 1, 1)
                # PL001.8：未亮段顶部 1px 6% 白描边（框架可见）
                if i >= lit:
                    p.setPen(QPen(QColor(255, 255, 255, 15), 1))
                    p.drawLine(QPointF(2.0, y + 1.0), QPointF(w - 2.0, y + 1.0))
        else:
            seg_w = (w - gap * (self._segments - 1)) / self._segments
            for i in range(self._segments):
                x = gap + i * (seg_w + gap)
                color = self._segment_color(i, lit)
                p.setBrush(color)
                p.setPen(Qt.NoPen)
                p.drawRoundedRect(QRectF(x, 1.0, seg_w - 1, h - 2.0), 1, 1)
                # PL001.8：未亮段左缘 1px 6% 白描边（框架可见）
                if i >= lit:
                    p.setPen(QPen(QColor(255, 255, 255, 15), 1))
                    p.drawLine(QPointF(x + 1.0, 2.0), QPointF(x + 1.0, h - 2.0))
        p.end()


# ===== ui/widgets/led_strip.py 模块说明 =====
# 类：LedStrip(QWidget)——LED 电平灯柱（VU 表替换/拍数指示）
#   set_level(0..1)：亮起段数 = level×segments；_segment_color 按位置分带
#     （未亮段 = panel_edge + 顶部 1px 6% 白描边——PL001.8 空态保留框架，
#     暗面板上灯柱轮廓可见）
#   绘制：垂直从底部起亮（水平从左），段间留缝模拟 LED 颗粒
# 设计理由：分段灯柱比连续渐变更像硬件 VU（M1.6 规格单）；
#   分带阈值/段数参数化（ui.json led_green_threshold/led_yellow_threshold/led_segments）
# 关联配置：config/static/ui.json（colors.warning/colors.danger 为 colors 子对象键，
#   I2.1 修正读取层级；glow_green/panel_inset 顶层键；led_segments 段数）

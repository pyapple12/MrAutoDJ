# RotaryKnob 旋钮：静态层（凹槽/刻度环/外圈）QPixmap 缓存 + 动态层指针旋转
# 交互：垂直拖拽、滚轮步进、双击复位；valueChanged(float) 信号

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QWidget

from config.static.static_config import get_static_config
from ui.widgets._skins import metal_gradient, top_highlight_pen

# 静态配置解包（旋钮配色）
_SC = get_static_config()
_UI = _SC.ui
_PANEL_EDGE = QColor(_UI.get("panel_edge", "#26292f"))
_PANEL_INSET = QColor(_UI.get("panel_inset", "#101215"))
_SILK = QColor(_UI.get("silk_text", "#8a9099"))
_GLOW_WHITE = QColor(_UI.get("glow_white", "#e8ecf0"))
_ANGLE_RANGE = 270.0  # 行程 270°（DJ 旋钮惯例）
_DRAG_SENS = 80.0  # 拖拽像素 → 全程（值域全程对应 80px）
WHEEL_STEP_DIVISIONS = int(
    _UI.get("wheel_step_divisions", 20)
)  # 滚轮全程等分数（G1.3）


class RotaryKnob(QWidget):
    # 旋钮：值域 [min,max]，指针角度线性映射；静态层缓存，动态层只画指针
    valueChanged = Signal(float)

    def __init__(
        self,
        min_value: float = 0.0,
        max_value: float = 1.0,
        default: float = 0.5,
        size: int = 28,
        parent=None,
    ):
        # 初始化：值域/默认值/固定尺寸；拖拽锚点
        super().__init__(parent)
        self._min = min_value
        self._max = max_value
        self._default = default
        self._value = default
        self._drag_y0 = 0.0
        self._drag_v0 = self._value
        self._pixmap: QPixmap | None = None
        self._cached_size = None
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)

    def value(self) -> float:
        # 当前值
        return self._value

    def set_value(self, v: float) -> None:
        # 设置值（钳制值域，变化才发信号与重绘）
        v = max(self._min, min(self._max, float(v)))
        if abs(v - self._value) < 1e-9:
            return
        self._value = v
        self.update()
        self.valueChanged.emit(v)

    def _angle(self) -> float:
        # 指针角度：min=-135°（左下）→ max=+135°（右下）；H0.5 分母防 min==max 除零
        span = max(self._max - self._min, 1e-9)
        ratio = (self._value - self._min) / span
        return -_ANGLE_RANGE / 2.0 + _ANGLE_RANGE * ratio

    # --- 交互 ---

    def mousePressEvent(self, event) -> None:
        # 按下：记录拖拽起点（值不跳变）
        self._drag_y0 = event.position().y()
        self._drag_v0 = self._value
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        # 垂直拖拽：上移增值（DJ 旋钮直觉：上=增）
        dy = self._drag_y0 - event.position().y()
        self.set_value(self._drag_v0 + dy * (self._max - self._min) / _DRAG_SENS)
        event.accept()

    def wheelEvent(self, event) -> None:
        # 滚轮步进：全程 /divisions（下滚=减；G1.3：配置驱动）
        step = (self._max - self._min) / WHEEL_STEP_DIVISIONS
        delta = step if event.angleDelta().y() > 0 else -step
        self.set_value(self._value + delta)
        event.accept()

    def mouseDoubleClickEvent(self, event) -> None:
        # 双击复位到默认值
        self.set_value(self._default)
        event.accept()

    # --- 绘制 ---

    def paintEvent(self, event) -> None:
        # 静态层 blit + 动态指针线（按当前角度）
        if self._pixmap is None or self._cached_size != self.size():
            self._render_cache()
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        s = self.width()
        cx, cy = s / 2.0, s / 2.0
        ang = math.radians(self._angle())
        r = s * 0.32
        # G0.4：指针直接画"圆心→端点"（原实现用 QRectF 当点取 center 致线段错位）
        painter.setPen(QPen(_GLOW_WHITE, 2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(
            QPointF(cx, cy),
            QPointF(cx + r * math.cos(ang), cy + r * math.sin(ang)),
        )

    def _render_cache(self) -> None:
        # 静态层：银色刻度环（15° 刻度线，顶部 30° 高亮）+ 金属外圈 + 旋帽
        s = self.width()
        pm = QPixmap(s, s)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        cx = cy = s / 2.0
        # 银色刻度环：细圆环 + 15° 刻度短线
        ring_r = s * 0.42
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(165, 170, 178, 130), 1))
        p.drawEllipse(QRectF(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2))
        for deg in range(0, 360, 15):
            a = math.radians(deg)
            lit = -15 <= deg < 15  # 顶部 30° 亮刻度
            color = QColor(240, 244, 248, 235) if lit else QColor(165, 170, 178, 120)
            p.setPen(QPen(color, 1.5 if lit else 1.0))
            r0 = ring_r - 3.0
            r1 = ring_r + 3.0
            p.drawLine(
                cx + r0 * math.cos(a),
                cy + r0 * math.sin(a),
                cx + r1 * math.cos(a),
                cy + r1 * math.sin(a),
            )
        # 外圈金属环（G1.2：公共皮肤渐变）
        ring2_r = s * 0.34
        ring2 = QRectF(cx - ring2_r, cy - ring2_r, ring2_r * 2, ring2_r * 2)
        p.setBrush(metal_gradient(0, 0, 0, s))
        p.setPen(Qt.NoPen)
        p.drawEllipse(ring2)
        # 中心旋帽（内凹座 + 顶部高光弧）
        cap_r = s * 0.26
        cap = QRectF(cx - cap_r, cy - cap_r, cap_r * 2, cap_r * 2)
        cap_grad = QLinearGradient(0, 0, 0, s)
        cap_grad.setColorAt(0.0, QColor(66, 70, 76, 255))
        cap_grad.setColorAt(1.0, QColor(28, 30, 34, 255))
        p.setBrush(cap_grad)
        p.setPen(QPen(QColor(0, 0, 0, 140), 1))
        p.drawEllipse(cap)
        p.setPen(top_highlight_pen(60))  # H3.3：公共皮肤高光
        p.drawArc(cap.adjusted(2, 2, -2, -2), 200 * 16, 140 * 16)
        p.end()
        self._pixmap = pm
        self._cached_size = self.size()


# ===== ui/widgets/rotary_knob.py 模块说明 =====
# 类：RotaryKnob(QWidget)——拟物旋钮
#   value()/set_value(v)：值域钳制 + valueChanged 信号（变化才发）
#   交互：垂直拖拽（上=增，_DRAG_SENS=80px 全程）、滚轮（全程/20）、双击复位默认
#   绘制：静态层（刻度环/金属环/旋帽）QPixmap 缓存 + 动态指针线（270° 行程）
# 设计理由：DJ 旋钮 270° 行程 + 垂直拖拽比圆环拖拽好操作（M1.6 规格单）；
#   静态层缓存保证重绘开销低
# 关联配置：config/static/ui.json（panel_edge/panel_inset/silk_text/glow_white）

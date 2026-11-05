# FaderSlider 推子：内凹槽 + 两端刻度 + 中央线 + 金属帽（垂直/水平）
# 交互：拖拽（点击跳转）、滚轮步进、双击回中；valueChanged(float) 信号

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from config.static.static_config import get_static_config
from ui import palette
from ui.palette import ThemeAware
from ui.scale import s
from ui.widgets._skins import metal_gradient, metal_pen, top_highlight_pen

# 静态配置解包（滚轮步进；配色改 paint 时经 palette 现取，J2 批次 2）
_UI = get_static_config().ui
WHEEL_STEP_DIVISIONS = int(
    _UI.get("wheel_step_divisions", 20)
)  # 滚轮全程等分数（G1.3）


class FaderSlider(ThemeAware, QWidget):
    # 推子：值域 [min,max]，帽位置线性映射；垂直或水平
    valueChanged = Signal(float)

    def __init__(
        self,
        min_value: float = 0.0,
        max_value: float = 1.0,
        default: float = 0.5,
        orientation: Qt.Orientation = Qt.Vertical,
        length: int = 120,
        parent=None,
    ):
        # 初始化：值域/方向/固定长度；垂直宽 24、水平高 24；主题感知（J2）
        super().__init__(parent)
        self._min = min_value
        self._max = max_value
        self._default = default
        self._value = default
        self._orientation = orientation
        # J4：宽/长基准 × ui_scale
        if orientation == Qt.Vertical:
            self.setFixedSize(s(24), s(length))
        else:
            self.setFixedSize(s(length), s(24))
        self.setCursor(Qt.PointingHandCursor)
        self.bind_theme()  # J2

    def value(self) -> float:
        # 当前值
        return self._value

    def set_value(self, v: float) -> None:
        # 设置值（钳制，变化才发信号与重绘）
        v = max(self._min, min(self._max, float(v)))
        if abs(v - self._value) < 1e-9:
            return
        self._value = v
        self.update()
        self.valueChanged.emit(v)

    # --- 几何换算 ---

    def _ratio(self) -> float:
        # 值 → 0..1 行程比例（H0.5 分母防 min==max 除零）
        span = max(self._max - self._min, 1e-9)
        return (self._value - self._min) / span

    def _set_from_pos(self, pos) -> None:
        # 位置 → 值（垂直：y 从底部起算；水平：x 从左起算）
        if self._orientation == Qt.Vertical:
            h = max(self.height() - 14.0, 1.0)
            r = 1.0 - (pos.y() - 7.0) / h
        else:
            w = max(self.width() - 14.0, 1.0)
            r = (pos.x() - 7.0) / w
        self.set_value(self._min + max(0.0, min(1.0, r)) * (self._max - self._min))

    # --- 交互 ---

    def mousePressEvent(self, event) -> None:
        # 按下：跳到点击位置（推子直跳语义）
        self._set_from_pos(event.position())
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        # 拖动：跟随位置
        self._set_from_pos(event.position())
        event.accept()

    def wheelEvent(self, event) -> None:
        # 滚轮步进：全程 /divisions（G1.3：配置驱动）
        step = (self._max - self._min) / WHEEL_STEP_DIVISIONS
        self.set_value(self._value + (step if event.angleDelta().y() > 0 else -step))
        event.accept()

    def mouseDoubleClickEvent(self, event) -> None:
        # 双击回中（(min+max)/2）
        self.set_value((self._min + self._max) / 2.0)
        event.accept()

    # --- 绘制 ---

    def paintEvent(self, event) -> None:
        # 静态槽/刻度 + 动态金属帽（位置 = 值映射）；禁用态 35% 透明度（J0.4 灰显）
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            p.setOpacity(0.35)
        vertical = self._orientation == Qt.Vertical
        w, h = self.width(), self.height()
        # 凹槽（内阴影感：inset 底 + 上下深线）
        if vertical:
            groove = QRectF(w / 2.0 - 3.0, 4.0, 6.0, h - 8.0)
        else:
            groove = QRectF(4.0, h / 2.0 - 3.0, w - 8.0, 6.0)
        p.setPen(QPen(QColor(0, 0, 0, 120), 1))
        p.setBrush(palette.color("panel_inset", "#101215"))
        p.drawRoundedRect(groove, 3, 3)
        # 中央线（刻度中点）
        p.setPen(QPen(palette.color("silk_text", "#8a9099"), 1))
        if vertical:
            p.drawLine(
                int(w / 2.0),
                int(groove.top() + groove.height() * 0.5),
                int(w / 2.0),
                int(groove.top() + groove.height() * 0.5) + 4,
            )
        else:
            p.drawLine(
                int(groove.left() + groove.width() * 0.5),
                int(h / 2.0),
                int(groove.left() + groove.width() * 0.5) + 4,
                int(h / 2.0),
            )
        # 金属帽（G1.2：公共皮肤渐变 + 描边 + 顶部高光棱）
        r = self._ratio()
        if vertical:
            cap = QRectF(3.0, 2.0 + (h - 16.0) * (1.0 - r), 18.0, 12.0)
        else:
            cap = QRectF(2.0 + (w - 16.0) * r, 3.0, 12.0, 18.0)
        p.setBrush(metal_gradient(0, cap.top(), 0, cap.bottom()))
        p.setPen(metal_pen())
        p.drawRoundedRect(cap, 3, 3)
        # 帽顶高光线
        p.setPen(top_highlight_pen())
        if vertical:
            p.drawLine(
                int(cap.left() + 2),
                int(cap.top() + 1),
                int(cap.right() - 2),
                int(cap.top() + 1),
            )
        else:
            p.drawLine(
                int(cap.left() + 1),
                int(cap.top() + 2),
                int(cap.left() + 1),
                int(cap.bottom() - 2),
            )
        p.end()


# ===== ui/widgets/fader_slider.py 模块说明 =====
# 类：FaderSlider(QWidget)——拟物推子（垂直/水平）
#   value()/set_value(v)：值域钳制 + valueChanged；_ratio/_set_from_pos 几何换算
#   交互：按下直跳、拖动跟随、滚轮全程/20、双击回中
#   绘制：内凹槽 + 中央刻度线 + 金属帽（渐变 + 高光棱），帽位置随值
# 设计理由：推子"直跳"语义（DJ 台推子点哪到哪，区别于平滑滑杆）；
#   金属帽渐变模拟拉丝质感（M1.6 规格单）
# 关联配置：config/static/ui.json（panel_inset/panel_edge/silk_text）

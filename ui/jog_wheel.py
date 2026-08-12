# Jog 转盘控件：外圈滚轮=弯音、顶面按住拖动=搓碟、SHIFT+滚=高速搜索、Vinyl 开关
# 参考：w.study.md B13-3.16（Jog 交互）、决策记录（双交互结合）

from __future__ import annotations

from PySide6.QtCore import QElapsedTimer, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QWidget

from config.static.static_config import get_static_config

# 静态配置解包（转盘颜色 + 弯音/搜索/搓碟灵敏度，参数一律走 ui.json）
_SC = get_static_config()
_UI_COLORS = _SC.ui.get("colors", {})

# 滚轮/拖动灵敏度（样本数 / 单位；出厂值即合理默认，可在 ui.json 调整）
WHEEL_BEND_STEP = float(_SC.ui.get("jog_bend_step", 0.05))  # 每格弯音速率（累积）
SEARCH_WHEEL_STEP = 4.0  # SHIFT+格 高速搜索速率
SCRATCH_GAIN_BASE = float(_SC.ui.get("jog_scratch_gain", 256))  # 搓碟基础每像素样本
SCRATCH_SPEED_REF = float(_SC.ui.get("jog_scratch_speed_ref", 800))  # px/s 参考速度


class JogWheel(QWidget):
    # Jog 转盘：paintEvent 绘制圆盘；wheelEvent 弯音/搜索；鼠标拖动搓碟
    bend_changed = Signal(float)  # 弯音速率（±0.5）
    search_changed = Signal(float)  # 高速搜索速率（±16）
    scratch_moved = Signal(int)  # 搓碟位移（样本，累加语义）
    touch_changed = Signal(bool)  # 触摸态
    vinyl_toggled = Signal(bool)

    def __init__(self, parent=None):
        # 初始化：尺寸、Vinyl 开关、触摸态、SHIFT 状态引用（MainWindow 注入）
        super().__init__(parent)
        self.setFixedSize(140, 140)
        self._vinyl = True
        self._touched = False
        self._last_pos: QPointF | None = None
        self._scratch_timer = QElapsedTimer()  # 搓碟速度测量（P3 增益标定）
        self._playing = False  # 播放状态（顶部指示点，F6.3）
        self._info_text = ""  # 中心屏文本（BPM/位置，F6.3）
        self.shift: object | None = None  # ShiftState 实例（MainWindow 注入）

        row = QVBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        self._vinyl_cb = QCheckBox("Vinyl")
        self._vinyl_cb.setChecked(True)
        self._vinyl_cb.toggled.connect(self._on_vinyl)
        row.addWidget(self._vinyl_cb, alignment=Qt.AlignCenter)

    def set_shift_state(self, shift) -> None:
        # 注入全局 SHIFT 状态（MainWindow 调用）
        self.shift = shift

    @property
    def vinyl(self) -> bool:
        # Vinyl 模式（顶面=搓碟）
        return self._vinyl

    # --- 事件 ---

    def wheelEvent(self, event) -> None:
        # 滚轮：外圈弯音（Vinyl 关或未触摸）；SHIFT+滚=高速搜索
        delta = event.angleDelta().y()
        if delta == 0:
            return
        steps = 1 if delta > 0 else -1
        if self.shift is not None and self.shift.is_shift():
            self.search_changed.emit(steps * SEARCH_WHEEL_STEP)
        else:
            self.bend_changed.emit(steps * WHEEL_BEND_STEP)
        event.accept()

    def mousePressEvent(self, event) -> None:
        # 顶面按下=触摸开始（Vinyl 开时进入搓碟）
        self._touched = True
        self._last_pos = event.position()
        self._scratch_timer.restart()
        self.touch_changed.emit(True)
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        # 拖动=搓碟位移（相对上次位置，x 方向映射样本；增益按速度标定）
        if self._touched and self._last_pos is not None:
            dx = event.position().x() - self._last_pos.x()
            self._last_pos = event.position()
            dt = (
                self._scratch_timer.restart() / 1000.0
                if self._scratch_timer.isValid()
                else 0.016
            )
            self.scratch_moved.emit(int(dx * self._scratch_gain(dx, dt)))
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        # 松开=触摸结束
        self._touched = False
        self._last_pos = None
        self.touch_changed.emit(False)
        event.accept()

    # --- Vinyl 开关 ---

    def _on_vinyl(self, on: bool) -> None:
        # Vinyl 模式切换（顶面=搓碟 vs 弯音）
        self._vinyl = on
        self.vinyl_toggled.emit(on)

    def _scratch_gain(self, dx: float, dt: float) -> float:
        # 搓碟增益速度映射（P3 标定）：慢速细腻（≥0.5x）、快速大幅（≤3x）；
        # gain = base × clamp(speed/ref, 0.5, 3.0)；dt 单位秒
        speed = abs(dx) / max(dt, 1e-3)
        return SCRATCH_GAIN_BASE * float(max(0.5, min(3.0, speed / SCRATCH_SPEED_REF)))

    # --- 绘制 ---

    def set_playing(self, playing: bool) -> None:
        # 播放状态（顶部旋转指示点 + 中心文本高亮，MainWindow _tick 驱动）
        if playing != self._playing:
            self._playing = playing
            self.update()

    def set_info(self, text: str) -> None:
        # 中心屏文本（BPM/位置，MainWindow _tick 驱动）
        if text != self._info_text:
            self._info_text = text
            self.update()

    def paintEvent(self, event) -> None:
        # 绘制圆盘：金属外圈（弯音区）+ 顶面（搓碟区）+ 中心屏文本 + 播放指示点
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        center = QPointF(w / 2, h / 2)
        r_out = min(w, h) / 2 - 2
        r_in = r_out * 0.66
        bg = QColor(str(_UI_COLORS.get("background", "#0d0d0d")))
        ring = QColor(str(_UI_COLORS.get("accent", "#00ff41")))
        # 外圈金属渐变环（F6.3）
        metal = QLinearGradient(0, 0, w, h)
        metal.setColorAt(0.0, QColor(210, 214, 220))
        metal.setColorAt(0.5, QColor(150, 154, 160))
        metal.setColorAt(1.0, QColor(110, 114, 120))
        painter.fillRect(self.rect(), bg)
        painter.setBrush(metal)
        painter.setPen(QPen(QColor(60, 64, 70), 2))
        painter.drawEllipse(center, r_out, r_out)  # 金属外圈
        # 顶面（搓碟区）：深灰内盘 + 细分圆
        painter.setBrush(QColor("#1a1a1a"))
        painter.setPen(QPen(ring, 2))
        painter.drawEllipse(center, r_in, r_in)
        painter.setPen(QPen(QColor(90, 94, 100), 1))
        painter.drawEllipse(center, r_in * 0.86, r_in * 0.86)
        # 播放指示点（顶部，播放时亮橙色）
        if self._playing:
            painter.setBrush(QColor("#ff7a2f"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(w / 2, h / 2 - r_in * 0.72), 3, 3)
        # 中心屏文本（BPM/位置）
        painter.setPen(QColor("#e8ecf0"))
        font = painter.font()
        font.setBold(True)
        font.setPointSizeF(9)
        painter.setFont(font)
        painter.drawText(
            QRectF(w / 2 - r_in * 0.7, h / 2 - 12, r_in * 1.4, 16),
            Qt.AlignCenter,
            self._info_text or "JOG",
        )
        painter.setPen(QColor("#8a9099"))
        painter.drawText(
            QRectF(w / 2 - r_in * 0.7, h / 2 + 4, r_in * 1.4, 12),
            Qt.AlignCenter,
            "VINYL" if self._vinyl else "CDJ",
        )
        painter.end()


# ===== ui/jog_wheel.py 模块说明 =====
# 模块级常量：
#   WHEEL_BEND_STEP=0.02 / SEARCH_WHEEL_STEP=4.0 / SCRATCH_GAIN=256：
#     滚轮与拖动的灵敏度标定
# 类型：
#   JogWheel(QWidget)：转盘控件
# 信号：
#   bend_changed(float)：滚轮弯音（每格 ±0.02，释放时 MainWindow 归零）
#   search_changed(float)：SHIFT+滚轮高速搜索（每格 ±4）
#   scratch_moved(int)：拖动搓碟（x 位移 ×256 样本）
#   touch_changed(bool)：触摸态
#   vinyl_toggled(bool)：Vinyl 模式开关
# 方法：
#   set_shift_state(shift)：注入全局 SHIFT（E2.1）
#   wheelEvent/mousePressEvent/mouseMoveEvent/mouseReleaseEvent：事件分发
# 设计理由：FLX4 交互（外圈滚轮=弯音、顶面按住拖动=搓碟，B13-3.16）；
#   组件零引擎依赖（信号解耦）；paintEvent 圆盘可视化
# 关联配置：config/static/ui.json（colors）

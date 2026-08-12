# GlowButton 背光按钮：内凹座 + 按下/激活辉光 + LED 灯态 + 模式色
# 交互：pressed/released/clicked 信号（继承 QAbstractButton）

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import QAbstractButton

from config.static.static_config import get_static_config

# 静态配置解包（按钮配色）
_SC = get_static_config()
_UI = _SC.ui
_PANEL_INSET = QColor(_UI.get("panel_inset", "#101215"))
_PANEL_EDGE = QColor(_UI.get("panel_edge", "#26292f"))
_SILK = QColor(_UI.get("silk_text", "#8a9099"))
_GLOW_WHITE = QColor(_UI.get("glow_white", "#e8ecf0"))
_GLOW_ORANGE = QColor(_UI.get("glow_orange", "#ff7a2f"))
_RADIUS = 4  # 按钮圆角


class GlowButton(QAbstractButton):
    # 背光按钮：常态内凹座；按下/checked/LED 亮时画径向辉光（led 色扩散）+ 亮色文字
    def __init__(self, text: str = "", parent=None):
        # 初始化：文本、LED 灯态与颜色、固定圆角
        super().__init__(parent)
        self.setText(text)
        self._led_on = False
        self._led_color = QColor(_GLOW_WHITE)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(28, 24)

    def set_led(self, on: bool, color: QColor | str | None = None) -> None:
        # 设置 LED 灯态（on + 可选颜色；空=保持当前色）
        if color is not None:
            self._led_color = QColor(color)
        self._led_on = bool(on)
        self.update()

    def led_on(self) -> bool:
        # LED 灯态查询（Pad/模式键灯阵用）
        return self._led_on

    def paintEvent(self, event) -> None:
        # 按状态绘制：底座（常态/悬停）或辉光（按下/checked/led_on）+ 文字
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        rect = QRectF(1.5, 1.5, w - 3.0, h - 3.0)
        path = QPainterPath()
        path.addRoundedRect(rect, _RADIUS, _RADIUS)
        active = self.isDown() or self.isChecked() or self._led_on
        if active:
            # 辉光：径向渐变（led 色中心亮 → 透明扩散，半径超过按钮范围
            # 让光晕溢出按钮，模拟硬件背光）
            grad = QRadialGradient(rect.center(), max(w, h) * 1.5)
            glow = self._led_color
            grad.setColorAt(0.0, QColor(glow.red(), glow.green(), glow.blue(), 220))
            grad.setColorAt(0.35, QColor(glow.red(), glow.green(), glow.blue(), 110))
            grad.setColorAt(1.0, QColor(glow.red(), glow.green(), glow.blue(), 0))
            p.fillPath(path, grad)
            # 底色提亮（辉光叠在亮底上更透）
            p.fillPath(path, QColor(glow.red(), glow.green(), glow.blue(), 60))
            p.setPen(QPen(QColor(glow.red(), glow.green(), glow.blue(), 220), 1))
            p.drawPath(path)
            text_color = _GLOW_WHITE  # H3.3：统一 token（原纯白与 glow_white 不一致）
        else:
            # 常态：内凹座（inset 底 + 底缘深线模拟凹入）
            p.fillPath(path, _PANEL_INSET)
            p.setPen(QPen(QColor(0, 0, 0, 100), 1))
            p.drawPath(path)
            text_color = _SILK
        # 文字居中（H3.5：超宽文本省略号，防溢出圆角）
        p.setPen(text_color)
        elided = p.fontMetrics().elidedText(
            self.text(), Qt.ElideRight, int(rect.width() - 6)
        )
        p.drawText(rect, Qt.AlignCenter, elided)
        p.end()


# ===== ui/widgets/glow_button.py 模块说明 =====
# 类：GlowButton(QAbstractButton)——拟物背光按钮
#   set_led(on, color)：LED 灯态 + 模式色（Pad 五模式/PLAY/CUE 等）；led_on() 查询
#   绘制：常态内凹座 + silk 文字；按下/checked/led_on 时径向辉光（led 色扩散）+ 白字
# 设计理由：LED 灯态独立于 checked（业务灯态与交互态分离，E2.7 灯阵复用）；
#   辉光用径向渐变模拟发光（无需贴图，主题化友好）
# 关联配置：config/static/ui.json（panel_inset/silk_text/glow_white/glow_orange）

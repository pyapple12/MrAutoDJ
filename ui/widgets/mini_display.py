# MiniDisplay 小屏：黑底圆角 + 荧光绿等宽文字 + 微弱辉光（7 段数字感）
# 接口：set_text(str) 只读显示；用于 BPM/拍数/曲名

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget

from ui import palette
from ui.palette import ThemeAware
from ui.scale import s

# 小屏配色（J2 起改 paint 时经 palette 现取 accent；屏底色固定黑不随主题）
_SCREEN_BG = QColor(10, 12, 12)
_RADIUS = 4


class MiniDisplay(ThemeAware, QWidget):
    # 迷你屏幕：黑底 + 荧光绿等宽文字（双层绘制模拟辉光），只读
    def __init__(self, parent=None):
        # 初始化：文字、等宽字体；主题感知（J2）
        super().__init__(parent)
        self._text = ""
        font = QFont("Consolas")
        font.setBold(True)
        self.setFont(font)
        self.setMinimumSize(s(48), s(20))  # J4：基准 × ui_scale
        self.bind_theme()  # J2

    def set_text(self, text: str) -> None:
        # 设置显示文本（变化才重绘）
        if text != self._text:
            self._text = text
            self.update()

    def text(self) -> str:
        # 当前显示文本
        return self._text

    def paintEvent(self, event) -> None:
        # 黑底圆角屏 + 绿字（先半透明宽笔描边模拟辉光，再实色正文）
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        rect = QRectF(1.0, 1.0, w - 2.0, h - 2.0)
        path = QPainterPath()
        path.addRoundedRect(rect, _RADIUS, _RADIUS)
        p.fillPath(path, _SCREEN_BG)
        if self._text:
            # H3.5：超宽文本省略号（防溢出屏体）
            # I3.5：先 setFont 再度量（原用默认字体度量、粗体绘制，宽度不一致
            # 导致 elide 判定与实际渲染错位）
            font_bold = QFont(self.font())
            font_bold.setPointSizeF(max(8.0, h * 0.55))
            p.setFont(font_bold)
            elided = p.fontMetrics().elidedText(self._text, Qt.ElideRight, int(w - 8))
            # 辉光层：半透明粗描边
            green = palette.color("accent", "#00ff41")
            p.setPen(QColor(green.red(), green.green(), green.blue(), 90))
            p.drawText(rect.adjusted(1, 0, -1, 0), Qt.AlignCenter, elided)
            # 正文层：实色
            p.setPen(green)
            p.drawText(rect.adjusted(1, 0, -1, 0), Qt.AlignCenter, elided)
        p.end()


# ===== ui/widgets/mini_display.py 模块说明 =====
# 类：MiniDisplay(QWidget)——迷你显示屏（BPM/拍数/曲名）
#   set_text(str)/text()：显示文本；双层绘制（半透明描边 = 辉光，实色 = 正文）
# 设计理由：荧光绿等宽文字模拟 7 段数码管观感（M1.6 规格单）；
#   屏底色固定黑（硬件屏幕本色），辉光用半透明描边零成本模拟
# 关联配置：config/static/ui.json（colors.accent 荧光绿，colors 子对象键，
#   I2.1 修正读取层级）

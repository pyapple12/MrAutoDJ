# GlowButton 背光按钮：内凹座 + 按下/激活辉光 + LED 灯态 + 模式色
# 交互：pressed/released/clicked 信号（继承 QAbstractButton）

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import QAbstractButton

from config.static.static_config import get_static_config
from ui import palette
from ui.palette import ThemeAware
from ui.scale import s

# 静态配置解包（按钮最小尺寸基准；配色改 paint 时经 palette 现取，J2 批次 2）
_UI = get_static_config().ui
_RADIUS = 4  # 按钮圆角（基准，J4 缩放随paint不涉及）


class GlowButton(ThemeAware, QAbstractButton):
    # 背光按钮：常态内凹座；按下/checked/LED 亮时画径向辉光（led 色扩散）+ 亮色文字
    def __init__(self, text: str = "", parent=None):
        # 初始化：文本、LED 灯态与颜色、固定圆角；最小尺寸 = 配置基准 × ui_scale（J4）
        super().__init__(parent)
        self.setText(text)
        self._led_on = False
        self._led_color = palette.color("glow_white", "#e8ecf0")
        self._outline_active = False  # 描边激活模式（PL001.11：checked 画描边不整面辉光）
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(
            s(int(_UI.get("button_min_width", 32))),
            s(int(_UI.get("button_min_height", 32))),
        )
        self.bind_theme()  # J2：主题切换自动重绘

    def set_outline_active(self, on: bool) -> None:
        # 描边激活模式开关（PL001.11：checked 时画 led 色描边 + 亮字，不整面辉光）
        self._outline_active = bool(on)
        self.update()

    def text_fits(self) -> bool:
        # 文本在当前按钮宽内完整放下（PL001.2 断言口；与 paintEvent 同一套缩字逻辑）
        fm = QFontMetrics(self.font())
        avail = self.width() - 6
        if fm.horizontalAdvance(self.text()) <= avail:
            return True
        shrunk = QFont(self.font())
        shrunk.setPointSize(max(8, shrunk.pointSize() - 1))
        return QFontMetrics(shrunk).horizontalAdvance(self.text()) <= avail

    def sizeHint(self) -> "QSize":
        # 文本驱动尺寸（PL001.2 根因修复：QAbstractButton 无 sizeHint 覆写时布局
        # 只给最小宽 32px——全部截断的源头）；宽度 = 文本宽 + 8px 边距，高 = 基准
        fm = QFontMetrics(self.font())
        return QSize(max(s(32), fm.horizontalAdvance(self.text()) + 8), s(32))

    def _glow_params(self) -> tuple[float, int, int]:
        # 辉光参数（PL001.11/14 + FIX004.12）：(半径系数, 外圈 alpha, 中圈 alpha)
        # 按压 = 全强度；**checked 默认降档**（勾选键不抢主操作——业务 LED 亮时
        # 除外：模式键/播放键等状态指示保持全强度）；描边激活走独立分支不进此；
        # light 主题整体降档
        light = palette.current() == "light"
        if self.isDown():
            return (1.0, 150, 70) if light else (1.0, 220, 110)
        if self.isChecked() and not self._led_on:
            return (0.85, 90, 45) if light else (0.85, 150, 75)
        return (1.0, 150, 70) if light else (1.0, 220, 110)

    def set_led(self, on: bool, color: QColor | str | None = None) -> None:
        # 设置 LED 灯态（on + 可选颜色；空=保持当前色）
        # I3.5：状态未变化不重绘（_tick 100ms × 十余控件高频调用，原无条件
        # update 造成 ~180 次/秒无效全量重绘）
        changed = False
        if color is not None:
            c = QColor(color)
            if c != self._led_color:
                self._led_color = c
                changed = True
        on = bool(on)
        if on != self._led_on:
            self._led_on = on
            changed = True
        if changed:
            self.update()

    def led_on(self) -> bool:
        # LED 灯态查询（Pad/模式键灯阵用）
        return self._led_on

    def paintEvent(self, event) -> None:
        # 按状态绘制：底座（常态/悬停）或辉光（按下/checked/led_on）+ 文字；
        # 禁用态 35% 透明度（J0.4）；描边激活模式画 led 色描边不整面辉光（PL001.11）；
        # 文本自适应缩字（PL001.2：超宽先降一档字号再省略，优先可读）
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            p.setOpacity(0.35)
        w, h = self.width(), self.height()
        rect = QRectF(1.5, 1.5, w - 3.0, h - 3.0)
        path = QPainterPath()
        path.addRoundedRect(rect, _RADIUS, _RADIUS)
        active = self.isDown() or self.isChecked() or self._led_on
        outline_now = self._outline_active and self.isChecked() and not self.isDown()
        if active and not outline_now:
            radius_scale, alpha_out, alpha_mid = self._glow_params()
            # 辉光：径向渐变（led 色中心亮 → 透明扩散，半径超过按钮范围
            # 让光晕溢出按钮，模拟硬件背光；参数分档见 _glow_params）
            grad = QRadialGradient(rect.center(), max(w, h) * 1.5 * radius_scale)
            glow = self._led_color
            grad.setColorAt(0.0, QColor(glow.red(), glow.green(), glow.blue(), alpha_out))
            grad.setColorAt(0.35, QColor(glow.red(), glow.green(), glow.blue(), alpha_mid))
            grad.setColorAt(1.0, QColor(glow.red(), glow.green(), glow.blue(), 0))
            p.fillPath(path, grad)
            # 底色提亮（辉光叠在亮底上更透）
            p.fillPath(path, QColor(glow.red(), glow.green(), glow.blue(), 60))
            p.setPen(QPen(QColor(glow.red(), glow.green(), glow.blue(), alpha_out), 1))
            p.drawPath(path)
            text_color = palette.color("glow_white", "#e8ecf0")  # H3.3：统一 token
        elif outline_now:
            # 描边激活（PL001.11）：led 色 1.5px 描边 + 微透底 + 亮字——激活不抢主操作
            glow = self._led_color
            p.fillPath(path, QColor(glow.red(), glow.green(), glow.blue(), 40))
            p.setPen(QPen(glow, 1.5))
            p.drawPath(path)
            text_color = palette.color("glow_white", "#e8ecf0")
        else:
            # 常态：内凹座（inset 底 + 底缘深线模拟凹入）
            p.fillPath(path, palette.color("panel_inset", "#101215"))
            p.setPen(QPen(QColor(0, 0, 0, 100), 1))
            p.drawPath(path)
            text_color = palette.color("silk_text", "#8a9099")
        # 文字居中（PL001.2：超宽先降一档字号，仍超宽才省略——文本优先可读）
        p.setPen(text_color)
        fm = p.fontMetrics()
        avail = int(rect.width() - 6)
        draw_font = QFont(p.font())
        if fm.horizontalAdvance(self.text()) > avail:
            draw_font.setPointSize(max(8, draw_font.pointSize() - 1))
            p.setFont(draw_font)
            fm = p.fontMetrics()
        elided = fm.elidedText(self.text(), Qt.ElideRight, avail)
        p.drawText(rect, Qt.AlignCenter, elided)
        p.end()


# ===== ui/widgets/glow_button.py 模块说明 =====
# 类：GlowButton(QAbstractButton)——拟物背光按钮
#   set_led(on, color)：LED 灯态 + 模式色（Pad 五模式/PLAY/CUE 等）；led_on() 查询
#   sizeHint()：文本驱动尺寸（PL001.2 根因修复——QAbstractButton 默认无文本
#     sizeHint，布局只给最小宽 32px，是全应用按钮截断的源头）
#   text_fits()：文本完整放下断言口（探针用；与 paint 缩字逻辑同源）
#   _glow_params()：辉光参数分档（PL001.11/14：按压全强度、checked 降档、
#     light 主题整体降档——防激活态抢主操作与浅底光晕发脏）
#   set_outline_active(on)：描边激活模式（PL001.11：checked 画 led 描边 +
#     亮字不整面辉光；FX ON 用）
#   _glow_params()：辉光分档（FIX004.12：checked 无业务 LED 默认降档——
#     原 set_checked_tier 死开关废弃，改默认生效）
#   绘制：常态内凹座 + silk 文字；按下/checked/led_on 辉光（分档）+ 白字；
#     描边激活态描边 + 微透底；超宽文本先降一档字号再省略（PL001.2）
# 设计理由：LED 灯态独立于 checked（业务灯态与交互态分离，E2.7 灯阵复用）；
#   辉光用径向渐变模拟发光（无需贴图，主题化友好）
# 关联配置：config/static/ui.json（panel_inset/silk_text/glow_white/glow_orange）；
#   ui.palette（辉光分档按主题现取）

# PanelFrame 面板容器：圆角渐变底 + 顶部高光 + 内凹描边 + 丝印标题（M1.6 四区容器）

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QFrame, QLabel

from config.static.static_config import get_static_config

# 静态配置解包（面板配色，AGENTS.md 参数约定）
_SC = get_static_config()
_UI = _SC.ui
_PANEL_BASE = QColor(_UI.get("panel_base", "#1c1e22"))
_PANEL_EDGE = QColor(_UI.get("panel_edge", "#26292f"))
_PANEL_INSET = QColor(_UI.get("panel_inset", "#101215"))
_SILK = QColor(_UI.get("silk_text", "#8a9099"))
_RADIUS = 10  # 面板圆角


class PanelFrame(QFrame):
    # 拟物面板：静态层（渐变/高光/描边）一次渲染 QPixmap 缓存，paintEvent 仅 blit
    def __init__(self, title: str = "", parent=None):
        # 初始化：标题 QLabel 叠放（丝印样式）；无标题则只画面板
        super().__init__(parent)
        self._title = title
        self._pixmap: QPixmap | None = None
        self._cached_size = None
        if title:
            self._label = QLabel(title.upper(), self)
            self._label.setStyleSheet(
                f"color: {_SILK.name(QColor.HexRgb)}; font-weight: 600; "
                f"letter-spacing: 3px; background: transparent;"
            )
            self._label.move(12, 6)

    def set_title(self, title: str) -> None:
        # 运行期改标题（G0.6：无标题构造时惰性创建标签，防 AttributeError）
        self._title = title
        if not hasattr(self, "_label"):
            self._label = QLabel(title.upper(), self)
            self._label.setStyleSheet(
                f"color: {_SILK.name(QColor.HexRgb)}; font-weight: 600; "
                f"letter-spacing: 3px; background: transparent;"
            )
            self._label.move(12, 6)
        self._label.setText(title.upper())

    def paintEvent(self, event) -> None:
        # 面板绘制：尺寸变化时重建静态缓存，否则直接 blit
        if self._pixmap is None or self._cached_size != self.size():
            self._render_cache()
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._pixmap)

    def _render_cache(self) -> None:
        # 静态层一次性渲染：圆角渐变底（加深）+ 金属拉丝线 + 顶部高光带 + 描边
        w = max(self.width(), 1)
        h = max(self.height(), 1)
        pm = QPixmap(w, h)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(1.0, 1.0, w - 2.0, h - 2.0)
        path = QPainterPath()
        path.addRoundedRect(rect, _RADIUS, _RADIUS)
        # 主体：垂直渐变（上浅下深，金属面板感；加深底色更接近 FLX4）
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(
            0.0, QColor(_PANEL_BASE.red(), _PANEL_BASE.green(), _PANEL_BASE.blue())
        )
        grad.setColorAt(
            0.5,
            QColor(
                _PANEL_BASE.red() + 6, _PANEL_BASE.green() + 6, _PANEL_BASE.blue() + 8
            ),
        )
        grad.setColorAt(1.0, _PANEL_EDGE)
        p.fillPath(path, grad)
        # 金属拉丝线：数条 1px 半透明白色横线（间隔 6px，顶部密底部疏）
        p.setClipPath(path)
        for y in range(4, h - 4, 6):
            alpha = 10 if (y // 6) % 2 == 0 else 5
            p.setPen(QPen(QColor(255, 255, 255, alpha), 1))
            p.drawLine(3, y, w - 3, y)
        p.setClipping(False)
        # 顶部 3px 高光带（外部光线反射）
        hi = QLinearGradient(0, 0, 0, 6)
        hi.setColorAt(0.0, QColor(255, 255, 255, 52))
        hi.setColorAt(1.0, QColor(255, 255, 255, 0))
        hi_path = QPainterPath()
        hi_path.addRoundedRect(QRectF(2.0, 2.0, w - 4.0, 6.0), 5, 5)
        p.fillPath(hi_path, hi)
        # 底缘内凹描边（面板嵌进台面）
        p.setPen(QPen(QColor(0, 0, 0, 110), 1))
        p.drawPath(path)
        p.end()
        self._pixmap = pm
        self._cached_size = self.size()


# ===== ui/widgets/panel_frame.py 模块说明 =====
# 类：PanelFrame(QFrame)——四区面板容器
#   __init__(title)：创建面板与丝印标题 QLabel（uppercase + 字距 3px + silk 色）
#   set_title(title)：运行期改标题
#   paintEvent(event)：尺寸变化重建缓存，否则 blit 静态层
#   _render_cache()：渐变底/顶部高光/底缘描边一次渲染到 QPixmap
# 设计理由：静态外观一次渲染（性能：重绘零开销，M1.6 性能策略）；
#   标题用 QLabel 便于后续主题化/国际化
# 关联配置：config/static/ui.json（panel_base/panel_edge/panel_inset/silk_text）

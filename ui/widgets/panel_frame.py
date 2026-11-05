# PanelFrame 面板容器：圆角渐变底 + 顶部高光 + 内凹描边 + 丝印标题（M1.6 四区容器）

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QFrame, QLabel

from config.static.static_config import get_static_config
from ui import palette
from ui.palette import ThemeAware
from ui.widgets import _textures

# 静态配置解包（面板圆角；配色改渲染时经 palette 现取，J2 批次 2）
_RADIUS = 10  # 面板圆角


class PanelFrame(ThemeAware, QFrame):
    # 拟物面板：静态层（渐变/高光/描边）一次渲染 QPixmap 缓存，paintEvent 仅 blit
    def __init__(self, title: str = "", parent=None):
        # 初始化：标题 QLabel 叠放（丝印样式）；无标题则只画面板；主题感知（J2）
        super().__init__(parent)
        self._title = title
        self._pixmap: QPixmap | None = None
        self._cached_size = None
        self.bind_theme()  # J2：主题切换清静态缓存重渲染
        if title:
            self._make_label(title)

    def _make_label(self, title: str) -> None:
        # 创建丝印标题 QLabel（silk 色按当前主题现取，J2）
        silk = palette.color("silk_text", "#8a9099")
        self._label = QLabel(title.upper(), self)
        self._label.setStyleSheet(
            f"color: {silk.name(QColor.HexRgb)}; font-weight: 600; "
            f"letter-spacing: 3px; background: transparent;"
        )
        self._label.move(12, 6)

    def set_title(self, title: str) -> None:
        # 运行期改标题（G0.6：无标题构造时惰性创建标签，防 AttributeError）
        self._title = title
        if not hasattr(self, "_label"):
            self._make_label(title)
        self._label.setText(title.upper())

    def paintEvent(self, event) -> None:
        # 面板绘制：尺寸变化时重建静态缓存，否则直接 blit
        if self._pixmap is None or self._cached_size != self.size():
            self._render_cache()
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._pixmap)

    def _render_cache(self) -> None:
        # 静态层一次性渲染：拉丝金属贴图底（J3 A 路线：程序化 PNG 缓存）+
        # 顶部高光带 + 描边（配色渲染时经 palette 现取，主题切换随缓存失效换贴图）
        w = max(self.width(), 1)
        h = max(self.height(), 1)
        pm = QPixmap(w, h)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(1.0, 1.0, w - 2.0, h - 2.0)
        path = QPainterPath()
        path.addRoundedRect(rect, _RADIUS, _RADIUS)
        # 主体：拉丝金属贴图裁剪到圆角（texture 按主题/尺寸键控三级缓存）
        tex = _textures.texture("brushed", w, h)
        p.setClipPath(path)
        p.drawPixmap(0, 0, tex)
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

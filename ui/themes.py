# 主题模块：从 config/static/ui.json 颜色生成 QSS（深色 DJ 风格，D4.5）

from __future__ import annotations

from PySide6.QtWidgets import QApplication, QWidget

from config.static.static_config import get_static_config

# 静态配置解包（主题颜色，AGENTS.md 参数约定）
_SC = get_static_config()
_UI = _SC.ui


def _build_qss(colors: dict) -> str:
    # 由颜色表生成深色 QSS：背景/前景/强调色 + 通用控件样式
    # H2.3：QSS 内全部颜色 token 化（panel_base/panel_edge/panel_inset 等），
    # 消除硬编码色值（原说明区"颜色零硬编码"与实现矛盾已修复）
    bg = colors.get("background", "#0d0d0d")
    fg = colors.get("accent", "#00ff41")
    warn = colors.get("warning", "#ffcc00")
    deck_a = colors.get("deck_a", "#00cccc")
    deck_b = colors.get("deck_b", "#cccc00")
    inset = _UI.get("panel_inset", "#101215")
    edge = _UI.get("panel_edge", "#26292f")
    base = _UI.get("panel_base", "#1c1e22")
    return f"""
    QMainWindow, QWidget {{ background: {bg}; color: {fg}; }}
    QLabel {{ color: {fg}; }}
    QPushButton {{
        background: {inset}; color: {fg}; border: 1px solid {edge};
        border-radius: 3px; padding: 4px 10px;
    }}
    QPushButton:hover {{ background: {edge}; }}
    QPushButton:checked {{ background: {deck_a}; color: {bg}; }}
    QCheckBox {{ color: {fg}; }}
    QSlider::groove:horizontal {{
        height: 4px; background: {edge}; border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 12px; margin: -4px 0; border-radius: 6px;
        background: {fg};
    }}
    QTableWidget {{
        background: {base}; color: {fg}; gridline-color: {edge};
        border: 1px solid {edge};
    }}
    QTableWidget::item:selected {{ background: {deck_b}; }}
    QLineEdit {{ background: {base}; color: {fg}; border: 1px solid {edge}; }}
    QStatusBar {{ color: {warn}; }}
    """


def apply_theme(app: QApplication, theme: str | None = None) -> None:
    # 应用主题 QSS 到应用（颜色来自 ui.json；默认主题读 base.json default_theme，
    # I3.4：原签名硬编码 "dark" 与配置脱钩；浅色主题预留 M1.7 批次 2 实现）
    if theme is None:
        theme = str(_SC.base.get("default_theme", "dark"))
    if theme != "dark":
        # 浅色主题预留：M1 仅深色（base.json default_theme=dark）
        pass
    app.setStyleSheet(_build_qss(_SC.ui.get("colors", {})))


# ===== ui/themes.py 模块说明 =====
# 函数：
#   _build_qss(colors)：由颜色表生成深色 QSS 字符串（背景/前景/强调色/通用控件；
#     H2.3 起控件底色/边框全部引用 ui.json token：panel_inset/panel_edge/panel_base）
#   apply_theme(app, theme)：应用主题（M1 仅深色；默认主题读 base.json
#     default_theme，颜色来自 config/static/ui.json）
# 设计理由：颜色全部 token 化（AGENTS.md 参数约定，ui.json 为唯一来源）；
#   QSS 模板化便于后续浅色主题扩展
# 关联配置：config/static/ui.json（colors.* + panel_inset/panel_edge/panel_base）；
#   config/static/base.json（default_theme，I3.4 补录）

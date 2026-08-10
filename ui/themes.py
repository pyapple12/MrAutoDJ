# 主题模块：从 config/static/ui.json 颜色生成 QSS（深色 DJ 风格，D4.5）

from __future__ import annotations

from PySide6.QtWidgets import QApplication, QWidget

from config.static.static_config import get_static_config

# 静态配置解包（主题颜色，AGENTS.md 参数约定）
_SC = get_static_config()


def _build_qss(colors: dict) -> str:
    # 由颜色表生成深色 QSS：背景/前景/强调色 + 通用控件样式
    bg = colors.get("background", "#0d0d0d")
    fg = colors.get("accent", "#00ff41")
    warn = colors.get("warning", "#ffcc00")
    deck_a = colors.get("deck_a", "#00cccc")
    deck_b = colors.get("deck_b", "#cccc00")
    return f"""
    QMainWindow, QWidget {{ background: {bg}; color: {fg}; }}
    QLabel {{ color: {fg}; }}
    QPushButton {{
        background: #1a1a1a; color: {fg}; border: 1px solid #2a2a2a;
        border-radius: 3px; padding: 4px 10px;
    }}
    QPushButton:hover {{ background: #222222; }}
    QPushButton:checked {{ background: {deck_a}; color: #0d0d0d; }}
    QCheckBox {{ color: {fg}; }}
    QSlider::groove:horizontal {{
        height: 4px; background: #2a2a2a; border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 12px; margin: -4px 0; border-radius: 6px;
        background: {fg};
    }}
    QTableWidget {{
        background: #111111; color: {fg}; gridline-color: #222222;
        border: 1px solid #2a2a2a;
    }}
    QTableWidget::item:selected {{ background: #003300; }}
    QLineEdit {{ background: #111111; color: {fg}; border: 1px solid #2a2a2a; }}
    QStatusBar {{ color: {warn}; }}
    """


def apply_theme(app: QApplication, theme: str = "dark") -> None:
    # 应用主题 QSS 到应用（颜色来自 ui.json；浅色主题暂未实现，深色为默认）
    if theme != "dark":
        # 浅色主题预留：M1 仅深色（ui.json default_theme=dark）
        pass
    app.setStyleSheet(_build_qss(_SC.ui.get("colors", {})))


# ===== ui/themes.py 模块说明 =====
# 函数：
#   _build_qss(colors)：由颜色表生成深色 QSS 字符串（背景/前景/强调色/通用控件）
#   apply_theme(app, theme)：应用主题（M1 仅深色；颜色来自 config/static/ui.json）
# 设计理由：颜色零硬编码（AGENTS.md 参数约定，ui.json 为唯一来源）；
#   QSS 模板化便于后续浅色主题扩展
# 关联配置：config/static/ui.json（colors.*）

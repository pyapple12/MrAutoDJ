# 主题模块：QSS 生成 + 运行期多主题切换（J2 批次 2）
# dark = ui.json 原生 token；light = ui.json + theme_light 覆盖（token 表见 ui/palette.py）

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from config.static.static_config import get_static_config
from ui import palette

_SC = get_static_config()


def _build_qss(colors: dict) -> str:
    # 由颜色表生成 QSS：背景/前景/强调色 + 通用控件样式（H2.3 全 token 化；
    # J2 起面板 token 亦经 palette 现取，跟随运行期主题）
    bg = colors.get("background", "#0d0d0d")
    fg = colors.get("accent", "#00ff41")
    warn = colors.get("warning", "#ffcc00")
    deck_a = colors.get("deck_a", "#00cccc")
    deck_b = colors.get("deck_b", "#cccc00")
    inset = palette.token("panel_inset", "#101215")
    edge = palette.token("panel_edge", "#26292f")
    base = palette.token("panel_base", "#1c1e22")
    return f"""
    QMainWindow {{ background: {bg}; }}
    QWidget {{ color: {fg}; background: transparent; }}
    QLabel {{ color: {fg}; background: transparent; }}
    QPushButton {{
        background: {inset}; color: {fg}; border: 1px solid {edge};
        border-radius: 3px; padding: 4px 10px;
    }}
    QPushButton:hover {{ background: {edge}; }}
    QPushButton:checked {{ background: {deck_a}; color: {bg}; }}
    QCheckBox {{ color: {fg}; background: transparent; }}
    QTableWidget {{
        background: {base}; color: {fg}; gridline-color: {edge};
        border: 1px solid {edge};
    }}
    QTableWidget::item:selected {{ background: {deck_b}; }}
    QLineEdit {{ background: {base}; color: {fg}; border: 1px solid {edge}; }}
    QStatusBar {{ color: {warn}; background: {bg}; }}
    """


def apply_theme(app: QApplication, theme: str | None = None) -> bool:
    # 应用主题（J2）：palette.set_theme 切 token 表 + 重建 QSS；
    # theme=None 读 base.json default_theme；未知主题返回 False 不抛
    if theme is None:
        theme = str(_SC.base.get("default_theme", "dark"))
    if not palette.set_theme(theme):
        return False
    app.setStyleSheet(_build_qss(palette.token("colors", {})))
    return True


def switch_theme(app: QApplication, theme: str) -> bool:
    # 运行期切换主题（J2）：token 表 + QSS 一体重建；控件刷新经 ThemeBus
    # 广播（ThemeAware 混入清缓存重绘），静态 LED 重涂由调用方负责
    return apply_theme(app, theme)


# ===== ui/themes.py 模块说明 =====
# 函数：
#   _build_qss(colors)：由颜色表生成 QSS（背景/前景/强调色/通用控件；
#     panel token 经 palette 现取，跟随运行期主题）
#   apply_theme(app, theme)：palette.set_theme + 重建 QSS（返回是否成功；
#     theme=None 读 base.json default_theme）
#   switch_theme(app, theme)：运行期切换入口（J2；与 apply_theme 同实现，
#     语义分离便于调用方阅读）
# 设计理由：颜色全部 token 化（AGENTS.md 参数约定）；J2 起主题切换 =
#   palette token 表重建 → 总线广播（控件清缓存重绘）→ QSS 重建，
#   全程无重启、无花屏（统一刷新入口 ThemeAware）
#   （PL001.6：QSS 删全局 QWidget 实底改全局透明 + 定点实底（表/输入框/
#   状态栏/主窗）——原全局实底在拟物纹理面板上打黑/白补丁；QSlider 规则随
#   Pitch 拟物化（PL001.12）删除）
# 异常处理：未知主题返回 False；缺键走默认
# 关联配置：config/static/ui.json（colors.* + panel_* + theme_light 覆盖表）；
#   config/static/base.json（default_theme）

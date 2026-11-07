# 运行期主题 token 提供者（J2 批次 2）：dark = ui.json 原生；light = ui.json + theme_light 覆盖
# 功能与 UI 数据层切割：控件 paint 时经 token()/color() 现取，主题切换经 ThemeBus 广播刷新
# （QSS 由 ui.themes.apply_theme 重建；静态层 QPixmap 缓存由 ThemeAware 混入清失效）

from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor

from config.static.static_config import get_static_config

_SC = get_static_config()
_UI = _SC.ui

# 主题注册表（J2）：dark = ui.json 全量 token；light = ui.json + theme_light 覆盖；
# FIX004/N4：白名单从 base.json themes 派生（与 settings 同源，消除第三处漂移）
AVAILABLE_THEMES = tuple(_SC.base.get("themes", ["dark", "light"])) or ("dark",)


class _ThemeBus(QObject):
    # 主题切换通知总线（进程单例；控件经 bind_theme 订阅）
    changed = Signal(str)


_bus: _ThemeBus | None = None


def bus() -> _ThemeBus:
    # 总线单例（惰性创建，避免 import 期构造 QObject）
    global _bus
    if _bus is None:
        _bus = _ThemeBus()
    return _bus


# light 覆盖表（ui.json theme_light；无键则与 dark 同）
_LIGHT_OVERRIDES: dict = dict(_UI.get("theme_light", {}))

_tokens: dict = dict(_UI)
_current = "dark"


def current() -> str:
    # 当前主题名
    return _current


def token(key: str, default=None):
    # 现取顶层 token（paint 时调用；dict 读原子，无锁安全）
    return _tokens.get(key, default)


def color(key: str, default: str) -> QColor:
    # 颜色 token：colors 子对象优先（warning/danger/accent 等），回退顶层键
    sub = _tokens.get("colors", {})
    if key in sub:
        return QColor(str(sub[key]))
    return QColor(str(_tokens.get(key, default)))


def silk_label_style(extra: str = "") -> str:
    # 丝印标签内联样式（FIX005/P3-11：原 4 份重复样式串统一——lib_hint 构造/
    # 刷新、panel_frame 两处；extra 附加如 "font-size: 12px; "）
    silk = color("silk_text", "#8a9099")
    return f"color: {silk.name(QColor.HexRgb)}; {extra} background: transparent;"


def set_theme(name: str) -> bool:
    # 切换主题（J2）：重建 token 表并广播 changed；未知主题拒绝返回 False。
    # 调用方负责重建 QSS（themes.apply_theme）与静态 LED 重涂
    global _tokens, _current
    if name not in AVAILABLE_THEMES:
        return False
    if name == _current:
        return True
    if name == "light":
        merged = dict(_UI)
        merged.update(_LIGHT_OVERRIDES)
        colors = dict(_UI.get("colors", {}))
        colors.update(_LIGHT_OVERRIDES.get("colors", {}))
        merged["colors"] = colors
        _tokens = merged
    else:
        _tokens = dict(_UI)
    _current = name
    bus().changed.emit(name)
    return True


class ThemeAware:
    # 主题感知混入（J2）：控件 __init__ 调 bind_theme()；主题切换时清静态层
    # QPixmap 缓存并重绘（防漏刷新花屏——统一刷新入口）

    def bind_theme(self) -> None:
        # 订阅主题总线（控件与窗口同生命周期，不额外断连）
        bus().changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, name: str) -> None:
        # 缓存失效 + 重绘（有静态层 _pixmap 的控件一并清 _cached_size）
        if getattr(self, "_pixmap", None) is not None:
            self._pixmap = None
            self._cached_size = None
        self.update()


# ===== ui/palette.py 模块说明 =====
# 模块级常量：
#   AVAILABLE_THEMES：主题注册表（dark/light，J2）
#   _LIGHT_OVERRIDES：light 主题覆盖（ui.json theme_light）
# 函数：
#   bus()：ThemeBus 单例（changed(str) 主题切换广播）
#   token(key, default)：顶层 token 现取（paint 时调用，零锁）
#   color(key, default)：颜色 token（colors 子对象优先，回退顶层）
#   set_theme(name)：切换 token 表 + 广播；QSS 重建由 themes.apply_theme 负责
# 类型：
#   ThemeAware：控件混入——bind_theme() 订阅；切换时清 _pixmap 缓存并 update()
# 设计理由：批次 2"功能与 UI 数据层切割"在运行期落地——原语控件不再在模块
#   import 期固化 QColor 常量，统一改 paint 时经 palette 现取；
#   主题切换 = set_theme（token 表）→ 总线广播 → 控件清缓存重绘 → apply_theme(QSS)
# 异常处理：未知主题 set_theme 返回 False 不抛；token 缺键回默认
# 关联配置：config/static/ui.json（全量 token；theme_light 覆盖表）

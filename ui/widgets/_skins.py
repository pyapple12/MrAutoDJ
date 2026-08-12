# 公共皮肤绘制工具（ui/widgets/ 内部共享，G1.2 去重）
# 用途：金属渐变/描边/高光——jog_wheel/fader_slider/rotary_knob 三处原各写一份

from __future__ import annotations

from PySide6.QtGui import QColor, QLinearGradient, QPen


def metal_gradient(
    x1: float = 0, y1: float = 0, x2: float = 0, y2: float = 0
) -> QLinearGradient:
    # 金属垂直/对角渐变（顶部亮 → 中灰 → 底部暗），返回可作 brush 的渐变
    g = QLinearGradient(x1, y1, x2, y2)
    g.setColorAt(0.0, QColor(208, 212, 218))
    g.setColorAt(0.5, QColor(150, 154, 160))
    g.setColorAt(1.0, QColor(112, 116, 122))
    return g


def metal_pen(width: float = 1.0) -> QPen:
    # 金属部件描边（深灰，统一观感）
    return QPen(QColor(60, 64, 70), width)


def top_highlight_pen(alpha: int = 110, width: float = 1.0) -> QPen:
    # 顶部高光棱线（金属部件受光面）
    return QPen(QColor(255, 255, 255, alpha), width)


# ===== ui/widgets/_skins.py 模块说明 =====
# 函数：
#   metal_gradient(x1,y1,x2,y2)：三档金属渐变（208,212,218 → 150,154,160 → 112,116,122）
#   metal_pen(width)：金属部件深灰描边
#   top_highlight_pen(alpha, width)：顶部高光棱线
# 设计理由：jog_wheel/fader_slider/rotary_knob 金属质感绘制重复三份且色值微差，
#   G1.2 收敛为单一实现（视觉统一，后续调质感只改一处）
# 关联配置：无（纯绘制工具，零业务依赖）

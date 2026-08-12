# 性能打击垫组件：1×8 网格 + 模式切换（FLX4 8 种 Pad 模式中的 5 种可软件实现）
# F6.2 改版：QPushButton → GlowButton（背光 + 五模式色灯态）

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from config.static.static_config import get_static_config
from ui.widgets.glow_button import GlowButton

# 静态配置解包（Pad 五模式色）
_SC = get_static_config()
_UI = _SC.ui
_PAD_COLORS = _UI.get(
    "pad_colors", ["#ff7a2f", "#00cccc", "#2fe37a", "#ff4444", "#ffcc00"]
)

# 可软件实现的 Pad 模式（FLX4 模式键：HOT CUE / PAD FX1 / PAD FX2 / BEAT JUMP /
# SAMPLER / KEYBOARD / BEAT LOOP / KEY SHIFT；此处取核心 5 种）
PAD_MODES = ["Hot Cue", "Beat Loop", "Beat Jump", "Sampler", "Key Shift"]


class PadWidget(QWidget):
    # 打击垫组件：1×8 网格 + 模式切换行；灯态由 set_pad_light 驱动（GlowButton LED）
    pad_clicked = Signal(int, str)  # (pad 序号 0-7, 当前模式)
    mode_changed = Signal(str)

    def __init__(self, parent=None):
        # 初始化：8 个可勾选 GlowButton + 5 个模式键（五模式色）
        super().__init__(parent)
        self._mode = "Hot Cue"
        self._pad_buttons = []

        pads = QGridLayout()
        pads.setSpacing(4)
        for i in range(8):
            btn = GlowButton(f"P{i + 1}")
            # G0.5：pad 不使用勾选态（点按辉光由 isDown 驱动，业务灯态由
            # set_pad_light→set_led 驱动，防 isChecked 残留导致灯阵失真）
            btn.setFixedSize(35, 35)
            btn.clicked.connect(
                lambda checked, idx=i: self.pad_clicked.emit(idx, self._mode)
            )
            pads.addWidget(btn, 0, i)
            self._pad_buttons.append(btn)

        modes = QHBoxLayout()
        modes.addWidget(QLabel("模式"))
        self._mode_buttons = {}
        for name in PAD_MODES:
            btn = GlowButton(name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=name: self._select_mode(m))
            modes.addWidget(btn)
            self._mode_buttons[name] = btn
        self._mode_buttons["Hot Cue"].setChecked(True)
        self._apply_mode_color()

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.addLayout(pads)
        layout.addLayout(modes)

    # --- 模式 ---

    def _apply_mode_color(self) -> None:
        # 模式色同步：当前模式键亮起（pad 灯色由 set_pad_light 按模式色控制）
        color = _PAD_COLORS[PAD_MODES.index(self._mode) % len(_PAD_COLORS)]
        for name, btn in self._mode_buttons.items():
            btn.set_led(name == self._mode, color if name == self._mode else None)

    def _select_mode(self, mode: str) -> None:
        # 切换模式：互斥勾选 + 模式色 + 清 pad 灯态 + 发信号
        self._mode = mode
        for name, btn in self._mode_buttons.items():
            btn.setChecked(name == mode)
        self._apply_mode_color()
        self.clear_pad_lights()
        self.mode_changed.emit(mode)

    @property
    def mode(self) -> str:
        # 当前模式（UI/引擎映射用）
        return self._mode

    def mode_color(self) -> str:
        # 当前模式色（pad 灯态默认色）
        return _PAD_COLORS[PAD_MODES.index(self._mode) % len(_PAD_COLORS)]

    # --- 灯态（E2.7） ---

    def set_pad_light(self, idx: int, on: bool) -> None:
        # 设置 pad 灯态（GlowButton LED + 模式色；越界忽略）
        if 0 <= idx < 8:
            self._pad_buttons[idx].set_led(on, self.mode_color())

    def clear_pad_lights(self) -> None:
        # 清空全部 pad 灯（模式切换时调用）
        for btn in self._pad_buttons:
            btn.set_led(False)

    def pad_light(self, idx: int) -> bool:
        # 查询 pad 灯态（引擎状态同步用）
        return 0 <= idx < 8 and self._pad_buttons[idx].led_on()


# ===== ui/pad_widget.py 模块说明 =====
# 模块级常量：
#   PAD_MODES：可软件实现的 5 种 Pad 模式（Hot Cue/Beat Loop/Beat Jump/Sampler/Key Shift）
#   _PAD_COLORS：五模式色（ui.json pad_colors）
# 类型：
#   PadWidget(QWidget)：打击垫组件
# 信号：
#   pad_clicked(idx, mode)：pad 按下（携带当前模式）
#   mode_changed(mode)：模式切换
# 方法：
#   _apply_mode_color()：模式键 LED + pad 灯色跟随模式色
#   _select_mode(mode)：互斥切换 + 清灯 + 发信号
#   set_pad_light/clear_pad_lights/pad_light：灯态管理（E2.7 LED 联动）
#   mode_color()：当前模式色（pad 灯态默认色）
# 设计理由：组件零引擎依赖（信号解耦，MainWindow 接线）；
#   F6.2 换 GlowButton（背光硬件感 + 五模式色灯阵，对齐 FLX4 彩色 Pad）
# 关联配置：config/static/ui.json（pad_colors）

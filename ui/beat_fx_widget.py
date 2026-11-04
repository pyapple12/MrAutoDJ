# Beat FX 面板：通道选择 + 效果类型 + 拍数 ± + BPM Auto/Tap + LEVEL/DEPTH
# F6.4 改版：全按钮 → GlowButton、效果下拉 → 互斥按钮组、拍数 → MiniDisplay、
#   DEPTH 滑块 → RotaryKnob

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui.widgets.glow_button import GlowButton
from ui.widgets.mini_display import MiniDisplay
from ui.widgets.rotary_knob import RotaryKnob

# 静态配置解包（配色 token，G2.2）
from config.static.static_config import get_static_config

_UI = get_static_config().ui

# 效果库（E1.8 引擎实现 + 既有）
FX_TYPES = ["HPF", "LPF", "Trans", "Echo", "Delay"]

# 拍数阶梯（H1.1：单源，main_window 的 Beat Loop Pad 引用此常量）
BEAT_LADDER = [1, 2, 4, 8, 16, 32]


class BeatFxWidget(QWidget):
    # Beat FX 面板：选择/通道/拍数/深度/开关（全部原语控件）
    fx_changed = Signal(str)  # 效果类型
    channel_changed = Signal(str)  # "1" | "2" | "both"（预留未接线，I3.2/M1.7 批次 1 启用）
    beats_changed = Signal(int)  # 拍数（预留未接线，I3.2/M1.7 批次 1 启用）
    depth_changed = Signal(float)  # 0-1
    onoff_changed = Signal(bool)
    bpm_tap = Signal()  # TAP 按钮（预留未接线，I3.2/M1.7 批次 1 启用）
    bpm_auto = Signal()  # AUTO 按钮（预留未接线，I3.2/M1.7 批次 1 启用）

    def __init__(self, parent=None):
        # 初始化：效果按钮组 + 通道开关 + 拍数 ± + 深度旋钮 + 开关 + BPM 模式
        super().__init__(parent)

        # 效果类型：互斥按钮组（替代下拉，对齐 FLX4 循环选择视觉）
        self._fx_buttons = {}
        fx_row = QHBoxLayout()
        fx_row.addWidget(QLabel("FX"))
        for name in FX_TYPES:
            btn = GlowButton(name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, n=name: self._select_fx(n))
            fx_row.addWidget(btn)
            self._fx_buttons[name] = btn
        self._fx_buttons["HPF"].setChecked(True)

        # 通道
        self._ch_1 = GlowButton("CH1")
        self._ch_2 = GlowButton("CH2")
        self._ch_both = GlowButton("1+2")
        for b in (self._ch_1, self._ch_2, self._ch_both):
            b.setCheckable(True)
        self._ch_1.setChecked(True)
        self._ch_1.clicked.connect(lambda: self._select_channel("1"))
        self._ch_2.clicked.connect(lambda: self._select_channel("2"))
        self._ch_both.clicked.connect(lambda: self._select_channel("both"))

        # 拍数：MiniDisplay + ±按钮
        self._beats_disp = MiniDisplay()
        self._beats_disp.setFixedSize(48, 20)  # H3.5：与 MiniDisplay 最小尺寸对齐
        self._beats_minus = GlowButton("-")
        self._beats_plus = GlowButton("+")
        self._beats_minus.clicked.connect(self._beats_delta)
        self._beats_plus.clicked.connect(self._beats_delta)

        # 深度旋钮
        self._depth = RotaryKnob(0.0, 1.0, default=0.0, size=28)

        # 开关
        self._onoff = GlowButton("FX ON")
        self._onoff.setCheckable(True)

        # BPM 模式
        self._bpm_auto = GlowButton("AUTO")
        self._bpm_tap_btn = GlowButton("TAP")

        row1 = QHBoxLayout()
        row1.addLayout(fx_row)
        row1.addWidget(self._ch_1)
        row1.addWidget(self._ch_2)
        row1.addWidget(self._ch_both)

        row2 = QHBoxLayout()
        row2.addWidget(self._beats_minus)
        row2.addWidget(self._beats_disp)
        row2.addWidget(self._beats_plus)
        row2.addStretch(1)
        row2.addWidget(self._bpm_auto)
        row2.addWidget(self._bpm_tap_btn)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("DEPTH"))
        row3.addWidget(self._depth)
        row3.addWidget(self._onoff)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row3)

        # 信号
        self._depth.valueChanged.connect(self.depth_changed.emit)
        self._onoff.toggled.connect(self.onoff_changed.emit)
        self._bpm_auto.clicked.connect(self.bpm_auto.emit)
        self._bpm_tap_btn.clicked.connect(self.bpm_tap.emit)
        self._beats = 1
        self._beats_disp.set_text("1")

    # --- 内部 ---

    def _select_fx(self, fx: str) -> None:
        # 效果互斥选择（橙色 LED 标识当前效果）
        for name, btn in self._fx_buttons.items():
            btn.setChecked(name == fx)
            btn.set_led(
                name == fx, _UI.get("glow_orange", "#ff7a2f") if name == fx else None
            )
        self.fx_changed.emit(fx)

    def _select_channel(self, ch: str) -> None:
        # 通道互斥选择 + 发信号
        for b, c in ((self._ch_1, "1"), (self._ch_2, "2"), (self._ch_both, "both")):
            b.setChecked(c == ch)
        self.channel_changed.emit(ch)

    def _beats_delta(self) -> None:
        # 拍数 ±（1-32，循环 BEAT_LADDER 阶梯）
        idx = BEAT_LADDER.index(self._beats) if self._beats in BEAT_LADDER else 0
        idx = (idx + 1) if self.sender() is self._beats_plus else (idx - 1)
        self.set_beats(BEAT_LADDER[idx % len(BEAT_LADDER)])
        self.beats_changed.emit(self._beats)

    def set_beats(self, beats: int) -> None:
        # 外部设置拍数（BPM Auto 联动；小屏同步）
        self._beats = max(1, min(32, beats))
        self._beats_disp.set_text(str(self._beats))

    def is_on(self) -> bool:
        # FX ON 开关状态公开查询（I1.2：替代 MainWindow 直访 _onoff.isChecked()
        # 私有字段，控件内部状态只经公开接口读取）
        return self._onoff.isChecked()


# ===== ui/beat_fx_widget.py 模块说明 =====
# 模块级常量：
#   FX_TYPES：效果库（HPF/LPF/Trans/Echo/Delay，与 E1.8 引擎对应）
# 类型：
#   BeatFxWidget(QWidget)：Beat FX 面板
# 信号：
#   fx_changed / depth_changed / onoff_changed：已接线（MainWindow 接引擎）
#   channel_changed / beats_changed / bpm_tap / bpm_auto：预留未接线
#     （I3.2 标注：对应 CH/AUTO/TAP 为用户可见预留控件，M1.7 批次 1 启用）
# 方法：
#   _select_fx(fx)：效果互斥（LED 橙色）
#   _select_channel(ch)：通道互斥
#   _beats_delta()：拍数阶梯 ±（1/2/4/8/16/32）
#   set_beats(beats)：外部同步（BPM Auto；小屏显示）
# 设计理由：B13-5 六部件（通道/选择/拍数±/深度/开关 + BPM Auto-Tap 为 SHIFT 语义独立化）；
#   F6.4 全原语化（GlowButton/MiniDisplay/RotaryKnob，对齐 FLX4 Effects 区视觉）
# 关联配置：config/static/ui.json（glow_orange 效果键灯色，H3.5 补全）

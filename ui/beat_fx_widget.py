# Beat FX 面板：通道选择 + 效果类型 + 拍数 ± + BPM Auto/Tap + LEVEL/DEPTH
# F6.4 改版：全按钮 → GlowButton、效果下拉 → 互斥按钮组、拍数 → MiniDisplay、
#   DEPTH 滑块 → RotaryKnob

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui import palette
from ui.scale import s
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

_FX_KNOB_SIZE = int(_UI.get("knob_size_fx", 28))  # J0.3：FX 区旋钮分级基准（J4 缩放）


class BeatFxWidget(QWidget):
    # Beat FX 面板：选择/通道/拍数/深度/开关（全部原语控件）
    fx_changed = Signal(str)  # 效果类型
    channel_changed = Signal(str)  # "1" | "2" | "both"（M1.7 已接线）
    beats_changed = Signal(int)  # 拍数（M1.7 已接线）
    depth_changed = Signal(float)  # 0-1
    onoff_changed = Signal(bool)
    bpm_tap = Signal()  # TAP 按钮（M1.7 已接线）
    bpm_auto = Signal()  # AUTO 按钮（M1.7 已接线）

    def __init__(self, parent=None):
        # 初始化：效果按钮组 + 通道开关 + 拍数 ± + 深度旋钮 + 开关 + BPM 模式
        super().__init__(parent)
        self._selected_fx = "HPF"  # 当前选中效果（J2 主题重涂 LED 用）

        # 效果类型：互斥按钮组（替代下拉，对齐 FLX4 循环选择视觉；PL001.3：
        # 去行首 "FX" 标签 + 紧凑行距 + 8pt 键字体——5 键 hint 总和须压进
        # effects 列最小宽 280 的内容区 264 防截断）
        self._fx_buttons = {}
        fx_row = QHBoxLayout()
        fx_row.setSpacing(2)
        for name in FX_TYPES:
            btn = GlowButton(name)
            btn.setCheckable(True)
            fx_font = btn.font()
            fx_font.setPointSize(8)
            btn.setFont(fx_font)
            btn.clicked.connect(lambda checked, n=name: self._select_fx(n))
            fx_row.addWidget(btn)
            self._fx_buttons[name] = btn
        self._fx_buttons["HPF"].setChecked(True)

        # 通道（J1.1 启用：FX 作用通道，MainWindow 按 CH 选择目标盘）
        self._ch_1 = GlowButton("CH1")
        self._ch_2 = GlowButton("CH2")
        self._ch_both = GlowButton("1+2")
        for b, tip in (
            (self._ch_1, "FX 作用于 DECK A"),
            (self._ch_2, "FX 作用于 DECK B"),
            (self._ch_both, "FX 同时作用于双盘"),
        ):
            b.setCheckable(True)
            b.setToolTip(tip)
        self._ch_1.setChecked(True)
        self._ch_1.clicked.connect(lambda: self._select_channel("1"))
        self._ch_2.clicked.connect(lambda: self._select_channel("2"))
        self._ch_both.clicked.connect(lambda: self._select_channel("both"))

        # 拍数：MiniDisplay + ±按钮（±有本地可见反馈保留可用；引擎接线 J1.1）
        self._beats_disp = MiniDisplay()
        self._beats_disp.setFixedSize(s(48), s(20))  # FIX005.7：恢复缩放（构造内仅 minimum）
        self._beats_minus = GlowButton("-")
        self._beats_plus = GlowButton("+")
        self._beats_minus.clicked.connect(self._beats_delta)
        self._beats_plus.clicked.connect(self._beats_delta)

        # 深度旋钮（J0.7：数值 Tooltip）
        self._depth = RotaryKnob(0.0, 1.0, default=0.0, size=_FX_KNOB_SIZE)  # FIX004.16 基准
        self._depth.setToolTip("深度 0%")
        self._depth.valueChanged.connect(
            lambda v: self._depth.setToolTip(f"深度 {v * 100:.0f}%")
        )

        # 开关（PL001.11：描边激活——checked 画 led 描边不整面辉光，主操作唯一性让位 Mix Now）
        self._onoff = GlowButton("FX ON")
        self._onoff.setCheckable(True)
        self._onoff.set_outline_active(True)

        # BPM 模式（J1.1 启用：AUTO=曲目 BPM 时基 / TAP=点按测速时基）
        self._bpm_auto = GlowButton("AUTO")
        self._bpm_tap_btn = GlowButton("TAP")
        self._bpm_auto.setToolTip("以曲目 BPM 作为 Beat FX 时基（Echo/Delay/Trans 同步节拍）")
        self._bpm_tap_btn.setToolTip("点按测速（同 Tap BPM），测得 BPM 作为 Beat FX 时基")

        # PL001.3：效果键与通道键拆两行（1650 窗宽下 8 键一行必截断）
        row1 = QHBoxLayout()
        row1.addLayout(fx_row)
        ch_row = QHBoxLayout()
        ch_row.setSpacing(2)
        ch_row.addWidget(QLabel("CH"))
        ch_row.addWidget(self._ch_1)
        ch_row.addWidget(self._ch_2)
        ch_row.addWidget(self._ch_both)
        ch_row.addStretch(1)

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
        layout.setContentsMargins(0, 0, 0, 0)  # PL001.3：默认 9px 边距挤占 FX 行宽（差 3px 截断）
        layout.setSpacing(4)
        layout.addLayout(row1)
        layout.addLayout(ch_row)
        layout.addLayout(row2)
        layout.addLayout(row3)

        # 信号
        self._depth.valueChanged.connect(self.depth_changed.emit)
        self._onoff.toggled.connect(self.onoff_changed.emit)
        self._bpm_auto.clicked.connect(self.bpm_auto.emit)
        self._bpm_tap_btn.clicked.connect(self.bpm_tap.emit)
        self._beats = 1
        self._beats_disp.set_text("1")
        # PL001.10：初始选中效果键走统一选中路径（初始即橙光，与点击后一致）
        self._select_fx("HPF")

    # --- 内部 ---

    def _select_fx(self, fx: str) -> None:
        # 效果互斥选择（橙色 LED 标识当前效果；J2 起色值 palette 现取）
        self._selected_fx = fx
        orange = palette.token("glow_orange", "#ff7a2f")
        for name, btn in self._fx_buttons.items():
            btn.setChecked(name == fx)
            btn.set_led(name == fx, orange if name == fx else None)
        self.fx_changed.emit(fx)

    def reapply_leds(self) -> None:
        # 主题切换后重涂效果键 LED（J2：当前选中效果重涂 glow_orange）
        orange = palette.token("glow_orange", "#ff7a2f")
        for name, btn in self._fx_buttons.items():
            btn.set_led(
                name == self._selected_fx, orange if name == self._selected_fx else None
            )

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
#   channel_changed / beats_changed / bpm_tap / bpm_auto：M1.7 起全部接线
#     （CH→FX 通道、beats→拍数、AUTO/TAP→FX 时基；I3.2 时的"预留"状态已解除）
# 方法：
#   _select_fx(fx)：效果互斥（LED 橙色；构造末尾即调一次——初始选中键橙光
#     与点击后一致，PL001.10）
#   _select_channel(ch)：通道互斥
#   _beats_delta()：拍数阶梯 ±（1/2/4/8/16/32）
#   set_beats(beats)：外部同步（BPM Auto；小屏显示）
#   is_on()：FX ON 开关公开查询（I1.2）
#   reapply_leds()：主题切换后重涂效果键 LED（J2）
# 布局（PL001.3）：效果 5 键行 / CH 3 键行 / 拍数+AUTO/TAP 行 / DEPTH+FX ON 行
#   四行；效果键 8pt 字体 + 去 "FX" 行标签 + VBox 边距归零（面板宽 280 内
#   容 264 的截断治理）；FX ON 描边激活（set_outline_active，PL001.11）
# 设计理由：B13-5 六部件（通道/选择/拍数±/深度/开关 + BPM Auto-Tap 为 SHIFT 语义独立化）；
#   F6.4 全原语化（GlowButton/MiniDisplay/RotaryKnob，对齐 FLX4 Effects 区视觉）
# 关联配置：config/static/ui.json（glow_orange 效果键灯色，H3.5 补全）

# Beat FX 面板：通道选择 + 效果类型 + 拍数 ± + BPM Auto/Tap + LEVEL/DEPTH
# 参考：w.study.md B13-5（Effects 区 6 部件）、MIDI 0x94 通道 FX 映射

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

# 效果库（E1.8 引擎实现 + 既有）
FX_TYPES = ["HPF", "LPF", "Trans", "Echo", "Delay"]


class BeatFxWidget(QWidget):
    # Beat FX 面板：选择/通道/拍数/深度/开关
    fx_changed = Signal(str)  # 效果类型
    channel_changed = Signal(str)  # "1" | "2" | "both"
    beats_changed = Signal(int)  # 拍数
    depth_changed = Signal(float)  # 0-1
    onoff_changed = Signal(bool)
    bpm_tap = Signal()
    bpm_auto = Signal()

    def __init__(self, parent=None):
        # 初始化：效果库下拉 + 通道开关 + 拍数 ± + 深度滑块 + 开关 + BPM 模式
        super().__init__(parent)

        self._fx_combo = QComboBox()
        self._fx_combo.addItems(FX_TYPES)

        self._ch_1 = QPushButton("CH1")
        self._ch_2 = QPushButton("CH2")
        self._ch_both = QPushButton("1+2")
        for b in (self._ch_1, self._ch_2, self._ch_both):
            b.setCheckable(True)
        self._ch_1.setChecked(True)

        self._beats_label = QLabel("1 拍")
        self._beats_minus = QPushButton("-")
        self._beats_plus = QPushButton("+")

        self._depth = QSlider(__import__("PySide6").QtCore.Qt.Horizontal)
        self._depth.setRange(0, 100)
        self._depth.setValue(0)

        self._onoff = QPushButton("FX ON")
        self._onoff.setCheckable(True)

        self._bpm_auto = QPushButton("BPM AUTO")
        self._bpm_tap_btn = QPushButton("TAP")

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("效果"))
        row1.addWidget(self._fx_combo)
        row1.addWidget(self._ch_1)
        row1.addWidget(self._ch_2)
        row1.addWidget(self._ch_both)

        row2 = QHBoxLayout()
        row2.addWidget(self._beats_minus)
        row2.addWidget(self._beats_label)
        row2.addWidget(self._beats_plus)
        row2.addStretch(1)
        row2.addWidget(self._bpm_auto)
        row2.addWidget(self._bpm_tap_btn)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("DEPTH"))
        row3.addWidget(self._depth, 1)
        row3.addWidget(self._onoff)

        layout = QVBoxLayout(self)
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row3)

        # 信号
        self._fx_combo.currentTextChanged.connect(self.fx_changed.emit)
        self._ch_1.clicked.connect(lambda: self._select_channel("1"))
        self._ch_2.clicked.connect(lambda: self._select_channel("2"))
        self._ch_both.clicked.connect(lambda: self._select_channel("both"))
        self._beats_minus.clicked.connect(self._beats_delta)
        self._beats_plus.clicked.connect(self._beats_delta)
        self._depth.valueChanged.connect(lambda v: self.depth_changed.emit(v / 100.0))
        self._onoff.toggled.connect(self.onoff_changed.emit)
        self._bpm_auto.clicked.connect(self.bpm_auto.emit)
        self._bpm_tap_btn.clicked.connect(self.bpm_tap.emit)
        self._beats = 1

    def _select_channel(self, ch: str) -> None:
        # 通道互斥选择 + 发信号
        for b, c in ((self._ch_1, "1"), (self._ch_2, "2"), (self._ch_both, "both")):
            b.setChecked(c == ch)
        self.channel_changed.emit(ch)

    def _beats_delta(self) -> None:
        # 拍数 ±（1-32，循环 1/2/4/8/16/32 阶梯）
        ladder = [1, 2, 4, 8, 16, 32]
        idx = ladder.index(self._beats) if self._beats in ladder else 0
        idx = (idx + 1) if self.sender() is self._beats_plus else (idx - 1)
        self._beats = ladder[idx % len(ladder)]
        self._beats_label.setText(f"{self._beats} 拍")
        self.beats_changed.emit(self._beats)

    def set_beats(self, beats: int) -> None:
        # 外部设置拍数（BPM Auto 联动）
        self._beats = max(1, min(32, beats))
        self._beats_label.setText(f"{self._beats} 拍")


# ===== ui/beat_fx_widget.py 模块说明 =====
# 模块级常量：
#   FX_TYPES：效果库（HPF/LPF/Trans/Echo/Delay，与 E1.8 引擎对应）
# 类型：
#   BeatFxWidget(QWidget)：Beat FX 面板
# 信号：
#   fx_changed / channel_changed / beats_changed / depth_changed / onoff_changed /
#   bpm_tap / bpm_auto：全部信号驱动（MainWindow 接引擎）
# 方法：
#   _select_channel(ch)：通道互斥
#   _beats_delta()：拍数阶梯 ±（1/2/4/8/16/32）
#   set_beats(beats)：外部同步（BPM Auto）
# 设计理由：B13-5 六部件（通道/选择/拍数±/深度/开关 + BPM Auto-Tap 为 SHIFT 语义独立化）
# 关联配置：无

# 打碟机控件：信息显示 + 传输控制按钮 + Pitch 滑块 + Keyloop 开关（D4.2）
# 原则：控件只发 Qt 信号，不直接碰引擎（MainWindow 连接信号到引擎方法，B1 纪律）

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ui.waveform_widget import WaveformWidget
from ui.widgets.glow_button import GlowButton

# 静态配置解包（配色 token，G2.2）
from config.static.static_config import get_static_config

_UI = get_static_config().ui


class DeckWidget(QWidget):
    # 打碟机控件：标题（曲名/BPM/调性）+ 波形 + 播放/CUE/循环按钮 + Pitch/Keylock
    play_clicked = Signal()
    cue_clicked = Signal()
    loop_toggled = Signal(bool)
    beatloop_clicked = Signal(int)
    keylock_toggled = Signal(bool)
    pitch_changed = Signal(float)  # 百分比（-8..8）

    def __init__(self, name: str = "DECK", parent=None):
        # 初始化控件树：信息标签 / 波形 / 控制行 / Pitch 滑块
        super().__init__(parent)
        self.deck_name = name

        self._info_label = QLabel(f"{name}: 未加载")
        self._progress_label = QLabel("0:00 / 0:00")

        self.waveform = WaveformWidget()

        self._play_btn = GlowButton("播放")
        self._cue_btn = GlowButton("CUE")
        self._loop_btn = GlowButton("循环")
        self._loop_btn.setCheckable(True)
        self._beatloop_btn = GlowButton("Beatloop 4")
        self._keylock_cb = GlowButton("Keylock")
        self._keylock_cb.setCheckable(True)

        self._pitch_slider = QSlider(Qt.Horizontal)
        self._pitch_slider.setRange(-8, 8)
        self._pitch_slider.setValue(0)
        self._pitch_label = QLabel("Pitch 0%")

        controls = QHBoxLayout()
        controls.addWidget(self._play_btn)
        controls.addWidget(self._cue_btn)
        controls.addWidget(self._loop_btn)
        controls.addWidget(self._beatloop_btn)
        controls.addWidget(self._keylock_cb)

        pitch_row = QHBoxLayout()
        pitch_row.addWidget(QLabel("Pitch"))
        pitch_row.addWidget(self._pitch_slider, 1)
        pitch_row.addWidget(self._pitch_label)

        layout = QVBoxLayout(self)
        layout.addWidget(self._info_label)
        layout.addWidget(self.waveform, 1)
        layout.addWidget(self._progress_label)
        layout.addLayout(controls)
        layout.addLayout(pitch_row)

        # 信号转发（UI 只发指令）
        self._play_btn.clicked.connect(self.play_clicked.emit)
        self._cue_btn.clicked.connect(self.cue_clicked.emit)
        self._loop_btn.toggled.connect(self.loop_toggled.emit)
        self._beatloop_btn.clicked.connect(lambda: self.beatloop_clicked.emit(4))
        self._keylock_cb.toggled.connect(self.keylock_toggled.emit)
        self._pitch_slider.valueChanged.connect(self._on_pitch_changed)

    # --- 状态更新（MainWindow 定时器/加载回调调用） ---

    def set_track(
        self, path: str, bpm: float, key: str, audio: np.ndarray | None
    ) -> None:
        # 载入曲目：更新信息标签与波形（G3.5：Path 顶层导入）
        name = Path(path).name if path else "未加载"
        bpm_str = f"{bpm:.1f}" if bpm and bpm > 0 else "---"
        self._info_label.setText(f"{self.deck_name}: {name}  |  {bpm_str} BPM  {key}")
        self.waveform.set_audio(audio)

    def update_progress(self, position: int, duration: int) -> None:
        # 刷新进度文本与波形播放头（100ms 定时器）
        self.waveform.set_position(position)
        cur = f"{position // 44100 // 60}:{position // 44100 % 60:02d}"
        tot = f"{duration // 44100 // 60}:{duration // 44100 % 60:02d}"
        self._progress_label.setText(f"{cur} / {tot}")

    def set_playing_state(self, is_playing: bool) -> None:
        # 播放状态按钮文案与 LED（播放=橙色背光；G2.2 配色 token）
        self._play_btn.setText("暂停" if is_playing else "播放")
        self._play_btn.set_led(is_playing, _UI.get("glow_orange", "#ff7a2f"))

    def _on_pitch_changed(self, value: int) -> None:
        # Pitch 滑块变化：更新标签并发信号（百分比）
        self._pitch_label.setText(f"Pitch {value:+d}%")
        self.pitch_changed.emit(float(value))


# ===== ui/deck_widget.py 模块说明 =====
# 类型：
#   DeckWidget(QWidget)：打碟机控件（deck_name 标识 A/B）
# 信号：
#   play_clicked / cue_clicked / loop_toggled(bool) / beatloop_clicked(int) /
#   keylock_toggled(bool) / pitch_changed(float)：UI 只发指令（引擎由 MainWindow 连接）
# 方法：
#   set_track(path, bpm, key, audio)：信息 + 波形更新
#   update_progress(position, duration)：进度文本 + 播放头（44100 采样率硬编码换算，
#     引擎约定固定 44100；M:SS 显示）
#   set_playing_state(is_playing)：按钮文案切换
# 设计理由：控件零引擎依赖（信号解耦，B1"UI 只发指令"）；Pitch 用整数百分比滑块
# 关联配置：无（颜色在 waveform 内部）

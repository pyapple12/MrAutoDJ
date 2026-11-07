# 打碟机控件：信息显示 + 传输控制按钮 + Pitch 滑块 + Keyloop 开关（D4.2）
# 原则：控件只发 Qt 信号，不直接碰引擎（MainWindow 连接信号到引擎方法，B1 纪律）

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ui.waveform_widget import WaveformWidget
from ui.widgets.fader_slider import FaderSlider
from ui.widgets.glow_button import GlowButton

# 静态配置解包（配色 token + 采样率换算基准，H0.6）
from config.static.static_config import get_static_config

_UI = get_static_config().ui
_SR = int(get_static_config().base.get("sample_rate", 44100))


class DeckWidget(QWidget):
    # 打碟机控件：标题（曲名/BPM/调性）+ 波形 + 播放/CUE/循环按钮 + Pitch/Keylock
    # + 循环键行（IN/OUT/4BEAT/◀▶）+ Beat Sync（J1.0）
    play_clicked = Signal()
    cue_clicked = Signal()
    loop_toggled = Signal(bool)
    beatloop_clicked = Signal(int)
    keylock_toggled = Signal(bool)
    pitch_changed = Signal(float)  # 百分比（域随 TEMPO 量程动态 ±6/±16/WIDE——FIX005.18 注释对齐）
    loop_in_clicked = Signal()  # J1.0：循环入点
    loop_out_clicked = Signal()  # J1.0：循环出点
    loop_fourbeat_clicked = Signal()  # J1.0：4 拍自动循环
    loop_halve_clicked = Signal()  # J1.0：循环减半（CALL ◀）
    loop_double_clicked = Signal()  # J1.0：循环加倍（CALL ▶）
    sync_toggled = Signal(bool)  # J1.0：Beat Sync 开关

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
        # J1.1：Keylock 启用（变速不变调，rubberband 后台重渲染；音高保持有
        # 1-2s 渲染延迟，去抖合并连续变化）
        self._keylock_cb.setToolTip("Keylock 变速不变调（rubberband 后台重渲染，约 1-2s）")

        # J1.0：循环键行（IN/OUT/4BEAT + CALL ◀▶ = 减半/加倍）+ Beat Sync
        self._loop_in_btn = GlowButton("IN")
        self._loop_in_btn.setToolTip("循环入点：当前位置为起点（OUT 闭合后激活）")
        self._loop_out_btn = GlowButton("OUT")
        self._loop_out_btn.setToolTip("循环出点：当前位置为终点并激活循环")
        self._loop_4beat_btn = GlowButton("4BEAT")
        self._loop_4beat_btn.setToolTip("从当前位置起 4 拍自动循环")
        self._loop_halve_btn = GlowButton("◀")
        self._loop_halve_btn.setToolTip("循环长度减半")
        self._loop_double_btn = GlowButton("▶")
        self._loop_double_btn.setToolTip("循环长度加倍（钳制曲尾）")
        self._sync_btn = GlowButton("SYNC")
        self._sync_btn.setCheckable(True)
        self._sync_btn.setToolTip("Beat Sync：对齐另一盘的有效 BPM（乐速倍率，可被 TEMPO 推子覆盖）")

        # PL001.12：Pitch 滑块拟物化（QSlider → FaderSlider，量程只读反显语义不变）
        self._pitch_slider = FaderSlider(-8.0, 8.0, 0.0, Qt.Horizontal, length=200)
        self._pitch_label = QLabel("Pitch 0%")
        self._pitch_slider.setToolTip("Pitch 量程指示（实时变速由 TEMPO 推子驱动）")

        controls = QHBoxLayout()
        controls.setSpacing(4)
        controls.addWidget(self._play_btn)
        controls.addWidget(self._cue_btn)
        controls.addWidget(self._loop_btn)
        controls.addWidget(self._beatloop_btn)
        controls.addWidget(self._keylock_cb)

        # J1.0：循环/同步键行
        loop_row = QHBoxLayout()
        loop_row.setSpacing(4)
        loop_row.addWidget(self._loop_in_btn)
        loop_row.addWidget(self._loop_out_btn)
        loop_row.addWidget(self._loop_4beat_btn)
        loop_row.addWidget(self._loop_halve_btn)
        loop_row.addWidget(self._loop_double_btn)
        loop_row.addWidget(self._sync_btn)

        pitch_row = QHBoxLayout()
        pitch_row.addWidget(QLabel("Pitch"))
        pitch_row.addWidget(self._pitch_slider, 1)
        pitch_row.addWidget(self._pitch_label)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.addWidget(self._info_label)
        layout.addWidget(self.waveform, 1)
        layout.addWidget(self._progress_label)
        layout.addLayout(controls)
        layout.addLayout(loop_row)
        layout.addLayout(pitch_row)

        # 信号转发（UI 只发指令）
        self._play_btn.clicked.connect(self.play_clicked.emit)
        self._cue_btn.clicked.connect(self.cue_clicked.emit)
        self._loop_btn.toggled.connect(self.loop_toggled.emit)
        self._beatloop_btn.clicked.connect(lambda: self.beatloop_clicked.emit(4))
        self._keylock_cb.toggled.connect(self.keylock_toggled.emit)
        self._pitch_slider.valueChanged.connect(self._on_pitch_changed)
        self._loop_in_btn.clicked.connect(self.loop_in_clicked.emit)
        self._loop_out_btn.clicked.connect(self.loop_out_clicked.emit)
        self._loop_4beat_btn.clicked.connect(self.loop_fourbeat_clicked.emit)
        self._loop_halve_btn.clicked.connect(self.loop_halve_clicked.emit)
        self._loop_double_btn.clicked.connect(self.loop_double_clicked.emit)
        self._sync_btn.toggled.connect(self.sync_toggled.emit)

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
        # 刷新进度文本与波形播放头（100ms 定时器；H0.6：采样率配置驱动）
        self.waveform.set_position(position)
        cur = f"{position // _SR // 60}:{position // _SR % 60:02d}"
        tot = f"{duration // _SR // 60}:{duration // _SR % 60:02d}"
        self._progress_label.setText(f"{cur} / {tot}")

    def set_playing_state(self, is_playing: bool) -> None:
        # 播放状态按钮文案与 LED（播放=橙色背光；G2.2 配色 token）
        self._play_btn.setText("暂停" if is_playing else "播放")
        self._play_btn.set_led(is_playing, _UI.get("glow_orange", "#ff7a2f"))

    def set_pitch_range(self, percent: float) -> None:
        # Pitch 滑块域随 TEMPO 量程重建（FIX004.18：±6/±16/WIDE 下反显不再
        # 被 ±8 固定域饱和）
        r = max(1.0, abs(float(percent)))
        self._pitch_slider.set_range(-r, r)
        self._pitch_slider.blockSignals(True)
        self._pitch_slider.set_value(0.0)
        self._pitch_slider.blockSignals(False)

    def set_pitch_display(self, percent: float) -> None:
        # Pitch 滑块转为量程指示（J1.1：实时变速由 TEMPO 推子驱动，此滑块只读
        # 反显当前乐速百分比；blockSignals 防回环；域由 set_pitch_range 随量程）
        percent = float(percent)
        self._pitch_slider.blockSignals(True)
        self._pitch_slider.set_value(percent)
        self._pitch_slider.blockSignals(False)
        self._pitch_label.setText(f"Pitch {percent:+.1f}%")

    def set_sync_active(self, on: bool) -> None:
        # 外部同步 SYNC 勾选与灯态（blockSignals 防回环，J1.0：手动 TEMPO 熄灭）
        self._sync_btn.blockSignals(True)
        self._sync_btn.setChecked(on)
        self._sync_btn.blockSignals(False)
        self._sync_btn.set_led(on, _UI.get("glow_blue", "#2f8bff"))

    def _on_pitch_changed(self, value: float) -> None:
        # Pitch 推子变化：更新标签并发信号（PL001.12 起 FaderSlider float 值；
        # 主要作为 TEMPO 只读反显，手动拖动仍发信号由上层决定语义）
        self._pitch_label.setText(f"Pitch {value:+.1f}%")
        self.pitch_changed.emit(float(value))


# ===== ui/deck_widget.py 模块说明 =====
# 类型：
#   DeckWidget(QWidget)：打碟机控件（deck_name 标识 A/B）
# 信号：
#   play_clicked / cue_clicked / loop_toggled(bool) / beatloop_clicked(int) /
#   keylock_toggled(bool) / pitch_changed(float)：UI 只发指令（引擎由 MainWindow 连接）
# 方法：
#   set_track(path, bpm, key, audio)：信息 + 波形更新
#   update_progress(position, duration)：进度文本 + 播放头（H0.6 起采样率
#     由 _SR = base.json sample_rate 换算，M:SS 显示）
#   set_playing_state(is_playing)：按钮文案切换
#   set_pitch_display(percent)：Pitch 量程只读反显（J1.1；PL001.12 起滑块为
#     FaderSlider 拟物件，blockSignals 防回环）
#   set_sync_active(on)：SYNC 勾选与灯态外部同步（J1.0）
# 设计理由：控件零引擎依赖（信号解耦，B1"UI 只发指令"）；Pitch 为 FaderSlider
#   拟物滑块（PL001.12/FIX004.18，量程只读反显随 TEMPO 量程重建）
# 关联配置：config/static/ui.json（glow_orange 播放 LED 色）；
#   config/static/base.json（sample_rate → _SR 进度换算，I3.4 补录）

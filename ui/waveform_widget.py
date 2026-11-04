# 波形控件：离线峰值降采样缓存 + 播放头滚动（D4.3）
# 渲染用 QPainter（深色主题，颜色取 config/static/ui.json）

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from config.static.static_config import get_static_config

# 静态配置解包（波形颜色；I3.5：变量名 _SC.ui → _UI 与其余 UI 模块统一）
_SC = get_static_config()
_UI = _SC.ui
_UI_COLORS = _UI.get("colors", {})


def _build_peaks(audio: np.ndarray, width: int) -> np.ndarray:
    # 双通道峰值降采样：每像素列取 [min, max]（返回 (width, 2) float32）
    if audio is None or len(audio) == 0 or width <= 0:
        return np.zeros((max(1, width), 2), dtype=np.float32)
    n = len(audio)
    # H0.3：1D mono 输入防护（原 np.mean(axis=1) 对 1D 抛 AxisError）
    mono = audio if audio.ndim == 1 else np.mean(audio, axis=1)
    mono = np.asarray(mono, dtype=np.float64)
    if n <= width:
        # 短音频：直接重采样到目标宽度
        idx = np.linspace(0, n - 1, width).astype(int)
        col = mono[idx]
        return np.stack([col, col], axis=1).astype(np.float32)
    per = n // width
    peaks = np.zeros((width, 2), dtype=np.float32)
    for i in range(width):
        seg = mono[i * per : (i + 1) * per]
        peaks[i, 0] = seg.min()
        peaks[i, 1] = seg.max()
    return peaks


class WaveformWidget(QWidget):
    # 波形显示控件：set_audio 计算峰值缓存，set_position 移动播放头（100ms 定时刷新）
    def __init__(self, parent=None):
        # 初始化：峰值缓存空、播放头 0、固定最小高度
        super().__init__(parent)
        self._peaks: np.ndarray = np.zeros((1, 2), dtype=np.float32)
        self._position: int = 0
        self._duration: int = 0
        self.setMinimumHeight(56)

    def set_audio(self, audio: np.ndarray | None) -> None:
        # 载入音频：按当前控件宽度降采样峰值缓存；播放头清零
        self._peaks = _build_peaks(audio, max(1, self.width()))
        self._duration = len(audio) if audio is not None else 0
        self._position = 0
        self.update()

    def set_position(self, samples: int) -> None:
        # 设置播放头位置（样本）；不变不重绘（100ms 定时器高频调用）
        samples = max(0, min(samples, self._duration))
        if samples != self._position:
            self._position = samples
            self.update()

    def paintEvent(self, event) -> None:
        # 绘制：波形中线 + 上下包络 + 播放头竖线；空音频仅画边框
        painter = QPainter(self)
        bg = QColor(str(_UI_COLORS.get("background", "#0d0d0d")))
        fg = QColor(str(_UI_COLORS.get("accent", "#00ff41")))
        painter.fillRect(self.rect(), bg)
        w, h = self.width(), self.height()
        mid = h / 2.0
        n_peaks = len(self._peaks)
        if n_peaks < 2 or self._duration <= 0:
            painter.setPen(QPen(fg, 1))
            painter.drawRect(0, 0, w - 1, h - 1)
            painter.end()
            return
        # 峰值索引 → 像素列
        pen = QPen(fg, 1)
        painter.setPen(pen)
        xs = np.linspace(0, w - 1, n_peaks)
        for i in range(n_peaks):
            x = int(xs[i])
            hi = mid - self._peaks[i, 1] * (mid - 2)
            lo = mid - self._peaks[i, 0] * (mid - 2)
            painter.drawLine(x, int(hi), x, int(lo))
        # 播放头
        if self._duration > 0:
            px = int(self._position / self._duration * (w - 1))
            painter.setPen(QPen(QColor(str(_UI_COLORS.get("deck_a", "#00cccc"))), 2))
            painter.drawLine(px, 0, px, h - 1)
        painter.end()


# ===== ui/waveform_widget.py 模块说明 =====
# 模块级常量：
#   _SC / _UI_COLORS：静态配置（波形颜色，AGENTS.md 参数约定）
# 函数：
#   _build_peaks(audio, width)：mono 直用 / 双通道均值（H0.3 支持 1D 输入）→
#     每像素列 [min,max]（O(width) 峰值缓存，避免每帧全量扫描；短音频线性重采样）
# 类型：
#   WaveformWidget(QWidget)：波形显示（set_audio/set_position/paintEvent）
# 设计理由：峰值缓存一次计算、绘制只扫描缓存（实时线程零依赖）；
#   set_position 仅变化时重绘（100ms 定时器不空转）
# 异常处理：空/None 音频返回零缓存并画边框（不崩溃）
# 关联配置：config/static/ui.json（colors.background/accent/deck_a）

# 性能打击垫组件：1×8 网格 + 模式切换（FLX4 8 种 Pad 模式中的 5 种可软件实现）
# 参考：w.study.md B13-3.12（Pad）/ 3.8-3.11（模式键）、MZH-Pad Modes

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# 可软件实现的 Pad 模式（FLX4 模式键：HOT CUE / PAD FX1 / PAD FX2 / BEAT JUMP /
# SAMPLER / KEYBOARD / BEAT LOOP / KEY SHIFT；此处取核心 5 种）
PAD_MODES = ["Hot Cue", "Beat Loop", "Beat Jump", "Sampler", "Key Shift"]


class PadWidget(QWidget):
    # 打击垫组件：1×8 网格 + 模式切换行；灯态由 set_pad_light 驱动
    pad_clicked = Signal(int, str)  # (pad 序号 0-7, 当前模式)
    mode_changed = Signal(str)

    def __init__(self, parent=None):
        # 初始化：8 个可勾选按钮 + 5 个模式键
        super().__init__(parent)
        self._mode = "Hot Cue"
        self._pad_buttons = []

        pads = QGridLayout()
        for i in range(8):
            btn = QPushButton(f"P{i + 1}")
            btn.setCheckable(True)
            btn.setFixedSize(44, 44)
            btn.clicked.connect(
                lambda checked, idx=i: self.pad_clicked.emit(idx, self._mode)
            )
            pads.addWidget(btn, 0, i)
            self._pad_buttons.append(btn)

        modes = QHBoxLayout()
        modes.addWidget(QLabel("模式"))
        self._mode_buttons = {}
        for name in PAD_MODES:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=name: self._select_mode(m))
            modes.addWidget(btn)
            self._mode_buttons[name] = btn
        self._mode_buttons["Hot Cue"].setChecked(True)

        layout = QVBoxLayout(self)
        layout.addLayout(pads)
        layout.addLayout(modes)

    # --- 模式 ---

    def _select_mode(self, mode: str) -> None:
        # 切换模式：互斥勾选 + 清 pad 灯态 + 发信号
        self._mode = mode
        for name, btn in self._mode_buttons.items():
            btn.setChecked(name == mode)
        self.clear_pad_lights()
        self.mode_changed.emit(mode)

    @property
    def mode(self) -> str:
        # 当前模式（UI/引擎映射用）
        return self._mode

    # --- 灯态（E2.7） ---

    def set_pad_light(self, idx: int, on: bool) -> None:
        # 设置 pad 灯态（按钮勾选态驱动高亮样式；越界忽略）
        if 0 <= idx < 8:
            self._pad_buttons[idx].setChecked(on)

    def clear_pad_lights(self) -> None:
        # 清空全部 pad 灯（模式切换时调用）
        for btn in self._pad_buttons:
            btn.setChecked(False)

    def pad_light(self, idx: int) -> bool:
        # 查询 pad 灯态（引擎状态同步用）
        return 0 <= idx < 8 and self._pad_buttons[idx].isChecked()


# ===== ui/pad_widget.py 模块说明 =====
# 模块级常量：
#   PAD_MODES：可软件实现的 5 种 Pad 模式（Hot Cue/Beat Loop/Beat Jump/Sampler/Key Shift）
# 类型：
#   PadWidget(QWidget)：打击垫组件
# 信号：
#   pad_clicked(idx, mode)：pad 按下（携带当前模式）
#   mode_changed(mode)：模式切换
# 方法：
#   _select_mode(mode)：互斥切换 + 清灯 + 发信号
#   set_pad_light/clear_pad_lights/pad_light：灯态管理（E2.7 LED 联动）
# 设计理由：组件零引擎依赖（信号解耦，MainWindow 接线）；
#   灯态用 QPushButton 勾选态驱动（QSS :checked 高亮）
# 关联配置：无

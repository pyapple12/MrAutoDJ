# 主窗口：曲库（搜索/表格）+ 双打碟机 + 混音台（EQ×2/横推/主音量）+ 转场（D4）
# 引擎可注入（无头测试传 fake）；100ms 定时器刷新进度；分析在后台线程 + 信号回填

from __future__ import annotations

import os
import threading
import time as _time
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.static.static_config import get_static_config
from modules import analyzer as analyzer_mod
from modules.engine import AudioEngine, EQ_GAIN_DB, JOG_BEND_MAX, SLOT_COUNT, State
from modules import library as library_mod
from modules.automix import AutomixController
from modules.stretcher import rubberband_available
from modules.transition import tempo_compatible
from modules.transition_manager import DEFAULT_FADE_SECONDS, TransitionManager
from ui.beat_fx_widget import BEAT_LADDER, BeatFxWidget
from ui.deck_widget import DeckWidget
from ui.jog_wheel import JogWheel
from ui.pad_widget import PadWidget
from ui import palette
from ui.scale import s
from ui.themes import switch_theme  # FIX004/②-9：顶层导入（原 _cycle_theme 函数内）
from ui.shift_state import ShiftState
from ui.widgets.fader_slider import FaderSlider
from ui.widgets.glow_button import GlowButton
from ui.widgets.led_strip import LedStrip
from ui.widgets.mini_display import MiniDisplay
from ui.widgets.panel_frame import CONTENT_TOP_MARGIN, PanelFrame
from ui.widgets.rotary_knob import RotaryKnob
from utils.logger import get_logger

# 静态配置解包（窗口尺寸，AGENTS.md 参数约定）
_SC = get_static_config()
_UI = _SC.ui  # 静态配置解包（窗口尺寸/配色 token）
_logger = get_logger(__name__)

# 间距网格与部件尺寸（J0.1/J0.3：4/8/12 三级网格 + 大小分级，ui.json 驱动；
# J4：全部经 ui.scale 乘全局缩放因子；PL001.1 起 main 列宽 = mins+shares 机制，
# _MAIN_PCTS 百分比键退役，改 splitter_main_mins/splitter_main_shares）
_SP_SM = s(int(_UI.get("spacing_sm", 4)))
_SP_MD = s(int(_UI.get("spacing_md", 8)))
_SP_LG = s(int(_UI.get("spacing_lg", 12)))
# FIX004.16：旋钮尺寸基准裸值（RotaryKnob 构造内统一 s()——原调用点再 s()
# 致 ui_scale≠1 时双重放大）
_KNOB_MIXER = int(_UI.get("knob_size_mixer", 32))
_KNOB_FX = int(_UI.get("knob_size_fx", 28))
_LIB_PCT = int(_UI.get("splitter_library_pct", 18))


def _on_analysis_result(window, path: str, record, error, epoch: int = -1) -> None:
    # 分析 worker 回调（H3.2：原 load_library 内嵌套闭包提升为模块级函数）：
    # 经 Qt 信号回主线程回填（错误曲目降级空记录）
    # I3.6 防御：窗口已关闭 → C++ 对象已删，emit 崩溃（静默丢弃）；
    # epoch 与当前曲库代次不一致 → 换文件夹后的旧 worker 结果（不回填混库）
    if getattr(window, "_closing", False):
        return
    if epoch >= 0 and epoch != window._library_epoch:
        return
    if error is not None:
        _logger.warning("分析失败 %s: %s", path, error)
    window.analysis_ready.emit(path, record or analyzer_mod.empty_record())


class MainWindow(QMainWindow):
    # 主窗口：引擎注入（默认创建真实引擎）、曲库、双盘、混音台、转场编排
    # 跨线程信号：分析结果回填（str=path, object=record）；状态消息（str）
    analysis_ready = Signal(str, object)
    status_message = Signal(str)

    def __init__(self, engine: AudioEngine | None = None):
        # 初始化：引擎/转场管理器/曲库状态/控件树/定时器
        super().__init__()
        self._engine = engine or AudioEngine()
        self._tm = TransitionManager(self._engine)
        # M2 自动编排桥（PL002.9：曲库/当前盘元数据经 getter 注入，late-bind）
        self._automix = AutomixController(
            self._tm,
            entries_getter=lambda: self._library,
            now_meta_getter=lambda: self._deck_meta[self._target],
        )
        # 跨线程信号连接（worker 线程 emit → 主线程槽）
        self.analysis_ready.connect(self._append_row_safe)
        self.status_message.connect(self._status)
        # 目标盘（双击加载/转场作用对象）：'a' 或 'b'
        self._target = "a"
        # 每盘元数据：{path, bpm, key, downbeats}
        self._deck_meta = {"a": {}, "b": {}}
        self._library: list = []  # [{path, bpm, key, energy, record}]
        # 曲库代次（I3.6：换文件夹 +1，旧分析线程结果按 epoch 丢弃防混库）
        self._library_epoch = 0
        # 关闭标记（I3.6：closeEvent 置位，分析 worker 回调前检查防 emit 已删对象）
        self._closing = False
        # --- E2 状态 ---
        self._shift = ShiftState(self)
        # Instant Doubles：上次加载 (path, time)；500ms 内同路径再次加载 → 复制到另一盘
        self._last_load = (None, 0.0)
        # 表演键状态（LED 刷新用）
        self._slip_btns: dict = {}
        self._censor_btns: dict = {}
        # Beat FX 目标盘配置（E2.4 面板 → 引擎）
        self._beat_fx_effect: str = ""
        self._beat_fx_depth: float = 0.0
        # --- J1.0/J1.1 TEMPO/Sync/FX 通道/监听状态 ---
        self._tempo_ranges = [
            int(x) for x in (_SC.base.get("tempo_ranges") or [6, 10, 16, 100])
        ]
        self._tempo_range = {"a": self._tempo_ranges[0], "b": self._tempo_ranges[0]}
        self._sync_on = {"a": False, "b": False}
        self._fx_channel = "1"  # CH1/CH2/both
        self._fx_beats = 4
        self._cue_active: str | None = None  # 当前监听盘
        # 弯音脉冲归零（P2 修复）：每盘 pending 值 + 单发定时器（超时调 jog_bend(0)）
        self._bend_pending: dict = {"a": 0.0, "b": 0.0}
        self._bend_timers: dict = {}
        # Mix 装填的来曲 entry（FIX004.2：mix 完成时经 _tick 滚动 _deck_meta；
        # FIX005.6：按盘键控——单槽在双盘先后 mix 时错配滚动）
        self._pending_entry: dict = {"a": None, "b": None}
        for _letter in ("a", "b"):
            _t = QTimer(self)
            _t.setSingleShot(True)
            _t.setInterval(int(_UI.get("jog_bend_reset_ms", 80)))
            _t.timeout.connect(lambda l=_letter: self._on_bend_timeout(l))
            self._bend_timers[_letter] = _t

        self.setWindowTitle(f"MrAutoDJ {_SC.base.get('version', '')}")  # J0.8：标题带版本
        w = int(_SC.base.get("window_width", 1280))
        h = int(_SC.base.get("window_height", 800))
        self._win_w = w
        self.resize(w, h)

        self._build_ui()
        self._connect_signals()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(100)  # 100ms 刷新进度/播放头

    # --- UI 构建 ---

    def _build_ui(self) -> None:
        # 构建控件树：FLX4 布局（F6 重构，I3.4 注释失实修正）——
        # Browse 顶部条 + 五列视图：曲库 | 主区四列（Deck A | Mixer | Deck B | Effects）
        # 每区 PanelFrame 深色面板包裹（对齐参考图）
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(_SP_MD, _SP_MD, _SP_MD, _SP_MD)
        root.setSpacing(_SP_MD)

        # --- Browse 区（顶部面板，J0.2：LOAD 组 / 搜索组 / 状态组 + Tooltip） ---
        browse_panel = PanelFrame("BROWSE")
        browse = QHBoxLayout(browse_panel)
        browse.setContentsMargins(_SP_LG, CONTENT_TOP_MARGIN, _SP_LG, _SP_MD)  # PATCH001.1 标题占位
        browse.setSpacing(_SP_SM)
        self._load_a_btn = GlowButton("LOAD A")
        self._load_a_btn.set_led(True, _UI.get("glow_orange", "#ff7a2f"))
        self._load_b_btn = GlowButton("LOAD B")
        self._load_b_btn.set_led(True, _UI.get("glow_orange", "#ff7a2f"))
        self._load_a_btn.setToolTip("加载选中曲目到 DECK A")
        self._load_b_btn.setToolTip("加载选中曲目到 DECK B")
        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索曲库...")
        self._search.setToolTip("输入关键字过滤曲库（Ctrl+F 聚焦）")
        self._open_btn = GlowButton("打开文件夹")
        self._open_btn.setToolTip("选择音乐文件夹并加载曲库（后台分析，失败曲目降级）")
        self._target_btn = GlowButton("目标盘: A")
        self._target_btn.setToolTip("双击曲库与 Beat FX 的作用盘；空格 = 播放/暂停目标盘")
        # E2.1 全局 SHIFT 按钮（也可用键盘 SHIFT）
        self._shift_btn = GlowButton("SHIFT")
        self._shift_btn.setCheckable(True)
        self._shift_btn.setToolTip("全局 SHIFT：按住（键盘或点按）解锁控件第二功能")
        browse.addWidget(self._load_a_btn)
        browse.addWidget(self._load_b_btn)
        browse.addSpacing(_SP_MD)
        browse.addWidget(self._search, 1)
        browse.addSpacing(_SP_MD)
        browse.addWidget(self._open_btn)
        browse.addWidget(self._target_btn)
        browse.addWidget(self._shift_btn)
        root.addWidget(browse_panel)

        # --- 主体：曲库 | 主区四列（Deck A | Mixer | Deck B | Effects） ---
        body = QSplitter(Qt.Horizontal)
        # 曲库面板
        lib_panel = PanelFrame("LIBRARY")
        lib_box = QVBoxLayout(lib_panel)
        lib_box.setContentsMargins(8, CONTENT_TOP_MARGIN, 8, 8)  # PATCH001.1 标题占位
        self._table_headers = _UI.get(
            "table_headers", ["状态", "曲名", "BPM", "调性", "能量"]
        )
        self._table = QTableWidget(0, len(self._table_headers))
        self._table.setHorizontalHeaderLabels(self._table_headers)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        # PATCH002.1：曲名列 Stretch 弹性（取代 stretchLastSection——能量列
        # 定宽不再被表格宽重排），其余列 Interactive 定宽
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        # PATCH001.2：定宽四列（曲名走 stretchLastSection 弹性）——280px 最小
        # 库列下五列全部可见（原默认宽 100×5 裁掉调性/能量）
        for col, width in ((0, 40), (2, 60), (3, 64), (4, 48)):
            self._table.setColumnWidth(col, width)
        # PATCH002.1（方案修订）：空态引导句与表格互斥可见——原 QStackedWidget
        # 方案改变库面板布局行为（表格超宽、列宽漂移）已回退；hint 沉底改居中
        # 大字（AlignCenter + 14px），空态时表格隐藏、hint 独占面板居中
        self._lib_hint = QLabel("打开文件夹加载曲库 · 双击曲目载入到目标盘")
        self._lib_hint.setAlignment(Qt.AlignCenter)
        self._lib_hint.setWordWrap(True)
        self._lib_hint.setMaximumWidth(272)  # PATCH002.1：限宽防长文本撑宽库面板
        self._lib_hint.setStyleSheet(
            palette.silk_label_style("font-size: 14px; ")
        )
        lib_box.addWidget(self._table)
        lib_box.addWidget(self._lib_hint)
        body.addWidget(lib_panel)

        # 双打碟机（含 E2 组件：Jog / Pad / 表演键；G3.5 导入上移顶层；
        # FIX005/P3-13：播放头色按盘注入——原双盘恒 deck_a 青）
        self.deck_widget_a = DeckWidget("DECK A")
        self.deck_widget_a.waveform.set_playhead_key("deck_a")
        self.deck_widget_b = DeckWidget("DECK B")
        self.deck_widget_b.waveform.set_playhead_key("deck_b")
        self.jog_a = JogWheel()
        self.jog_b = JogWheel()
        self.jog_a.set_shift_state(self._shift)
        self.jog_b.set_shift_state(self._shift)
        self.pad_a = PadWidget()
        self.pad_b = PadWidget()
        # 表演键（E2.8）：Slip / Censor / Stutter
        self._slip_btns["a"] = self._add_perf_key("Slip")
        self._censor_btns["a"] = self._add_perf_key("Censor")
        self._stutter_btns = {}
        self._stutter_btns["a"] = self._add_perf_key("Stutter")
        self._slip_btns["b"] = self._add_perf_key("Slip")
        self._censor_btns["b"] = self._add_perf_key("Censor")
        self._stutter_btns["b"] = self._add_perf_key("Stutter")

        # 主区四列
        main = QSplitter(Qt.Horizontal)
        main.addWidget(
            self._build_deck_panel(
                "a",
                "DECK A",
                self.deck_widget_a,
                self.jog_a,
                self.pad_a,
                self._slip_btns["a"],
                self._censor_btns["a"],
                self._stutter_btns["a"],
            )
        )
        main.addWidget(self._build_mixer_panel())
        main.addWidget(
            self._build_deck_panel(
                "b",
                "DECK B",
                self.deck_widget_b,
                self.jog_b,
                self.pad_b,
                self._slip_btns["b"],
                self._censor_btns["b"],
                self._stutter_btns["b"],
            )
        )
        main.addWidget(self._build_effects_panel())
        body.addWidget(main)
        # J0.1：比例进 ui.json + stretch 因子（曲库/Mixer/FX 定比、双 Deck 均分拉伸）
        body.setChildrenCollapsible(False)
        main.setChildrenCollapsible(False)
        # PL001.1：列宽下限（五列最小宽总和 1270 ≤ 主区可用 1276@1600 窗——
        # Pad 全宽化后 deck 395 / mixer 200 / effects 280）
        lib_panel.setMinimumWidth(280)
        self._main_mins = [int(v) for v in _UI.get("splitter_main_mins", [395, 200, 395, 280])]
        self._main_shares = [float(v) for v in _UI.get("splitter_main_shares", [0.375, 0.10, 0.375, 0.15])]
        main.widget(0).setMinimumWidth(self._main_mins[0])
        main.widget(1).setMinimumWidth(self._main_mins[1])
        main.widget(2).setMinimumWidth(self._main_mins[2])
        main.widget(3).setMinimumWidth(self._main_mins[3])
        self._splitter_body = body
        self._splitter_main = main
        self._apply_splitter_sizes()
        QTimer.singleShot(0, self._apply_splitter_sizes)  # show 后重申比例
        body.setStretchFactor(0, 0)
        body.setStretchFactor(1, 1)
        main.setStretchFactor(0, 1)
        main.setStretchFactor(1, 0)
        main.setStretchFactor(2, 1)
        main.setStretchFactor(3, 0)
        root.addWidget(body, 3)

        # J0.8：Browse 行 Tab 顺序
        for a, b in (
            (self._load_a_btn, self._load_b_btn),
            (self._load_b_btn, self._search),
            (self._search, self._open_btn),
            (self._open_btn, self._target_btn),
            (self._target_btn, self._shift_btn),
        ):
            QWidget.setTabOrder(a, b)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        self._update_lib_hint()
        self._status("就绪")

    def _apply_splitter_sizes(self) -> None:
        # PL001.1：确定性两级 splitter 尺寸（构造时与 show 后各执行一次）。
        # body = 库列窗宽百分比；main = **各列最小宽 + 富余按份额分配**
        # （原按窗宽百分比的 setSizes 总和 > 主区宽，被 QSplitter 等比压缩 +
        # 最小宽钳制，列宽失真且不可预测；mins+shares 任何窗宽下全列 ≥ min）
        w = max(self.width(), 1)
        self._splitter_body.setSizes(
            [int(w * _LIB_PCT / 100), int(w * (100 - _LIB_PCT) / 100)]
        )
        mw = max(self._splitter_main.width(), 1)
        extra = max(0, mw - sum(self._main_mins))
        self._splitter_main.setSizes(
            [m + int(extra * sh) for m, sh in zip(self._main_mins, self._main_shares)]
        )

    def _update_lib_hint(self) -> None:
        # PL001.13 + PATCH002.1：空库显示居中引导句（表格隐藏），有数据反向
        empty = self._table.rowCount() == 0
        self._table.setVisible(not empty)
        self._lib_hint.setVisible(empty)

    def _refresh_lib_hint_style(self) -> None:
        # FIX004.17：主题切换后引导句样式随 palette 重设
        self._lib_hint.setStyleSheet(palette.silk_label_style("font-size: 12px; "))

    def _on_theme_bus_changed(self, _name: str) -> None:
        # 主题总线槽（FIX005.17：命名槽替代 lambda；关窗后广播早退）
        if self._closing:
            return
        self._refresh_lib_hint_style()

    def _build_deck_panel(
        self, letter: str, name: str, wdg, jog, pad, slip, censor, stut
    ) -> QWidget:
        # 构建单盘面板：DeckWidget（信息/波形/控制/Pitch）+ Jog/TEMPO 行 +
        # 全宽 Pad 行（含模式键）+ 表演键行
        # （PL001.1 改版：8×42 Pad 网格须 ~380px 行宽，与 Jog 同行在五列布局的
        # Deck 列宽（≥400）下结构性放不下——Pad 移至 Jog 行下方全宽，FLX4 同为
        # Pad 区独立于转盘区的行分布）
        panel = PanelFrame(name)
        box = QVBoxLayout(panel)
        box.setContentsMargins(_SP_MD, CONTENT_TOP_MARGIN, _SP_MD, _SP_MD)  # PATCH001.1
        box.setSpacing(_SP_SM)
        box.addWidget(wdg, 1)
        # 上排：Jog + TEMPO 竖置位（实时变速 + 量程循环；Pitch 滑块只读反显）
        top = QHBoxLayout()
        top.setSpacing(_SP_MD)
        top.addWidget(jog)
        top.addStretch(1)
        tempo_col = QVBoxLayout()
        tempo_col.setSpacing(_SP_SM)
        tempo_col.addWidget(QLabel("TEMPO"), 0, Qt.AlignHCenter)
        tempo = FaderSlider(-1.0, 1.0, 0.0, Qt.Vertical, length=120)  # FIX004.16 基准值（构造内缩放）
        tempo.setToolTip("TEMPO 实时变速（Keylock 开时经重渲染保持音高）")
        setattr(self, f"_tempo_{letter}", tempo)
        range_btn = GlowButton(f"±{self._tempo_range[letter]}%")
        range_btn.setToolTip("切换 TEMPO 量程（±6/±10/±16/WIDE）")
        setattr(self, f"_tempo_range_btn_{letter}", range_btn)
        tempo_col.addWidget(tempo, 0, Qt.AlignHCenter)
        tempo_col.addWidget(range_btn, 0, Qt.AlignHCenter)
        top.addLayout(tempo_col)
        box.addLayout(top)
        # 全宽 Pad 行（含模式键）与表演键行
        box.addWidget(pad)
        krow = QHBoxLayout()
        krow.setSpacing(_SP_SM)
        for k in (slip, censor, stut):
            krow.addWidget(k)
        box.addLayout(krow)
        tempo.valueChanged.connect(lambda v, l=letter: self._on_tempo(l, v))
        range_btn.clicked.connect(lambda l=letter: self._cycle_tempo_range(l))
        self._bind_value_tip(tempo, lambda v, l=letter: self._tempo_tip(l, v))
        return panel

    def _build_mixer_panel(self) -> QWidget:
        # 构建 Mixer 面板：TRIM/EQ 旋钮 + VU/推子/FaderStart/Tap + 横推 + 主音量
        # + 耳机监听区预留（J0.5）
        panel = PanelFrame("MIXER")
        box = QVBoxLayout(panel)
        box.setContentsMargins(_SP_MD, CONTENT_TOP_MARGIN, _SP_MD, _SP_MD)  # PATCH001.1
        box.setSpacing(_SP_MD)
        # 行1：TRIM A/B（J0.3：Mixer 旋钮 32 分级；J0.7：数值 Tooltip）
        row1 = QHBoxLayout()
        row1.setSpacing(_SP_SM)
        row1.addWidget(QLabel("A TRIM"))
        self._trim_a = RotaryKnob(0.0, 2.0, default=1.0, size=_KNOB_MIXER)
        row1.addWidget(self._trim_a)
        row1.addSpacing(_SP_LG)
        row1.addWidget(QLabel("B TRIM"))
        self._trim_b = RotaryKnob(0.0, 2.0, default=1.0, size=_KNOB_MIXER)
        row1.addWidget(self._trim_b)
        row1.addStretch(1)
        box.addLayout(row1)
        self._bind_value_tip(self._trim_a, lambda v: f"TRIM A ×{v:.2f}")
        self._bind_value_tip(self._trim_b, lambda v: f"TRIM B ×{v:.2f}")
        # 行2：EQ A/B（低中高旋钮）
        row2 = QHBoxLayout()
        row2.setSpacing(_SP_LG)
        self._eq_a_sliders = {}
        self._eq_b_sliders = {}
        for title, knobs in (("A", self._eq_a_sliders), ("B", self._eq_b_sliders)):
            col = QVBoxLayout()
            col.setSpacing(_SP_SM)
            col.addWidget(QLabel(f"{title} EQ"))
            for band in ("低", "中", "高"):
                r = QHBoxLayout()
                r.setSpacing(_SP_SM)
                r.addWidget(QLabel(band))
                k = RotaryKnob(-1.0, 1.0, default=0.0, size=_KNOB_MIXER)
                k.setObjectName(f"{title}-{band}")
                r.addWidget(k)
                col.addLayout(r)
                knobs[band] = k
                # J0.7：EQ Tooltip 显示 dB（+1 → +6dB / -1 → -30dB）
                self._bind_value_tip(
                    k,
                    lambda v, b=f"{title}-{band}": (
                        f"{b} EQ {EQ_GAIN_DB[0] * v if v >= 0 else EQ_GAIN_DB[1] * abs(v):+.1f} dB"
                    ),
                )
            row2.addLayout(col)
        row2.addStretch(1)
        box.addLayout(row2)
        # 行3：VU + FaderStart + Tap（A/B 两列）
        row3 = QHBoxLayout()
        row3.setSpacing(_SP_LG)
        for letter in ("a", "b"):
            col = QVBoxLayout()
            col.setSpacing(_SP_SM)
            label = letter.upper()
            col.addWidget(QLabel(f"{label} VU"))
            meter = LedStrip()  # I2.3：段数走 ui.json led_segments
            setattr(self, f"_vu_{letter}", meter)
            col.addWidget(meter)
            fs = GlowButton(f"{label} FS")  # PL001.5：短名防截断（tooltip 全名）
            fs.setCheckable(True)
            fs.setToolTip("Fader Start：开启后推子从 0 推起 = 播放、拉到底 = 停止")
            setattr(self, f"_fs_{letter}", fs)
            col.addWidget(fs)
            tap = GlowButton("TAP")  # PL001.5：短名（A/B 由列上下文区分）
            tap.setToolTip(f"DECK {label} Tap：连续点按测 BPM（取中值），用于无分析数据的曲目")
            setattr(self, f"_tap_{letter}", tap)
            col.addWidget(tap)
            row3.addLayout(col)
        row3.addStretch(1)
        box.addLayout(row3)
        # 行4：横推（水平；PATCH002.3：标签改同行——原独立一行致纵向 panel-void）
        row4 = QHBoxLayout()
        row4.setSpacing(_SP_SM)
        row4.addWidget(QLabel("横推"))
        self._xfader = FaderSlider(-1.0, 1.0, 0.0, Qt.Horizontal, length=140)  # FIX004.16
        self._bind_value_tip(
            self._xfader,
            lambda v: (
                f"横推 L {int((1 - (v + 1) / 2) * 100)}% / R {int((v + 1) / 2 * 100)}%"
            ),
        )
        row4.addWidget(self._xfader, 1)
        box.addLayout(row4)
        # 行5：耳机监听区（J1.0 启用：CUE A/B 独占预听 + 音量；平衡预留双源混音）
        row5 = QHBoxLayout()
        row5.setSpacing(_SP_SM)
        row5.addWidget(QLabel("PHONES"))
        self._phones_cue_a = GlowButton("CA")  # PL001.5：短名防截断
        self._phones_cue_b = GlowButton("CB")
        self._phones_bal = RotaryKnob(-1.0, 1.0, default=0.0, size=_KNOB_FX)
        self._phones_vol = RotaryKnob(0.0, 1.0, default=1.0, size=_KNOB_FX)
        self._phones_cue_a.setToolTip("耳机预听 DECK A（CUE A；再次点击停止；需可用输出设备）")
        self._phones_cue_b.setToolTip("耳机预听 DECK B（CUE B；再次点击停止；需可用输出设备）")
        self._phones_bal.setEnabled(False)
        self._phones_bal.setToolTip("监听平衡（预留：需双源混合监听，v2 接入）")
        self._phones_vol.setToolTip("监听音量")
        row5.addWidget(self._phones_cue_a)
        row5.addWidget(self._phones_cue_b)
        row5.addWidget(self._phones_bal)
        row5.addWidget(self._phones_vol)
        row5.addStretch(1)
        box.addLayout(row5)
        return panel

    def _bind_value_tip(self, wgt, fmt) -> None:
        # J0.7：控件数值实时 Tooltip（hover 显示当前值，变化即更新）
        wgt.setToolTip(fmt(wgt.value()))
        wgt.valueChanged.connect(lambda v: wgt.setToolTip(fmt(v)))

    def _build_effects_panel(self) -> QWidget:
        # 构建 Effects 面板：MASTER 旋钮 + Beat FX + FX 状态小屏 + 转场按钮
        panel = PanelFrame("EFFECTS")
        box = QVBoxLayout(panel)
        box.setContentsMargins(_SP_MD, CONTENT_TOP_MARGIN, _SP_MD, _SP_MD)  # PATCH001.1
        box.setSpacing(_SP_MD)
        self._volume = RotaryKnob(0.0, 2.0, default=1.0, size=_KNOB_MIXER)
        self._bind_value_tip(self._volume, lambda v: f"主音量 ×{v:.2f}")
        master_row = QHBoxLayout()
        master_row.setSpacing(_SP_SM)
        master_row.addWidget(QLabel("MASTER"))
        master_row.addWidget(self._volume)
        master_row.addStretch(1)
        box.addLayout(master_row)
        self._beat_fx = BeatFxWidget()
        box.addWidget(self._beat_fx, 1)
        # J0.7：FX 状态小屏（目标盘 + 效果 + 开关显性化）
        fx_row = QHBoxLayout()
        fx_row.setSpacing(_SP_SM)
        fx_row.addWidget(QLabel("FX 状态"))
        self._fx_status = MiniDisplay()
        self._fx_status.setFixedSize(s(120), s(20))  # FIX005.7：恢复缩放（构造内仅 minimum，setFixedSize 需显式 s()）
        fx_row.addWidget(self._fx_status, 1)
        box.addLayout(fx_row)
        # M2 推荐区（PL002.12）：推荐曲名小屏 + explanation + NEXT 单步 + AUTO 开关
        # （窄列适配：小屏 110 + 按钮短名——effects 内容区 264 内放得下）
        rec_row = QHBoxLayout()
        rec_row.setSpacing(_SP_SM)
        self._rec_display = MiniDisplay()
        self._rec_display.setFixedSize(s(110), s(20))
        self._auto_next_btn = GlowButton("NEXT")
        self._auto_next_btn.setToolTip("Auto Next：按兼容分推荐下一曲并立即 Prepare（单步）")
        self._auto_btn = GlowButton("AUTO")
        self._auto_btn.setCheckable(True)
        self._auto_btn.setToolTip("自动模式：每次 Mix 完成后自动推荐并 Prepare 下一曲；手动装填即退出")
        rec_row.addWidget(QLabel("推荐"))
        rec_row.addWidget(self._rec_display)
        rec_row.addWidget(self._auto_next_btn)
        rec_row.addWidget(self._auto_btn)
        box.addLayout(rec_row)
        self._rec_label = QLabel("")
        self._rec_label.setStyleSheet("font-size: 11px; background: transparent;")
        box.addWidget(self._rec_label)
        # 转场（FLX4 无此部件，保留功能：Prepare/Mix）
        self._prepare_btn = GlowButton("Prepare 来曲")
        self._prepare_btn.setToolTip("以目标盘为当前曲、选中曲为来曲，预渲染变速转场缓冲")
        self._mix_btn = GlowButton("Mix Now")
        self._mix_btn.set_led(True, _UI.get("glow_orange", "#ff7a2f"))
        self._mix_btn.setToolTip("在下一个下拍（或立即）混入已预备的来曲")
        tr_col = QVBoxLayout()
        tr_col.setSpacing(_SP_SM)
        tr_col.addWidget(self._prepare_btn)
        tr_col.addWidget(self._mix_btn)
        box.addLayout(tr_col)
        self._update_fx_status()
        return panel

    def _update_fx_status(self) -> None:
        # FX 状态行刷新（J0.7；J1.1 起显示 FX 通道而非目标盘；效果名大写对齐硬件观感）
        if self._beat_fx.is_on() and self._beat_fx_effect:
            ch = {"1": "A", "2": "B", "both": "A+B"}.get(self._fx_channel, "A")
            text = f"{ch} {self._beat_fx_effect.upper()} ON"
        else:
            text = "-- OFF"
        self._fx_status.set_text(text)

    def _add_perf_key(self, name: str) -> GlowButton:
        # 构建表演功能键（Slip/Censor/Stutter；均为勾选语义）
        btn = GlowButton(name)
        btn.setCheckable(True)
        return btn

    def _connect_signals(self) -> None:
        # 连接信号：按钮/滑块 → 引擎/转场；表格双击 → 加载到目标盘
        self._load_a_btn.clicked.connect(lambda: self._load_selected_to("a"))
        self._load_b_btn.clicked.connect(lambda: self._load_selected_to("b"))
        self._open_btn.clicked.connect(self._open_folder)
        self._target_btn.clicked.connect(self._toggle_target)
        self._search.textChanged.connect(self._filter_table)
        self._table.itemDoubleClicked.connect(self._on_row_double_clicked)
        self._prepare_btn.clicked.connect(self._on_prepare)
        self._mix_btn.clicked.connect(self._on_mix)
        self._xfader.valueChanged.connect(
            lambda v: self._engine.crossfader.set_position(v)
        )
        self._volume.valueChanged.connect(lambda v: self._engine.set_volume(v))
        # E2.1 SHIFT：按钮与键盘共用状态（G3.1：changed 接线到按钮 LED 灯态）
        self._shift_btn.toggled.connect(self._shift.set_active)
        self._shift.changed.connect(
            lambda on: self._shift_btn.set_led(on, _UI.get("glow_blue", "#2f8bff"))
        )
        for deck_letter, widget in (
            ("a", self.deck_widget_a),
            ("b", self.deck_widget_b),
        ):
            deck = getattr(self._engine, f"deck_{deck_letter}")
            widget.play_clicked.connect(lambda d=deck: self._toggle_play(d))
            widget.cue_clicked.connect(lambda d=deck: self._on_cue(d))
            widget.loop_toggled.connect(lambda on, d=deck: d.set_loop(on))
            widget.beatloop_clicked.connect(
                lambda beats, d=deck: self._on_beatloop(d, beats)
            )
            widget.keylock_toggled.connect(lambda on, d=deck: self._on_keylock(d, on))
            widget.pitch_changed.connect(lambda v, d=deck: self._on_pitch(d, v))
            # J1.0 循环键行 + Beat Sync
            widget.loop_in_clicked.connect(lambda d=deck: self._loop_action(d, "in"))
            widget.loop_out_clicked.connect(lambda d=deck: self._loop_action(d, "out"))
            widget.loop_fourbeat_clicked.connect(
                lambda d=deck: self._on_beatloop(d, 4)
            )
            widget.loop_halve_clicked.connect(
                lambda d=deck: self._loop_action(d, "halve")
            )
            widget.loop_double_clicked.connect(
                lambda d=deck: self._loop_action(d, "double")
            )
            widget.sync_toggled.connect(
                lambda on, l=deck_letter: self._on_sync(l, on)
            )
        self._connect_eq(self._eq_a_sliders, self._engine.deck_a)
        self._connect_eq(self._eq_b_sliders, self._engine.deck_b)
        # --- E2 信号接线 ---
        # TRIM / VU / Fader Start / Tap（原语控件 valueChanged 为 float，直接映射）
        self._trim_a.valueChanged.connect(lambda v: self._engine.deck_a.set_pregain(v))
        self._trim_b.valueChanged.connect(lambda v: self._engine.deck_b.set_pregain(v))
        self._fs_a.toggled.connect(self._engine.set_fader_start)
        self._tap_a.clicked.connect(lambda: self._on_tap("a"))
        self._tap_b.clicked.connect(lambda: self._on_tap("b"))
        # Jog（每盘）
        for letter, jog, deck in (
            ("a", self.jog_a, self._engine.deck_a),
            ("b", self.jog_b, self._engine.deck_b),
        ):
            jog.bend_changed.connect(lambda v, l=letter: self._on_bend_release(l, v))
            jog.search_changed.connect(lambda v, d=deck: d.jog_search(v))
            jog.scratch_moved.connect(lambda s, d=deck: d.jog_scratch(s))
            jog.touch_changed.connect(lambda on, d=deck: d.jog_touch(on))
            jog.vinyl_toggled.connect(
                lambda on, letter=letter: self._on_vinyl(letter, on)
            )
        # Pad（每盘）
        for letter, pad, deck in (
            ("a", self.pad_a, self._engine.deck_a),
            ("b", self.pad_b, self._engine.deck_b),
        ):
            pad.pad_clicked.connect(
                lambda idx, mode, d=deck, l=letter: self._on_pad(l, d, idx, mode)
            )
        # Beat FX（J1.1：通道选择 + 拍数 + AUTO/TAP 全接线）
        self._beat_fx.fx_changed.connect(self._on_beat_fx_fx)
        self._beat_fx.depth_changed.connect(self._on_beat_fx_depth)
        self._beat_fx.onoff_changed.connect(self._on_beat_fx_onoff)
        self._beat_fx.channel_changed.connect(self._on_beat_fx_channel)
        self._beat_fx.beats_changed.connect(self._on_beat_fx_beats)
        self._beat_fx.bpm_auto.connect(self._on_fx_auto)
        self._beat_fx.bpm_tap.connect(self._on_fx_tap)
        # 耳机监听（J1.0）
        self._phones_cue_a.clicked.connect(lambda: self._on_cue_preview("a"))
        self._phones_cue_b.clicked.connect(lambda: self._on_cue_preview("b"))
        self._phones_vol.valueChanged.connect(self._on_cue_volume)
        # M2 推荐区接线（PL002.12）
        self._auto_next_btn.clicked.connect(self._on_recommend_and_prepare)
        self._auto_btn.toggled.connect(self._toggle_automix)
        # FIX004.17：主题切换时引导句样式随 palette 重设（内联样式不随 QSS）；
        # FIX005.17：lambda 改命名槽（lambda 强持有主窗且 closeEvent 不断连，
        # 多窗/探针场景广播触碰已删对象）
        palette.bus().changed.connect(self._on_theme_bus_changed)
        # 表演键（E2.8）
        self._slip_btns["a"].toggled.connect(self._engine.deck_a.slip_toggle)
        self._slip_btns["b"].toggled.connect(self._engine.deck_b.slip_toggle)
        self._censor_btns["a"].toggled.connect(self._engine.deck_a.censor)
        self._censor_btns["b"].toggled.connect(self._engine.deck_b.censor)
        for letter, deck in (("a", self._engine.deck_a), ("b", self._engine.deck_b)):
            self._stutter_btns[letter].clicked.connect(deck.stutter)
        # J0.8：Ctrl+F 聚焦搜索框
        focus_search = QShortcut(QKeySequence("Ctrl+F"), self)
        focus_search.activated.connect(self._search.setFocus)
        # J2：Ctrl+T 运行期主题切换（dark/light 循环，全控件刷新无重启）
        cycle_theme = QShortcut(QKeySequence("Ctrl+T"), self)
        cycle_theme.activated.connect(self._cycle_theme)

    def _connect_eq(self, knobs: dict, deck) -> None:
        # 连接一组 EQ 旋钮到指定盘的三频 setter（RotaryKnob float 值直接映射）
        knobs["低"].valueChanged.connect(lambda v: deck.eq.set_low(v))
        knobs["中"].valueChanged.connect(lambda v: deck.eq.set_mid(v))
        knobs["高"].valueChanged.connect(lambda v: deck.eq.set_high(v))

    def _entry_by_path(self, path: str) -> dict | None:
        # 曲库条目查找（H1.2：双击加载与 Instant Doubles 共用，避免重复遍历）
        return next((e for e in self._library if e["path"] == path), None)

    # --- 曲库（D4.4） ---

    def load_library(self, folder: str, records: dict | None = None) -> int:
        # 加载曲库到表格：records 提供时直接使用（无分析）；否则后台 analyze_many
        # 返回文件数；分析结果通过信号回填（UI 线程安全）
        files = analyzer_mod.scan_folder(folder)
        if not files:
            self._status(f"未找到音频文件: {folder}")
            return 0
        self._library = []
        self._table.setRowCount(0)
        self._update_lib_hint()  # PL001.13：清库后引导句回归
        if records is not None:
            for path in files:
                rec = records.get(path) or analyzer_mod.empty_record()
                self._append_row(path, rec)
            self._status(f"曲库加载完成: {len(files)} 首")
            return len(files)

        self._status(f"分析中 {len(files)} 首...")

        # I3.6：代次+1 并随线程携带——连续换文件夹时旧 worker 结果过期丢弃
        self._library_epoch += 1
        epoch = self._library_epoch
        threading.Thread(
            target=analyzer_mod.analyze_many,
            args=(files, lambda p, r, e: _on_analysis_result(self, p, r, e, epoch)),
            kwargs={"with_cues": False},
            daemon=True,
        ).start()
        return len(files)

    def _append_row_safe(self, path: str, rec: dict) -> None:
        # 主线程槽：追加表格行（analyze_many 回调经 QueuedConnection 调用）
        self._append_row(path, rec)

    def _append_row(self, path: str, rec: dict) -> None:
        # 追加一行到表格与曲库列表（条目统一走 library.entry_from——PL002.6：
        # 增加 name/artist/timbre 字段供 automix 消费；兼容标记随当前播放盘 BPM）
        entry = library_mod.entry_from(path, rec)
        bpm = entry["bpm"]
        key = entry["key"]
        energy = entry["energy"]
        now_bpm = self._deck_meta[self._target].get("bpm", 0.0)
        mark = ":)" if tempo_compatible(now_bpm, bpm) else ""
        row = self._table.rowCount()
        self._table.insertRow(row)
        for col, text in enumerate(
            (
                mark,
                entry["name"],
                f"{bpm:.1f}" if bpm > 0 else "---",
                key,
                str(energy),
            )
        ):
            self._table.setItem(row, col, QTableWidgetItem(text))
        self._library.append(entry)
        self._table.item(row, 0).setData(Qt.UserRole, path)
        self._update_lib_hint()  # PL001.13：有行即隐藏引导句

    def _filter_table(self, text: str) -> None:
        # 搜索过滤：隐藏不匹配行（简单包含匹配）
        text = text.strip().lower()
        for row in range(self._table.rowCount()):
            name_item = self._table.item(row, 1)
            visible = not text or (
                name_item is not None and text in name_item.text().lower()
            )
            self._table.setRowHidden(row, not visible)

    @staticmethod
    def _make_deck_meta(entry: dict) -> dict:
        # 曲库条目 → 盘元数据（FIX004.2：Load/Instant Doubles/Mix 完成三入口
        # 统一构造；含 energy/timbre 供 automix 评分）
        return {
            "path": entry["path"],
            "bpm": entry.get("bpm", 0.0),
            "key": entry.get("key", "?"),
            "energy": entry.get("energy", 0),
            "timbre": entry.get("timbre"),
            "downbeats": list(entry.get("record", {}).get("downbeats", [])),
        }

    def _load_track_to(self, letter: str, path: str, entry: dict) -> None:
        # 加载曲目到指定盘（解码+播放+波形+元数据；异常捕获不崩溃）
        try:
            audio = self._engine.load_audio(path)
        except Exception as exc:
            _logger.error("加载失败 %s: %s", path, exc)
            self._status(f"加载失败: {Path(path).name}")
            return
        deck = getattr(self._engine, f"deck_{letter}")
        deck.play(audio)
        deck.set_tempo(entry["bpm"])
        widget = getattr(self, f"deck_widget_{letter}")
        widget.set_track(path, entry["bpm"], entry["key"], audio)
        widget.waveform.set_grid(entry["record"].get("downbeats", []))  # PATCH001.3 下拍网格
        widget.set_playing_state(True)
        self._reset_tempo_ui(letter)  # J1.1：新曲重置 TEMPO/量程反显/Sync
        self._deck_meta[letter] = self._make_deck_meta(entry)  # FIX004.2 三入口统一
        self._pending_entry[letter] = None  # 手动换曲仅清同盘 pending（FIX005.6）
        # PL002.11：手动装填退出自动模式（防双源打架）
        if self._automix.auto_mode:
            self._set_automix_ui(False, quiet=True)
            self._status("手动装填：AUTO 自动模式已退出")
        self._status(f"已加载到 DECK {letter.upper()}: {Path(path).name}")

    def _load_selected_to(self, letter: str) -> None:
        # LOAD A/B 按钮（E3，FLX4 语义）：加载当前选中曲目到指定盘
        row = self._table.currentRow()
        if row < 0:
            self._status("请先选中曲目")
            return
        path_item = self._table.item(row, 0)
        if path_item is None:
            return
        path = path_item.data(Qt.UserRole)
        entry = self._entry_by_path(path)
        if entry is None:
            return
        self._load_track_to(letter, path, entry)

    def _on_row_double_clicked(self, item) -> None:
        # 双击行 → 加载到目标盘（解码 + 播放 + 波形 + 元数据；异常捕获不崩溃）
        # E2.6：500ms 内同路径再次加载 = Instant Doubles（复制到另一盘同位置播放）
        if item is None:
            return
        path_item = self._table.item(item.row(), 0)
        if path_item is None:
            return
        path = path_item.data(Qt.UserRole)
        entry = self._entry_by_path(path)
        if entry is None:
            return

        now = _time.time()
        if self._last_load[0] == path and now - self._last_load[1] < 0.5:
            # Instant Doubles：加载到另一盘（非目标盘）同位置
            other = "b" if self._target == "a" else "a"
            other_deck = getattr(self._engine, f"deck_{other}")
            src_deck = getattr(self._engine, f"deck_{self._target}")
            try:
                audio = self._engine.load_audio(path)
            except Exception as exc:
                _logger.error("加载失败 %s: %s", path, exc)
                return
            other_deck.play(audio)
            other_deck.set_position_samples(
                src_deck.position
            )  # H0.4：公开方法持锁 seek
            other_widget = getattr(self, f"deck_widget_{other}")
            other_widget.set_track(path, entry["bpm"], entry["key"], audio)
            other_widget.waveform.set_grid(entry["record"].get("downbeats", []))  # PATCH001.3
            other_widget.set_playing_state(True)
            self._reset_tempo_ui(other)  # J1.1：Instant Doubles 同样重置 TEMPO 域
            self._deck_meta[other] = self._make_deck_meta(entry)  # FIX004.2 补 energy/timbre
            self._last_load = (None, 0.0)
            # PL002.11：手动装填退出自动模式
            if self._automix.auto_mode:
                self._set_automix_ui(False, quiet=True)
            self._status(f"Instant Doubles → DECK {other.upper()}")
            return
        self._last_load = (path, now)
        self._load_track_to(self._target, path, entry)
        self._tm.mark_stale()

    # --- 打碟机控制（D4.2 信号连接） ---

    def _toggle_play(self, deck) -> None:
        # 播放/暂停切换：暂停标记翻转（play 已在加载时调用）
        deck.pause()

    def _on_cue(self, deck) -> None:
        # CUE 按钮：设置当前播放位置为 CUE 并回到 CUE（先设后回，实现 cue 预听）
        deck.cue_set()
        deck.cue_play()
        self._status(f"CUE 已设置并回到 {deck.cue_seconds:.1f}s")

    def _on_beatloop(self, deck, beats: int) -> None:
        # Beatloop：按当前盘 BPM 设置拍循环（I1.1：BPM 统一读公开 deck.bpm property）
        bpm = deck.bpm
        if bpm > 0:
            deck.set_beatloop(beats, bpm)
            self._status(f"Beatloop {beats} 拍")
        else:
            self._status("当前盘 BPM 未知，无法 Beatloop")

    # --- TEMPO / Keylock / Sync / 循环（J1.0/J1.1） ---

    def _tempo_tip(self, letter: str, v: float) -> str:
        # TEMPO 推子 Tooltip：显示乐速倍率与当前量程下百分比
        pct = self._tempo_range[letter]
        rate = 1.0 + v * pct / 100.0
        return f"TEMPO {letter.upper()} ×{rate:.3f}（{v * pct:+.1f}%）"

    def _on_tempo(self, letter: str, v: float) -> None:
        # TEMPO 推子 → 乐速倍率（J1.1 P4）：Keylock 关=实时变速 / 开=重渲染
        # 不变调；Pitch 滑块只读反显；手动动推子解除该盘 Beat Sync
        rate = 1.0 + v * self._tempo_range[letter] / 100.0
        deck = getattr(self._engine, f"deck_{letter}")
        deck.set_tempo_rate(rate)
        widget = getattr(self, f"deck_widget_{letter}")
        widget.set_pitch_display((rate - 1.0) * 100.0)
        if self._sync_on[letter]:
            self._sync_on[letter] = False
            widget.set_sync_active(False)
            self._status(f"DECK {letter.upper()} Beat Sync 解除（手动 TEMPO）")

    def _cycle_tempo_range(self, letter: str) -> None:
        # TEMPO 量程循环（J1.1：±6/±10/±16/WIDE，WIDE 幅度=配置最后一档）
        ranges = self._tempo_ranges or [6, 10, 16, 100]
        cur = self._tempo_range[letter]
        idx = ranges.index(cur) if cur in ranges else 0
        nxt = ranges[(idx + 1) % len(ranges)]
        self._tempo_range[letter] = nxt
        btn = getattr(self, f"_tempo_range_btn_{letter}")
        btn.setText("WIDE" if nxt >= 100 else f"±{nxt}%")
        # FIX004.18：Pitch 反显域随量程重建（±8 固定域在 ±16/WIDE 下饱和失真）
        widget = getattr(self, f"deck_widget_{letter}")
        widget.set_pitch_range(nxt)
        # 保持当前乐速：滑块位置重映射到新量程（blockSignals 防回环）
        deck = getattr(self._engine, f"deck_{letter}")
        tempo = getattr(self, f"_tempo_{letter}")
        v = max(-1.0, min(1.0, (deck.tempo_rate - 1.0) / (nxt / 100.0)))
        tempo.blockSignals(True)
        tempo.set_value(v)
        tempo.blockSignals(False)
        # FIX005.5：量程切换后回写 Pitch 反显（set_pitch_range 内部清零滑块，
        # 乐速非零时标签/帽位滞留旧值与实际乐速矛盾）
        widget.set_pitch_display((deck.tempo_rate - 1.0) * 100.0)
        self._status(
            f"DECK {letter.upper()} TEMPO 量程 {'WIDE' if nxt >= 100 else f'±{nxt}%'}"
        )

    def _on_keylock(self, deck, on: bool) -> None:
        # Keylock 开关（J1.1 启用）：开 = 乐速变化走 rubberband 重渲染（不变调，
        # 约 1-2s 渲染延迟去抖合并）；关 = 回实时变速（卸载烘焙回原速域）
        deck.set_keylock(on)
        self._status(
            f"Keylock {'开（乐速变化将重渲染保持音高）' if on else '关（实时变速）'}"
        )

    def _on_sync(self, letter: str, on: bool) -> None:
        # Beat Sync（J1.0）：对齐另一盘有效 BPM（乐速倍率钳制当前量程内；
        # 手动动 TEMPO 推子解除）
        other = "b" if letter == "a" else "a"
        other_deck = getattr(self._engine, f"deck_{other}")
        deck = getattr(self._engine, f"deck_{letter}")
        widget = getattr(self, f"deck_widget_{letter}")
        self._sync_on[letter] = on
        widget.set_sync_active(on)
        if not on:
            self._status(f"DECK {letter.upper()} Beat Sync 关")
            return
        target = other_deck.effective_bpm
        my_bpm = deck.bpm
        if my_bpm <= 0 or target <= 0:
            self._sync_on[letter] = False
            widget.set_sync_active(False)
            self._status(f"DECK {letter.upper()} Sync 失败：双方需已知 BPM")
            return
        pct = self._tempo_range[letter] / 100.0
        rate = max(1.0 - pct, min(1.0 + pct, target / my_bpm))
        deck.set_tempo_rate(rate)
        tempo = getattr(self, f"_tempo_{letter}")
        v = max(-1.0, min(1.0, (rate - 1.0) / pct)) if pct else 0.0
        tempo.blockSignals(True)
        tempo.set_value(v)
        tempo.blockSignals(False)
        widget.set_pitch_display((rate - 1.0) * 100.0)
        self._status(
            f"DECK {letter.upper()} Beat Sync：×{rate:.3f}（对齐 {target:.1f} BPM）"
        )

    def _reset_tempo_ui(self, letter: str) -> None:
        # 新曲加载后重置 TEMPO 滑块/Pitch 反显/Sync（引擎 play 已重置乐速域；
        # FIX004.18：Pitch 域随当前量程重建——跨曲换量程后域保持正确）
        tempo = getattr(self, f"_tempo_{letter}")
        tempo.blockSignals(True)
        tempo.set_value(0.0)
        tempo.blockSignals(False)
        widget = getattr(self, f"deck_widget_{letter}")
        widget.set_pitch_range(self._tempo_range[letter])
        widget.set_pitch_display(0.0)
        self._sync_on[letter] = False
        widget.set_sync_active(False)

    def _loop_action(self, deck, action: str) -> None:
        # 循环键分发（J1.0）：in/out/halve/double + 状态提示
        if action == "in":
            deck.loop_in()
            self._status("循环入点已设（OUT 闭合）")
        elif action == "out":
            deck.loop_out()
            self._status(
                "循环已闭合激活" if deck.loop_active else "出点需先设入点且晚于入点"
            )
        elif action == "halve":
            deck.loop_halve()
            self._status("循环长度减半")
        elif action == "double":
            deck.loop_double()
            self._status("循环长度加倍")

    def _on_pitch(self, deck, percent: float) -> None:
        # Pitch 滑块变化（J1.1 起为 TEMPO 只读反显，手动拖动仅提示语义）
        self._status(f"Pitch {percent:+.0f}%（量程指示；实时变速请用 TEMPO 推子）")

    # --- 转场（D3 集成到 UI） ---

    def _on_prepare(self) -> None:
        # Prepare：以目标盘为 now，表格选中行为来曲，走 TransitionManager
        # I3.1：rubberband 前置探测（缺失只提示不阻断——SKIP 直混转场仍可用）
        # PL002.11：手动 Prepare 退出自动模式（防双源打架）
        if self._automix.auto_mode:
            self._set_automix_ui(False, quiet=True)
            self._status("手动 Prepare：AUTO 自动模式已退出")
        if not rubberband_available():
            self._status("⚠ rubberband 未找到：变速转场不可用，仅支持 SKIP 直混")
        row = self._table.currentRow()
        if row < 0:
            self._status("请先选中来曲")
            return
        entry = self._library[row] if row < len(self._library) else None
        if entry is None:
            return
        now_meta = self._deck_meta[self._target]
        if not now_meta.get("path"):
            self._status("目标盘未播放，无法 Prepare")
            return
        now_deck = getattr(self._engine, f"deck_{self._target}")
        ok = self._tm.prepare(
            now_deck,
            now_meta.get("bpm", 0.0),
            now_meta.get("downbeats", []),
            entry["path"],
            entry["bpm"],
            entry["record"].get("downbeats", []),
            cue_seconds=0.0,
            fade_seconds=DEFAULT_FADE_SECONDS,
            on_done=self._on_prepared_done,
        )
        # FIX005.6：仅在守卫通过（prepare 返回 True）后登记 pending——
        # 原守卫判定前置位且不查返回值，拒绝时 pending 滞留
        if ok:
            self._pending_entry[self._target] = entry
            self._status(f"预备中: {Path(entry['path']).name}")
        else:
            self._status(
                "Prepare 被拒（当前盘需 PLAYING 且已知 BPM、无进行中预备）"
            )

    def _on_prepared_done(self, plan, error) -> None:
        # prepare 完成回调（worker 线程；经状态信号回主线程更新）；
        # FIX004/②-3：关窗防护（I3.6 同型——防 emit 已删 C++ 对象）
        if getattr(self, "_closing", False):
            return
        if error is not None:
            self.status_message.emit(f"Prepare 失败: {error}")
            return
        skip = "SKIP" if plan and plan.skip else "STRETCH"
        self.status_message.emit(f"Prepare 完成（{skip}），可 Mix")

    def _on_mix(self) -> None:
        # Mix Now：目标盘混入已预备缓冲（失败提示原因）；AUTO 链式装填改由
        # _tick 的 mix 完成消费驱动（FIX004.3——原 mix_now 置 MIXING 后立即
        # prepare 被 PLAYING 守卫恒拒且静默）
        now_deck = getattr(self._engine, f"deck_{self._target}")
        if self._tm.mix_now(now_deck):
            self._status("Mix 开始")
        else:
            self._status("Mix 被拒：无预备缓冲或状态不允许")

    # --- E2 处理器 ---

    def _on_tap(self, letter: str) -> None:
        # Tap BPM：调用盘 tap 并显示 BPM
        deck = getattr(self._engine, f"deck_{letter}")
        bpm = deck.tap()
        if bpm > 0:
            self._status(f"DECK {letter.upper()} Tap BPM: {bpm:.1f}")

    def _on_bend_release(self, letter: str, v: float) -> None:
        # 弯音累积语义（P2 修复）：每格在 pending 上累加（同向滚动弯得更多，
        # 反向抵消），钳制 ±JOG_BEND_MAX（FIX005/②-8 单源）；重启单发定时器，
        # 超时后 jog_bend(0) 归零
        if abs(v) > 0.01:
            self._bend_pending[letter] = max(
                -JOG_BEND_MAX, min(JOG_BEND_MAX, self._bend_pending[letter] + v)
            )  # FIX004/②-8：单源 engine.JOG_BEND_MAX（原 0.5 字面量双源）
            getattr(self._engine, f"deck_{letter}").jog_bend(self._bend_pending[letter])
            self._bend_timers[letter].start()

    def _on_bend_timeout(self, letter: str) -> None:
        # 弯音定时归零：脉冲结束恢复原速
        getattr(self._engine, f"deck_{letter}").jog_bend(0.0)
        self._bend_pending[letter] = 0.0

    def _on_vinyl(self, letter: str, on: bool) -> None:
        # Vinyl 模式切换提示
        self._status(f"DECK {letter.upper()} Vinyl {'开' if on else '关'}")

    def _on_pad(self, letter: str, deck, idx: int, mode: str) -> None:
        # Pad 按下分发（按模式映射到引擎；SHIFT 时取第二功能）
        shift = self._shift.is_shift()
        if mode == "Hot Cue":
            if shift:
                deck.hot_cue_clear(idx)
            elif deck.hot_cue_state(idx)["has"]:
                deck.hot_cue_play(idx)
            else:
                deck.hot_cue_set(idx)
        elif mode == "Beat Loop":
            if shift:
                deck.set_loop(False)
            else:
                # I1.1：走 _on_beatloop 统一入口（公开 bpm property + BPM 未知提示）
                self._on_beatloop(deck, BEAT_LADDER[idx % len(BEAT_LADDER)])
        elif mode == "Beat Jump":
            step = [1, 2, 4, 8][idx % 4]
            direction = -1 if idx < 4 else 1
            deck.beat_jump(direction * step, align=True)
        elif mode == "Sampler":
            if shift:
                deck.sample_unload(idx)
            elif deck.sample_state(idx)["loaded"]:
                deck.sample_play(idx)
            else:
                self._status(f"采样槽 {idx + 1} 未载入（暂无 UI 装填入口——M3 随电台录音装填）")
        elif mode == "Key Shift":
            # FLX4 语义：Pad1/8 均为复位键（0 半音）→ 未移调时两灯同亮为预期行为
            # （I2.2：slot_count 可配，半音表固定 8 项，越界槽位忽略）
            semitone_table = [0, 1, 2, 3, -3, -2, -1, 0]
            if idx >= len(semitone_table):
                return
            semitones = semitone_table[idx]
            if shift:
                deck.set_key_shift(deck.key_shift + semitones if semitones else 0)
            else:
                deck.set_key_shift(semitones)

    # --- Beat FX 通道/拍数/AUTO/TAP（J1.1 接线） ---

    def _fx_channel_decks(self) -> list:
        # FX 通道 → 目标盘列表（CH1/CH2/1+2，取代原"目标盘"语义）
        return {
            "1": [self._engine.deck_a],
            "2": [self._engine.deck_b],
            "both": [self._engine.deck_a, self._engine.deck_b],
        }.get(self._fx_channel, [self._engine.deck_a])

    def _on_beat_fx_channel(self, ch: str) -> None:
        # FX 通道切换：清旧通道效果、应用新通道（防效果残留到非通道盘）
        self._fx_channel = ch
        for d in (self._engine.deck_a, self._engine.deck_b):
            d.set_fx("", 0.0)
        self._apply_beat_fx()
        label = {"1": "A", "2": "B", "both": "A+B"}.get(ch, "A")
        self._status(f"FX 通道：{label}")

    def _on_beat_fx_beats(self, beats: int) -> None:
        # 拍数接线（J1.1）：Echo/Delay 延迟 = beats/4 拍、Trans 门控周期随 BPM
        self._fx_beats = beats
        for d in (self._engine.deck_a, self._engine.deck_b):
            d.set_fx_beats(beats)

    def _on_fx_auto(self) -> None:
        # AUTO（J1.1）：以曲目 BPM 为 FX 时基（引擎在 set_tempo/Tap 后自动重配延迟）
        decks = self._fx_channel_decks()
        if any(d.bpm <= 0 for d in decks):
            self._status("FX AUTO：通道内存在无 BPM 的盘（先加载曲目或 Tap）")
            return
        for d in decks:
            d.set_fx_beats(self._fx_beats)
        self._status("FX AUTO：以曲目 BPM 为时基")

    def _on_fx_tap(self) -> None:
        # TAP（J1.1）：点按测速作为 FX 时基（取通道第一盘）
        bpm = self._fx_channel_decks()[0].tap()
        if bpm > 0:
            self._status(f"FX TAP BPM: {bpm:.1f}")
        else:
            self._status("FX TAP：连续点按至少 2 次")

    def _apply_beat_fx(self) -> None:
        # 按面板当前状态应用 Beat FX 到通道盘（效果/深度/开关变化统一调用）
        on = self._beat_fx.is_on()  # I1.2：公开接口读取开关状态
        for deck in self._fx_channel_decks():
            if on and self._beat_fx_effect:
                deck.set_fx(self._beat_fx_effect, self._beat_fx_depth)
            else:
                deck.set_fx("", 0.0)
        self._update_fx_status()  # J0.7：状态小屏联动

    # --- 耳机监听（J1.0） ---

    def _on_cue_preview(self, letter: str) -> None:
        # 耳机预听（独占切换）：播放该盘当前位置到曲尾；再点同盘停止
        player = self._engine.ensure_cue_player()
        if player is None or player.is_dead:
            self._status("耳机监听不可用（无可用输出设备）")
            return
        if self._cue_active == letter:
            player.stop()
            self._cue_active = None
            getattr(self, f"_phones_cue_{letter}").set_led(False)
            self._status(f"DECK {letter.upper()} 监听停止")
            return
        deck = getattr(self._engine, f"deck_{letter}")
        buf = deck.cue_buffer()
        if buf is None or len(buf) == 0:
            self._status(f"DECK {letter.upper()} 无音频可监听")
            return
        player.play(buf)
        self._cue_active = letter
        for l in ("a", "b"):
            getattr(self, f"_phones_cue_{l}").set_led(
                l == letter, _UI.get("glow_green", "#2fe37a")
            )
        self._status(f"DECK {letter.upper()} 监听中")

    def _on_cue_volume(self, v: float) -> None:
        # 监听音量（J1.0）
        player = self._engine.ensure_cue_player()
        if player is not None:
            player.set_volume(v)

    # --- M2 自动编排（PL002.12） ---

    def _on_recommend_and_prepare(self) -> None:
        # Auto Next：推荐下一曲（小屏+理由显示）并立即 Prepare 装填
        rec = self._automix.recommend()
        if rec is None:
            self._rec_display.set_text("--")
            self._rec_label.setText("无可用推荐（需当前盘已知 BPM 与曲库数据）")
            self._status("无可用推荐：当前盘需已知 BPM，曲库需有其他曲目")
            return
        self._rec_display.set_text(rec["entry"]["name"][:12])
        self._rec_label.setText(rec["explanation"])
        now_deck = getattr(self._engine, f"deck_{self._target}")
        entry = self._automix.prepare_next(now_deck, on_done=self._on_prepared_done)
        if entry is not None:
            self._pending_entry[self._target] = entry  # FIX005.6 键控
            self._status(f"已推荐并预备: {rec['entry']['name']}（{rec['explanation']}）")
        else:
            self._status("推荐预备失败（当前盘需 PLAYING 且已知 BPM）")

    def _set_automix_ui(self, on: bool, quiet: bool = False) -> None:
        # AUTO 状态统一设置（PL002.11：auto_mode + 按钮勾选 + LED 三同步——
        # 程序化退出（手动装填）不依赖 toggled 信号；quiet=不发状态栏）
        self._automix.auto_mode = bool(on)
        self._auto_btn.blockSignals(True)
        self._auto_btn.setChecked(bool(on))
        self._auto_btn.blockSignals(False)
        self._auto_btn.set_led(bool(on), _UI.get("glow_blue", "#2f8bff"))
        if not quiet:
            self._status(
                f"AUTO 自动模式{'开：Mix 完成后自动接歌' if on else '关'}"
            )

    def _toggle_automix(self, on: bool) -> None:
        # AUTO 开关槽（用户点击 toggled 驱动；转统一设置）
        self._set_automix_ui(bool(on))

    # --- 主题切换（J2 批次 2） ---

    def _cycle_theme(self) -> None:
        # Ctrl+T：dark/light 循环切换（token 表 + QSS 重建；控件经 ThemeBus
        # 清缓存重绘；静态 LED 按新主题重涂）
        name = "light" if palette.current() == "dark" else "dark"
        if not switch_theme(QApplication.instance(), name):
            self._status(f"未知主题：{name}")
            return
        self._apply_static_leds()
        self._refresh_lib_hint_style()
        self._status(f"主题切换：{name}（Ctrl+T 循环）")

    def _apply_static_leds(self) -> None:
        # 静态 LED 基色按当前主题重涂（动态 LED——播放键/Pad/滑行键——由 _tick
        # 周期性重涂无需处理；此处覆盖 LOAD/SHIFT/SYNC/监听/Beat FX 效果键）
        orange = palette.token("glow_orange", "#ff7a2f")
        blue = palette.token("glow_blue", "#2f8bff")
        green = palette.token("glow_green", "#2fe37a")
        self._load_a_btn.set_led(True, orange)
        self._load_b_btn.set_led(True, orange)
        self._mix_btn.set_led(True, orange)
        self._shift_btn.set_led(self._shift.is_shift(), blue)
        for letter in ("a", "b"):
            deck = getattr(self._engine, f"deck_{letter}")
            playing = deck.state in (State.PLAYING, State.MIXING) and not deck.paused
            widget = getattr(self, f"deck_widget_{letter}")
            widget.set_playing_state(playing)
            widget.set_sync_active(self._sync_on[letter])
            getattr(self, f"_phones_cue_{letter}").set_led(
                self._cue_active == letter, green
            )
        self._beat_fx.reapply_leds()

    def _on_beat_fx_fx(self, fx: str) -> None:
        # Beat FX 效果类型变化：记录并应用
        self._beat_fx_effect = fx
        self._apply_beat_fx()

    def _on_beat_fx_depth(self, v: float) -> None:
        # Beat FX 深度变化：记录并应用
        self._beat_fx_depth = v
        self._apply_beat_fx()

    def _on_beat_fx_onoff(self, on: bool) -> None:
        # Beat FX 开关变化：按状态统一应用（off 时清空）
        if on and not self._beat_fx_effect:
            self._beat_fx_effect = "HPF"  # 默认效果
        self._apply_beat_fx()

    def keyPressEvent(self, event) -> None:
        # 键盘 SHIFT 驱动全局修饰状态（E2.1）；空格 = 播放/暂停目标盘（J0.8，
        # 子控件持有焦点时由子控件消费按键，不影响搜索框输入空格）
        if event.key() == Qt.Key_Space:
            self._toggle_play(getattr(self._engine, f"deck_{self._target}"))
            self._status(f"空格：DECK {self._target.upper()} 播放/暂停")
            event.accept()
            return
        if event.key() == Qt.Key_Shift:  # Qt.Key_Shift
            self._shift.set_active(True)
            self._shift_btn.setChecked(True)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event) -> None:
        # 键盘 SHIFT 释放
        if event.key() == Qt.Key_Shift:
            self._shift.set_active(False)
            self._shift_btn.setChecked(False)
        super().keyReleaseEvent(event)

    # --- 定时刷新（D4.3 播放头/进度） ---

    def _tick(self) -> None:
        # 100ms 定时器：进度/播放头/播放状态 + VU + LED 灯态（E2.5/E2.7）+ Jog 中心屏
        for letter, widget in (("a", self.deck_widget_a), ("b", self.deck_widget_b)):
            deck = getattr(self._engine, f"deck_{letter}")
            widget.update_progress(deck.position, deck.duration)
            # I0.4：MIXING 也计入播放中（原只判 "playing"，Mix Now 后 16s
            # 淡化期间播放键文案/灯态失实且点击行为错位）
            playing = deck.state in (State.PLAYING, State.MIXING) and not deck.paused
            widget.set_playing_state(playing)
            # Jog 中心屏（F6.3）：BPM + 位置
            jog = self.jog_a if letter == "a" else self.jog_b
            jog.set_playing(playing)
            bpm = self._deck_meta[letter].get("bpm", 0.0)
            info = f"{bpm:.1f}" if bpm and bpm > 0 else "--"
            jog.set_info(f"{info} BPM")
        # VU（E2.5）
        vu = self._engine.vu_levels()
        self._vu_a.set_level(vu[0])
        self._vu_b.set_level(vu[1])
        # LED（E2.7）
        for letter, deck in (("a", self._engine.deck_a), ("b", self._engine.deck_b)):
            pad = self.pad_a if letter == "a" else self.pad_b
            if pad.mode == "Hot Cue":
                for i in range(SLOT_COUNT):
                    pad.set_pad_light(i, deck.hot_cue_state(i)["has"])
            elif pad.mode == "Sampler":
                for i in range(SLOT_COUNT):
                    pad.set_pad_light(i, deck.sample_state(i)["loaded"])
            elif pad.mode == "Key Shift":
                pad.set_pad_light(0, deck.key_shift == 0)
                pad.set_pad_light(1, deck.key_shift == 1)
                pad.set_pad_light(2, deck.key_shift == 2)
                pad.set_pad_light(3, deck.key_shift >= 3)
                pad.set_pad_light(4, deck.key_shift == -3)
                pad.set_pad_light(5, deck.key_shift == -2)
                pad.set_pad_light(6, deck.key_shift == -1)
                pad.set_pad_light(7, deck.key_shift == 0)
            self._slip_btns[letter].setChecked(deck.slip_active)
            # FIX004.3：mix 完成消费（UI 线程，替代原 mix_now 后立即链式的
            # MIXING 守卫死锁）——meta 滚动到来曲 + AUTO 模式链式装填下一曲
            if deck.take_mix_finished():  # FIX005.17：公开读即清（原私有直读直写）
                pending = self._pending_entry[letter]
                if pending is not None:
                    finished_path = self._deck_meta[letter].get("path")  # 播完曲（滚动前捕获）
                    self._deck_meta[letter] = self._make_deck_meta(pending)
                    incoming = pending
                    self._pending_entry[letter] = None
                    # FIX005.10：混后引擎 BPM/下拍网格随新曲（原只滚 meta，
                    # Beat FX 时基/beat_jump/网格全按旧曲）
                    deck.set_tempo(incoming.get("bpm", 0.0))
                    widget.waveform.set_grid(incoming.get("record", {}).get("downbeats", []))
                    self._status(
                        f"Mix 完成 → DECK {letter.upper()}: {Path(incoming['path']).name}"
                    )
                    if self._automix.auto_mode:
                        nxt = self._automix.on_mix_started(deck, finished_path=finished_path)  # FIX005.1/.2
                        if nxt is not None:
                            self._pending_entry[letter] = nxt
                            self._status(f"AUTO 链式预备: {Path(nxt['path']).name}")
                        else:
                            self._status("AUTO：无更多可用推荐（自动接歌停止）")

    # --- 其他 ---

    def _toggle_target(self) -> None:
        # 切换目标盘 A/B（双击加载与转场作用对象）；AUTO 模式期间切盘即退出
        # （FIX005/#20：now_meta_getter 以 _target late-bind，切盘会使 AUTO 链
        # 基准错位）
        self._target = "b" if self._target == "a" else "a"
        self._target_btn.setText(f"目标盘: {self._target.upper()}")
        self._update_fx_status()  # J0.7：状态小屏联动
        if self._automix.auto_mode:
            self._set_automix_ui(False, quiet=True)
            self._status("切换目标盘：AUTO 自动模式已退出")
        self._status(f"目标盘切换为 DECK {self._target.upper()}")

    def _open_folder(self) -> None:
        # 打开文件夹并加载曲库（分析后台执行）
        folder = QFileDialog.getExistingDirectory(self, "选择音乐文件夹")
        if folder:
            self.load_library(folder)

    def _status(self, msg: str) -> None:
        # 状态栏提示（同时写日志）
        self.statusBar().showMessage(msg, 5000)
        _logger.info("%s", msg)

    def closeEvent(self, event) -> None:
        # 关闭：置关闭标记（分析 worker 回调前检查，I3.6 防 emit 已删对象崩溃）、
        # 停止定时器并关闭引擎流（异常捕获不崩溃）
        self._closing = True
        self._set_automix_ui(False, quiet=True)  # PL002.11：关闭即停自动模式
        self._timer.stop()
        try:
            self._engine.close()
        except Exception:
            _logger.warning("引擎关闭异常（忽略）", exc_info=True)
        event.accept()


# ===== ui/main_window.py 模块说明 =====
# 模块级常量：
#   _SC / _UI：静态配置（窗口尺寸/配色 token）
#   _logger：统一日志器（utils.logger）
# 类型：
#   MainWindow(QMainWindow)：主窗口（engine 可注入便于无头测试）
# 方法：
#   load_library(folder, records=None)：曲库加载（records 注入跳过分析；否则后台线程
#     analyze_many + QueuedConnection 回填）；_append_row/_append_row_safe/_filter_table
#   _on_row_double_clicked：双击加载到目标盘（解码+播放+波形+元数据，异常捕获）
#   _toggle_play/_on_cue/_on_beatloop/_on_keylock/_on_pitch：DeckWidget 信号处理
#   _on_prepare/_on_prepared_done/_on_mix：TransitionManager 集成（D3 复用）
#   _tick：100ms 刷新进度/播放头/播放状态
#   _bind_value_tip(wgt, fmt)：控件数值实时 Tooltip（J0.7）
#   _update_fx_status()：FX 状态小屏刷新（J0.7，目标盘/效果/开关）
#   _apply_splitter_sizes()：两级 splitter 确定性尺寸（PL001.1：body 按窗宽
#     百分比、main = 各列最小宽 + 富余按份额分配——构造与 show 后各一次；
#     原百分比 setSizes 总和超主区被压缩+钳制是列宽失真根因）
#   _update_lib_hint()：空库引导句显隐（PL001.13，rowCount==0 时可见）
#   _on_recommend_and_prepare()/_toggle_automix(on)：M2 推荐区（PL002.12——
#     Auto Next 单步推荐装填；AUTO 勾选自动模式，手动装填即退出防双源）
#   _toggle_target/_open_folder/_status/closeEvent：目标盘/文件对话框/状态栏/关闭
# 设计理由：UI 只发指令（信号→引擎方法，B1 纪律）；引擎/转场注入便于无头测试；
#   后台分析经 QueuedConnection 回主线程（Qt 线程安全）
# 异常处理：加载/引擎关闭异常捕获不崩溃（AGENTS.md 错误策略）；分析失败曲目降级空记录
# 关联配置：config/static/base.json（window_width/height/sample_rate）；
#   ui.json（colors/jog_bend_reset_ms/table_headers，H3.5 补全；
#   splitter_*/spacing_*/knob_size_*/button_min_*，J0.1/J0.3 补全）

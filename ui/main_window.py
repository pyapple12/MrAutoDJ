# 主窗口：曲库（搜索/表格）+ 双打碟机 + 混音台（EQ×2/横推/主音量）+ 转场（D4）
# 引擎可注入（无头测试传 fake）；100ms 定时器刷新进度；分析在后台线程 + 信号回填

from __future__ import annotations

import threading
import time as _time
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
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
from modules.engine import AudioEngine, SLOT_COUNT, State
from modules.stretcher import rubberband_available
from modules.transition import tempo_compatible
from modules.transition_manager import DEFAULT_FADE_SECONDS, TransitionManager
from ui.beat_fx_widget import BEAT_LADDER, BeatFxWidget
from ui.deck_widget import DeckWidget
from ui.jog_wheel import JogWheel
from ui.pad_widget import PadWidget
from ui.shift_state import ShiftState
from ui.widgets.fader_slider import FaderSlider
from ui.widgets.glow_button import GlowButton
from ui.widgets.led_strip import LedStrip
from ui.widgets.panel_frame import PanelFrame
from ui.widgets.rotary_knob import RotaryKnob
from utils.logger import get_logger

# 静态配置解包（窗口尺寸，AGENTS.md 参数约定）
_SC = get_static_config()
_UI = _SC.ui  # 静态配置解包（窗口尺寸/配色 token）

_logger = get_logger(__name__)


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
        # 弯音脉冲归零（P2 修复）：每盘 pending 值 + 单发定时器（超时调 jog_bend(0)）
        self._bend_pending: dict = {"a": 0.0, "b": 0.0}
        self._bend_timers: dict = {}
        for _letter in ("a", "b"):
            _t = QTimer(self)
            _t.setSingleShot(True)
            _t.setInterval(int(_UI.get("jog_bend_reset_ms", 80)))
            _t.timeout.connect(lambda l=_letter: self._on_bend_timeout(l))
            self._bend_timers[_letter] = _t

        self.setWindowTitle("MrAutoDJ")
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
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        # --- Browse 区（顶部面板） ---
        browse_panel = PanelFrame("BROWSE")
        browse = QHBoxLayout(browse_panel)
        browse.setContentsMargins(10, 8, 10, 8)
        self._load_a_btn = GlowButton("LOAD A")
        self._load_a_btn.set_led(True, _UI.get("glow_orange", "#ff7a2f"))
        self._load_b_btn = GlowButton("LOAD B")
        self._load_b_btn.set_led(True, _UI.get("glow_orange", "#ff7a2f"))
        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索曲库...")
        self._open_btn = GlowButton("打开文件夹")
        self._target_btn = GlowButton("目标盘: A")
        # E2.1 全局 SHIFT 按钮（也可用键盘 SHIFT）
        self._shift_btn = GlowButton("SHIFT")
        self._shift_btn.setCheckable(True)
        browse.addWidget(self._load_a_btn)
        browse.addWidget(self._load_b_btn)
        browse.addWidget(self._search, 1)
        browse.addWidget(self._open_btn)
        browse.addWidget(self._target_btn)
        browse.addWidget(self._shift_btn)
        root.addWidget(browse_panel)

        # --- 主体：曲库 | 主区四列（Deck A | Mixer | Deck B | Effects） ---
        body = QSplitter(Qt.Horizontal)
        # 曲库面板
        lib_panel = PanelFrame("LIBRARY")
        lib_box = QVBoxLayout(lib_panel)
        lib_box.setContentsMargins(8, 8, 8, 8)
        self._table_headers = _UI.get(
            "table_headers", ["状态", "曲名", "BPM", "调性", "能量"]
        )
        self._table = QTableWidget(0, len(self._table_headers))
        self._table.setHorizontalHeaderLabels(self._table_headers)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)
        lib_box.addWidget(self._table)
        body.addWidget(lib_panel)

        # 双打碟机（含 E2 组件：Jog / Pad / 表演键；G3.5 导入上移顶层）
        self.deck_widget_a = DeckWidget("DECK A")
        self.deck_widget_b = DeckWidget("DECK B")
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
        w = self._win_w
        body.setSizes([int(w * 0.24), int(w * 0.76)])
        main.setSizes([int(w * 0.24), int(w * 0.22), int(w * 0.24), int(w * 0.19)])
        root.addWidget(body, 3)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        self._status("就绪")

    def _build_deck_panel(
        self, letter: str, name: str, wdg, jog, pad, slip, censor, stut
    ) -> QWidget:
        # 构建单盘面板：DeckWidget（信息/波形/控制/Pitch）+ Jog + Pad + 表演键
        panel = PanelFrame(name)
        box = QVBoxLayout(panel)
        box.setContentsMargins(8, 8, 8, 8)
        box.addWidget(wdg, 1)
        perf = QHBoxLayout()
        perf.addWidget(jog)
        pad_col = QVBoxLayout()
        pad_col.addWidget(pad)
        krow = QHBoxLayout()
        for k in (slip, censor, stut):
            krow.addWidget(k)
        pad_col.addLayout(krow)
        perf.addLayout(pad_col)
        box.addLayout(perf)
        return panel

    def _build_mixer_panel(self) -> QWidget:
        # 构建 Mixer 面板：TRIM/EQ 旋钮 + VU/推子/FaderStart/Tap + 横推 + 主音量
        panel = PanelFrame("MIXER")
        box = QVBoxLayout(panel)
        box.setContentsMargins(8, 8, 8, 8)
        # 行1：TRIM A/B
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("A TRIM"))
        self._trim_a = RotaryKnob(0.0, 2.0, default=1.0)
        row1.addWidget(self._trim_a)
        row1.addSpacing(12)
        row1.addWidget(QLabel("B TRIM"))
        self._trim_b = RotaryKnob(0.0, 2.0, default=1.0)
        row1.addWidget(self._trim_b)
        row1.addStretch(1)
        box.addLayout(row1)
        # 行2：EQ A/B（低中高旋钮）
        row2 = QHBoxLayout()
        self._eq_a_sliders = {}
        self._eq_b_sliders = {}
        for title, knobs in (("A", self._eq_a_sliders), ("B", self._eq_b_sliders)):
            col = QVBoxLayout()
            col.addWidget(QLabel(f"{title} EQ"))
            for band in ("低", "中", "高"):
                r = QHBoxLayout()
                r.addWidget(QLabel(band))
                k = RotaryKnob(-1.0, 1.0, default=0.0)
                k.setObjectName(f"{title}-{band}")
                r.addWidget(k)
                col.addLayout(r)
                knobs[band] = k
            row2.addLayout(col)
            row2.addSpacing(12)
        row2.addStretch(1)
        box.addLayout(row2)
        # 行3：VU + FaderStart + Tap（A/B 两列）
        row3 = QHBoxLayout()
        for letter in ("a", "b"):
            col = QVBoxLayout()
            label = letter.upper()
            col.addWidget(QLabel(f"{label} VU"))
            meter = LedStrip()  # I2.3：段数走 ui.json led_segments（原显式 12 双处）
            setattr(self, f"_vu_{letter}", meter)
            col.addWidget(meter)
            fs = GlowButton(f"{label} FaderStart")
            fs.setCheckable(True)
            setattr(self, f"_fs_{letter}", fs)
            col.addWidget(fs)
            tap = GlowButton(f"{label} Tap")
            setattr(self, f"_tap_{letter}", tap)
            col.addWidget(tap)
            row3.addLayout(col)
            row3.addSpacing(12)
        row3.addStretch(1)
        box.addLayout(row3)
        # 行4：横推（水平）
        row4 = QHBoxLayout()
        xf_col = QVBoxLayout()
        xf_col.addWidget(QLabel("横推"))
        self._xfader = FaderSlider(-1.0, 1.0, 0.0, Qt.Horizontal, length=140)
        xf_col.addWidget(self._xfader)
        row4.addLayout(xf_col, 1)
        box.addLayout(row4)
        return panel

    def _build_effects_panel(self) -> QWidget:
        # 构建 Effects 面板：MASTER 旋钮 + Beat FX + 转场按钮（G3.5 导入已上移顶层）
        panel = PanelFrame("EFFECTS")
        box = QVBoxLayout(panel)
        box.setContentsMargins(8, 8, 8, 8)
        self._volume = RotaryKnob(0.0, 2.0, default=1.0)
        master_row = QHBoxLayout()
        master_row.addWidget(QLabel("MASTER"))
        master_row.addWidget(self._volume)
        master_row.addStretch(1)
        box.addLayout(master_row)
        self._beat_fx = BeatFxWidget()
        box.addWidget(self._beat_fx, 1)
        # 转场（FLX4 无此部件，保留功能：Prepare/Mix）
        self._prepare_btn = GlowButton("Prepare 来曲")
        self._mix_btn = GlowButton("Mix Now")
        self._mix_btn.set_led(True, _UI.get("glow_orange", "#ff7a2f"))
        tr_col = QVBoxLayout()
        tr_col.addWidget(self._prepare_btn)
        tr_col.addWidget(self._mix_btn)
        box.addLayout(tr_col)
        return panel

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
        # Beat FX（作用目标盘）
        self._beat_fx.fx_changed.connect(self._on_beat_fx_fx)
        self._beat_fx.depth_changed.connect(self._on_beat_fx_depth)
        self._beat_fx.onoff_changed.connect(self._on_beat_fx_onoff)
        # 表演键（E2.8）
        self._slip_btns["a"].toggled.connect(self._engine.deck_a.slip_toggle)
        self._slip_btns["b"].toggled.connect(self._engine.deck_b.slip_toggle)
        self._censor_btns["a"].toggled.connect(self._engine.deck_a.censor)
        self._censor_btns["b"].toggled.connect(self._engine.deck_b.censor)
        for letter, deck in (("a", self._engine.deck_a), ("b", self._engine.deck_b)):
            self._stutter_btns[letter].clicked.connect(deck.stutter)

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
        # 追加一行到表格与曲库列表（兼容标记随当前播放盘 BPM 刷新；
        # H3.1：tempo_compatible 顶层导入）
        bpm = float(rec.get("bpm", 0.0) or 0.0)
        key = rec.get("key", "?") or "?"
        energy = rec.get("energy", 0)
        now_bpm = self._deck_meta[self._target].get("bpm", 0.0)
        mark = ":)" if tempo_compatible(now_bpm, bpm) else ""
        row = self._table.rowCount()
        self._table.insertRow(row)
        for col, text in enumerate(
            (
                mark,
                Path(path).name,
                f"{bpm:.1f}" if bpm > 0 else "---",
                key,
                str(energy),
            )
        ):
            self._table.setItem(row, col, QTableWidgetItem(text))
        self._library.append(
            {"path": path, "bpm": bpm, "key": key, "energy": energy, "record": rec}
        )
        self._table.item(row, 0).setData(Qt.UserRole, path)

    def _filter_table(self, text: str) -> None:
        # 搜索过滤：隐藏不匹配行（简单包含匹配）
        text = text.strip().lower()
        for row in range(self._table.rowCount()):
            name_item = self._table.item(row, 1)
            visible = not text or (
                name_item is not None and text in name_item.text().lower()
            )
            self._table.setRowHidden(row, not visible)

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
        widget.set_playing_state(True)
        self._deck_meta[letter] = {
            "path": path,
            "bpm": entry["bpm"],
            "key": entry["key"],
            "downbeats": list(entry["record"].get("downbeats", [])),
        }
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
            other_widget.set_playing_state(True)
            self._deck_meta[other] = {
                "path": path,
                "bpm": entry["bpm"],
                "key": entry["key"],
                "downbeats": list(entry["record"].get("downbeats", [])),
            }
            self._last_load = (None, 0.0)
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

    def _on_keylock(self, deck, on: bool) -> None:
        # Keylock 开关（占位：M1 预渲染管线接入点在转场；此处仅提示）
        self._status(f"Keylock {'开' if on else '关'}")

    def _on_pitch(self, deck, percent: float) -> None:
        # Pitch 变化（占位：预渲染管线在 D3 转场接入，实时变调后续扩展）
        self._status(f"Pitch {percent:+.0f}%（预渲染接入待 D3 管线完善）")

    # --- 转场（D3 集成到 UI） ---

    def _on_prepare(self) -> None:
        # Prepare：以目标盘为 now，表格选中行为来曲，走 TransitionManager
        # I3.1：rubberband 前置探测（缺失只提示不阻断——SKIP 直混转场仍可用）
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
        self._tm.prepare(
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
        self._status(f"预备中: {Path(entry['path']).name}")

    def _on_prepared_done(self, plan, error) -> None:
        # prepare 完成回调（worker 线程；经状态信号回主线程更新）
        if error is not None:
            self.status_message.emit(f"Prepare 失败: {error}")
            return
        skip = "SKIP" if plan and plan.skip else "STRETCH"
        self.status_message.emit(f"Prepare 完成（{skip}），可 Mix")

    def _on_mix(self) -> None:
        # Mix Now：目标盘混入已预备缓冲（失败提示原因）
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
        # 反向抵消），钳制 ±0.5；重启单发定时器，超时后 jog_bend(0) 归零
        if abs(v) > 0.01:
            self._bend_pending[letter] = max(
                -0.5, min(0.5, self._bend_pending[letter] + v)
            )
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
                self._status(f"采样槽 {idx + 1} 未载入")
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

    def _apply_beat_fx(self) -> None:
        # 按面板当前状态应用 Beat FX 到目标盘（效果/深度/开关任一变化时统一调用）
        deck = getattr(self._engine, f"deck_{self._target}")
        on = self._beat_fx.is_on()  # I1.2：公开接口读取开关状态（不再跨控件访问私有字段）
        if on and self._beat_fx_effect:
            deck.set_fx(self._beat_fx_effect, self._beat_fx_depth)
        else:
            deck.set_fx("", 0.0)

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
        # 键盘 SHIFT 驱动全局修饰状态（E2.1）
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

    # --- 其他 ---

    def _toggle_target(self) -> None:
        # 切换目标盘 A/B（双击加载与转场作用对象）
        self._target = "b" if self._target == "a" else "a"
        self._target_btn.setText(f"目标盘: {self._target.upper()}")
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
#   _toggle_target/_open_folder/_status/closeEvent：目标盘/文件对话框/状态栏/关闭
# 设计理由：UI 只发指令（信号→引擎方法，B1 纪律）；引擎/转场注入便于无头测试；
#   后台分析经 QueuedConnection 回主线程（Qt 线程安全）
# 异常处理：加载/引擎关闭异常捕获不崩溃（AGENTS.md 错误策略）；分析失败曲目降级空记录
# 关联配置：config/static/base.json（window_width/height/sample_rate）；
#   ui.json（colors/jog_bend_reset_ms/table_headers，H3.5 补全）

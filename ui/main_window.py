# 主窗口：曲库（搜索/表格）+ 双打碟机 + 混音台（EQ×2/横推/主音量）+ 转场（D4）
# 引擎可注入（无头测试传 fake）；100ms 定时器刷新进度；分析在后台线程 + 信号回填

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.static.static_config import get_static_config
from modules import analyzer as analyzer_mod
from modules.engine import AudioEngine
from modules.transition import tempo_compatible
from modules.transition_manager import TransitionManager
from utils.logger import get_logger

# 静态配置解包（窗口尺寸，AGENTS.md 参数约定）
_SC = get_static_config()
_UI_COLORS = _SC.ui.get("colors", {})

_logger = get_logger(__name__)


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
        # 构建控件树：工具栏（打开/目标盘/加载演示）→ 曲库 + 双盘 + 混音台
        central = QWidget()
        root = QVBoxLayout(central)

        toolbar = QHBoxLayout()
        self._open_btn = QPushButton("打开文件夹")
        self._target_btn = QPushButton("目标盘: A")
        toolbar.addWidget(self._open_btn)
        toolbar.addWidget(self._target_btn)
        toolbar.addStretch(1)
        root.addLayout(toolbar)

        body = QSplitter(Qt.Horizontal)
        # 曲库面板
        lib_panel = QWidget()
        lib_box = QVBoxLayout(lib_panel)
        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索曲库...")
        lib_box.addWidget(self._search)
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Mix", "曲名", "BPM", "调性", "能量"])
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)
        lib_box.addWidget(self._table)
        body.addWidget(lib_panel)

        # 双打碟机
        from ui.deck_widget import DeckWidget

        self.deck_widget_a = DeckWidget("DECK A")
        self.deck_widget_b = DeckWidget("DECK B")
        decks = QSplitter(Qt.Horizontal)
        decks.addWidget(self.deck_widget_a)
        decks.addWidget(self.deck_widget_b)
        body.addWidget(decks)
        body.setSizes([int(self._win_w * 0.35), int(self._win_w * 0.65)])
        root.addWidget(body, 3)

        # 混音台
        mixer = QWidget()
        mix_box = QHBoxLayout(mixer)
        self._eq_a_sliders = self._add_eq_group(mix_box, "A EQ")
        self._eq_b_sliders = self._add_eq_group(mix_box, "B EQ")
        # 横推
        xf_col = QVBoxLayout()
        xf_col.addWidget(QLabel("横推"))
        self._xfader = QSlider(Qt.Horizontal)
        self._xfader.setRange(-100, 100)
        self._xfader.setValue(0)
        xf_col.addWidget(self._xfader)
        mix_box.addLayout(xf_col)
        # 主音量
        vol_col = QVBoxLayout()
        vol_col.addWidget(QLabel("主音量"))
        self._volume = QSlider(Qt.Horizontal)
        self._volume.setRange(0, 200)
        self._volume.setValue(100)
        vol_col.addWidget(self._volume)
        mix_box.addLayout(vol_col)
        # 转场
        self._prepare_btn = QPushButton("Prepare 来曲")
        self._mix_btn = QPushButton("Mix Now")
        tr_col = QVBoxLayout()
        tr_col.addWidget(self._prepare_btn)
        tr_col.addWidget(self._mix_btn)
        mix_box.addLayout(tr_col)
        root.addWidget(mixer)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        self._status("就绪")

    def _add_eq_group(self, box: QHBoxLayout, title: str) -> dict:
        # 构建一组三频 EQ 滑块（低/中/高，-100..100 映射 -1..1）
        col = QVBoxLayout()
        col.addWidget(QLabel(title))
        sliders = {}
        for band in ("低", "中", "高"):
            row = QHBoxLayout()
            row.addWidget(QLabel(band))
            s = QSlider(Qt.Horizontal)
            s.setRange(-100, 100)
            s.setValue(0)
            s.setObjectName(f"{title}-{band}")
            row.addWidget(s)
            col.addLayout(row)
            sliders[band] = s
        box.addLayout(col)
        return sliders

    def _connect_signals(self) -> None:
        # 连接信号：按钮/滑块 → 引擎/转场；表格双击 → 加载到目标盘
        self._open_btn.clicked.connect(self._open_folder)
        self._target_btn.clicked.connect(self._toggle_target)
        self._search.textChanged.connect(self._filter_table)
        self._table.itemDoubleClicked.connect(self._on_row_double_clicked)
        self._prepare_btn.clicked.connect(self._on_prepare)
        self._mix_btn.clicked.connect(self._on_mix)
        self._xfader.valueChanged.connect(
            lambda v: self._engine.crossfader.set_position(v / 100.0)
        )
        self._volume.valueChanged.connect(lambda v: self._engine.set_volume(v / 100.0))
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

    def _connect_eq(self, sliders: dict, deck) -> None:
        # 连接一组 EQ 滑块到指定盘的三频 setter
        sliders["低"].valueChanged.connect(lambda v: deck.eq.set_low(v / 100.0))
        sliders["中"].valueChanged.connect(lambda v: deck.eq.set_mid(v / 100.0))
        sliders["高"].valueChanged.connect(lambda v: deck.eq.set_high(v / 100.0))

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

        def _on_result(path: str, record, error) -> None:
            # worker 线程回调：经 Qt 信号回主线程回填（错误曲目降级空记录）
            if error is not None:
                _logger.warning("分析失败 %s: %s", path, error)
            self.analysis_ready.emit(path, record or analyzer_mod.empty_record())

        threading.Thread(
            target=analyzer_mod.analyze_many,
            args=(files, _on_result),
            kwargs={"with_cues": False},
            daemon=True,
        ).start()
        return len(files)

    def _append_row_safe(self, path: str, rec: dict) -> None:
        # 主线程槽：追加表格行（analyze_many 回调经 QueuedConnection 调用）
        self._append_row(path, rec)

    def _append_row(self, path: str, rec: dict) -> None:
        # 追加一行到表格与曲库列表（兼容标记随当前播放盘 BPM 刷新）
        from modules.transition import tempo_compatible as _tc

        bpm = float(rec.get("bpm", 0.0) or 0.0)
        key = rec.get("key", "?") or "?"
        energy = rec.get("energy", 0)
        now_bpm = self._deck_meta[self._target].get("bpm", 0.0)
        mark = ":)" if _tc(now_bpm, bpm) else ""
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

    def _on_row_double_clicked(self, item) -> None:
        # 双击行 → 加载到目标盘（解码 + 播放 + 波形 + 元数据；异常捕获不崩溃）
        if item is None:
            return
        path_item = self._table.item(item.row(), 0)
        if path_item is None:
            return
        path = path_item.data(Qt.UserRole)
        entry = next((e for e in self._library if e["path"] == path), None)
        if entry is None:
            return
        try:
            audio = self._engine.load_audio(path)
        except Exception as exc:
            _logger.error("加载失败 %s: %s", path, exc)
            self._status(f"加载失败: {Path(path).name}")
            return
        deck = getattr(self._engine, f"deck_{self._target}")
        deck.play(audio)
        widget = getattr(self, f"deck_widget_{self._target}")
        widget.set_track(path, entry["bpm"], entry["key"], audio)
        widget.set_playing_state(True)
        self._deck_meta[self._target] = {
            "path": path,
            "bpm": entry["bpm"],
            "key": entry["key"],
            "downbeats": list(entry["record"].get("downbeats", [])),
        }
        self._tm.mark_stale()
        self._status(f"已加载到 DECK {self._target.upper()}: {Path(path).name}")

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
        # Beatloop：按当前盘 BPM 设置拍循环（无 BPM 忽略）
        bpm = (
            self._deck_meta["a"].get("bpm")
            if deck is self._engine.deck_a
            else self._deck_meta["b"].get("bpm")
        )
        if bpm and bpm > 0:
            deck.set_beatloop(beats, bpm)
            self._status(f"Beatloop {beats} 拍")

    def _on_keylock(self, deck, on: bool) -> None:
        # Keylock 开关（占位：M1 预渲染管线接入点在转场；此处仅提示）
        self._status(f"Keylock {'开' if on else '关'}")

    def _on_pitch(self, deck, percent: float) -> None:
        # Pitch 变化（占位：预渲染管线在 D3 转场接入，实时变调后续扩展）
        self._status(f"Pitch {percent:+.0f}%（预渲染接入待 D3 管线完善）")

    # --- 转场（D3 集成到 UI） ---

    def _on_prepare(self) -> None:
        # Prepare：以目标盘为 now，表格选中行为来曲，走 TransitionManager
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
            fade_seconds=16.0,
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

    # --- 定时刷新（D4.3 播放头/进度） ---

    def _tick(self) -> None:
        # 100ms 定时器：刷新两盘进度/播放头/播放状态文案
        for letter, widget in (("a", self.deck_widget_a), ("b", self.deck_widget_b)):
            deck = getattr(self._engine, f"deck_{letter}")
            widget.update_progress(deck.position, deck.duration)
            playing = deck.state.value == "playing" and not deck.paused
            widget.set_playing_state(playing)

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
        # 关闭：停止定时器并关闭引擎流（异常捕获不崩溃）
        self._timer.stop()
        try:
            self._engine.close()
        except Exception:
            _logger.warning("引擎关闭异常（忽略）", exc_info=True)
        event.accept()


# ===== ui/main_window.py 模块说明 =====
# 模块级常量：
#   _SC / _UI_COLORS：静态配置（窗口尺寸/颜色）
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
# 关联配置：config/static/base.json（window_width/height）；ui.json（colors）

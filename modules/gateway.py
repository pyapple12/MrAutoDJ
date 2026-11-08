# WS 网关（PL003）：Tauri sidecar 的 asyncio WebSocket 服务
# 职责：接收 RPC 指令映射引擎方法 + 30Hz 状态推流；引擎零改动（锁语义沿用引擎内部锁）
# 协议：docs/ipc_protocol.md（protocol_version=1）

from __future__ import annotations

import argparse
import asyncio
import json
import threading
import time
from pathlib import Path

import numpy as np
import websockets

from config.static.static_config import get_static_config
from modules.waveform_data import build_peaks, peaks_bytes
from utils.logger import get_logger

_BASE = get_static_config().base
SAMPLE_RATE = int(_BASE.get("sample_rate", 44100))
DEFAULT_TICK_HZ = int(_BASE.get("gateway_tick_hz", 30))
APP_VERSION = str(_BASE.get("version", "0.0.0"))
PROTOCOL_VERSION = 1

# 错误码（错误码表见 docs/ipc_protocol.md；消息一律中文）
E_UNKNOWN_CMD = "unknown_cmd"
E_BAD_ARGS = "bad_args"
E_NOT_READY = "not_ready"
E_BAD_STATE = "bad_state"
E_ENGINE = "engine_error"
E_BAD_JSON = "bad_json"

_logger = get_logger(__name__)


class GatewayError(Exception):
    # 网关业务错误：携带协议错误码与中文消息（UI 只认 code 不认细节）
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


# ---------------------------------------------------------------------------
# 假引擎（--fake 无设备模式 + 探针注入复用；接口鸭子对齐真引擎，路由不分支）
# ---------------------------------------------------------------------------


class FakeDeckEQ:
    # 假三频 EQ：仅记录（接口对齐 engine.DeckEQ 的 setter 面）
    def __init__(self):
        self.low = self.mid = self.high = 0.0

    def set_low(self, amt: float) -> None:
        self.low = float(amt)

    def set_mid(self, amt: float) -> None:
        self.mid = float(amt)

    def set_high(self, amt: float) -> None:
        self.high = float(amt)

    def reset(self) -> None:
        self.low = self.mid = self.high = 0.0


class FakeDeck:
    # 假打碟机：wall-clock 位置推进 + 状态翻转，接口对齐 engine.Deck 公开面
    # （PL004 控制面全集——tempo/表演键/循环/eq/fx/hotcue/sampler/jog 全鸭子对齐）
    def __init__(self, lock):
        self._lock = lock
        self._n = 0
        self._pos0 = 0
        self._t0 = 0.0
        self._is_paused = True
        self._cue = 0.0
        self.bpm = 0.0
        self._rate = 1.0
        self._keylock_on = False
        self._key_shift_val = 0
        self._slip_on = False
        self._loop_on = False
        self._censor_on = False
        self.eq = FakeDeckEQ()
        self._fx = ""
        self._fx_beats = 4
        self._hot_cues = [False] * 8
        self._samples = [False] * 8
        self._jog_touched = False
        self._bend = 0.0
        self._search = 0.0

    def play(self, audio: np.ndarray) -> None:
        # 假播放：记录时长并从当前起点推进（等价真 Deck 的 play 语义）
        self._n = int(len(audio))
        self._pos0 = 0
        self._t0 = time.monotonic()
        self._is_paused = False

    def pause(self) -> None:
        # 播放/暂停切换（对齐真 Deck pause 的 toggle 语义）
        if self._is_paused:
            self._t0 = time.monotonic()
        else:
            self._pos0 = self.position
        self._is_paused = not self._is_paused

    @property
    def paused(self) -> bool:
        return self._is_paused

    @property
    def state(self) -> str:
        # 状态字符串（真引擎为 State 枚举，序列化后同为 "idle"/"playing"）
        if self._n == 0:
            return "idle"
        return "paused" if self._is_paused else "playing"

    @property
    def duration(self) -> int:
        return self._n

    @property
    def position(self) -> int:
        # 位置：暂停冻结、播放推进、曲尾钳制（真引擎由回调驱动，假件用时钟近似）
        if self._is_paused or self._n == 0:
            return min(self._pos0, self._n)
        pos = self._pos0 + int((time.monotonic() - self._t0) * SAMPLE_RATE)
        return min(pos, self._n)

    @property
    def tempo_rate(self) -> float:
        return self._rate

    @property
    def effective_bpm(self) -> float:
        return self.bpm * self._rate

    @property
    def key_shift(self) -> int:
        return self._key_shift_val

    def set_position_samples(self, samples: int) -> None:
        # seek：重定位（播放中重置推进起点）
        self._pos0 = max(0, int(samples))
        self._t0 = time.monotonic()

    def set_tempo(self, bpm: float) -> None:
        self.bpm = float(bpm or 0.0)

    def set_tempo_rate(self, rate: float) -> None:
        self._rate = float(rate)

    def set_keylock(self, on: bool) -> None:
        self._keylock_on = bool(on)

    def set_key_shift(self, semitones: int) -> None:
        self._key_shift_val = int(semitones)

    def slip_toggle(self, active: bool) -> None:
        self._slip_on = bool(active)

    def slip_active(self) -> bool:
        return self._slip_on

    def censor(self, active: bool) -> None:
        self._censor_on = bool(active)

    def stutter(self) -> None:
        pass

    def set_loop(self, active: bool) -> None:
        self._loop_on = bool(active)

    def loop_active(self) -> bool:
        return self._loop_on

    def set_beatloop(self, beats: int, bpm: float) -> None:
        self._loop_on = True

    def loop_in(self) -> None:
        pass

    def loop_out(self) -> None:
        pass

    def loop_halve(self) -> None:
        pass

    def loop_double(self) -> None:
        pass

    def beat_jump(self, beats: int, align: bool = False) -> None:
        pass

    def set_pregain(self, gain: float) -> None:
        self._pregain = float(gain)

    def set_fx(self, effect: str, depth: float) -> None:
        self._fx = str(effect)

    def set_fx_beats(self, beats: int) -> None:
        self._fx_beats = int(beats)

    def tap(self) -> float:
        # 假 tap：固定返回 120（探针断言 bpm>0 用）
        return 120.0

    def hot_cue_set(self, slot: int) -> None:
        self._hot_cues[slot] = True

    def hot_cue_play(self, slot: int) -> None:
        pass

    def hot_cue_clear(self, slot: int) -> None:
        self._hot_cues[slot] = False

    def hot_cue_state(self, slot: int) -> dict:
        return {"has": self._hot_cues[slot]}

    def sample_load(self, slot: int, audio: np.ndarray) -> None:
        self._samples[slot] = True

    def sample_play(self, slot: int) -> None:
        pass

    def sample_stop(self, slot: int) -> None:
        pass

    def sample_unload(self, slot: int) -> None:
        self._samples[slot] = False

    def sample_state(self, slot: int) -> dict:
        return {"loaded": self._samples[slot]}

    def take_mix_finished(self) -> bool:
        # 假 mix 完成消费（接口对齐真 Deck；假件无转场流程恒 False）
        return False

    def jog_touch(self, on: bool) -> None:
        self._jog_touched = bool(on)

    def jog_scratch(self, delta_samples: int) -> None:
        self._pos0 = max(0, self.position + int(delta_samples))
        self._t0 = time.monotonic()

    def jog_bend(self, rate: float) -> None:
        self._bend = float(rate)

    def jog_search(self, rate: float) -> None:
        self._search = float(rate)

    def cue_set(self) -> None:
        self._cue = self.position / SAMPLE_RATE

    def cue_play(self) -> None:
        self.set_position_samples(int(self._cue * SAMPLE_RATE))

    def cue_buffer(self) -> np.ndarray | None:
        # 监听预听缓冲：CUE 点到曲尾（假件从 CUE 起合成短段；无曲返回 None）
        if self._n == 0:
            return None
        n = max(1, self._n - int(self._cue * SAMPLE_RATE))
        t = np.arange(n) / SAMPLE_RATE
        mono = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        return np.stack([mono, mono], axis=1)

    @property
    def cue_seconds(self) -> float:
        return self._cue


class FakeCuePlayer:
    # 假监听播放器：记录播放态（接口对齐 engine CuePlayer 公开面）
    def __init__(self):
        self.is_dead = False
        self.playing = False

    def play(self, buf) -> None:
        self.playing = True

    def stop(self) -> None:
        self.playing = False

    def set_volume(self, v: float) -> None:
        pass


class FakeCrossfader:
    # 假横推：仅记录位置
    def __init__(self):
        self.position = 0.5

    def set_position(self, v: float) -> None:
        self.position = float(v)


class FakeEngine:
    # 假引擎：合成音源 + 无设备输出（--fake CLI 与探针注入共用）
    def __init__(self):
        self._lock = __import__("threading").Lock()
        self.deck_a = FakeDeck(self._lock)
        self.deck_b = FakeDeck(self._lock)
        self.crossfader = FakeCrossfader()
        self.cue_player = FakeCuePlayer()

    def load_audio(self, path: str) -> np.ndarray:
        # 合成 30 秒 440Hz 正弦（假件不触盘、不解码）
        n = 30 * SAMPLE_RATE
        t = np.arange(n) / SAMPLE_RATE
        mono = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        return np.stack([mono, mono], axis=1)

    def vu_levels(self) -> list[float]:
        return [0.5, 0.25]

    def set_volume(self, v: float) -> None:
        pass

    def set_fader_start(self, enabled: bool) -> None:
        pass

    def ensure_cue_player(self):
        return self.cue_player

    def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# 客户端连接与网关本体
# ---------------------------------------------------------------------------


class _ClientConn:
    # 单客户端出站通道：唯一写出者（sender 协程），慢客户端丢帧不阻塞推流
    def __init__(self, ws):
        self.ws = ws
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=64)
        self.alive = True


class Gateway:
    # WS 网关：RPC 路由 + 30Hz 状态推流（引擎注入，tm/automix 可选）
    def __init__(self, engine, tick_hz: int = DEFAULT_TICK_HZ, tm=None, automix=None, use_fake: bool = False):
        # 引擎注入：use_fake 或 engine 为 None 时用假引擎（CLI --fake / 探针）
        if use_fake or engine is None:
            engine = FakeEngine()
            _logger.info("gateway 使用假引擎（--fake 模式）")
        self.engine = engine
        self.tm = tm
        self.automix = automix
        self.use_fake = bool(use_fake)
        self.tick_hz = max(1, int(tick_hz))
        self.slot_count = int(_BASE.get("slot_count", 8))
        # 网关侧 UI 状态（对齐 main_window 拥有的非引擎状态；引擎零改动）
        self._tempo_ranges = [int(r) for r in _BASE.get("tempo_ranges", [6, 10, 16, 100])]
        self._tempo_range = {"a": self._tempo_ranges[0], "b": self._tempo_ranges[0]}
        self._sync_on = {"a": False, "b": False}
        self._fx = {"effect": "", "depth": 0.0, "on": False, "channel": "1", "beats": 4}
        self._target = "a"
        self._cue_active: str | None = None
        # 曲库与分析（PL005：条目含 record 供 automix 评分与波形网格）
        self._entries: list[dict] = []
        self._deck_meta: dict[str, dict | None] = {"a": None, "b": None}
        self._analyzing = False
        self._analysis_stop = False
        self._pending_prepare: dict[str, dict | None] = {"a": None, "b": None}
        self._clients: set[_ClientConn] = set()
        self._server = None
        self._tick_task: asyncio.Task | None = None
        # 指令路由表（PL003 v1 8 条 + PL004 控制面全集；锁语义沿用引擎内部锁）
        self._routes = {
            # 传输（PL003）
            "load": self._cmd_load,
            "play": self._cmd_play,
            "pause": self._cmd_pause,
            "cue": self._cmd_cue,
            "seek": self._cmd_seek,
            "set_volume": self._cmd_set_volume,
            "set_xfader": self._cmd_set_xfader,
            "mix": self._cmd_mix,
            # TEMPO / Sync / 循环
            "set_tempo_rate": self._cmd_set_tempo_rate,
            "cycle_tempo_range": self._cmd_cycle_tempo_range,
            "set_sync": self._cmd_set_sync,
            "set_loop": self._cmd_set_loop,
            "loop": self._cmd_loop,
            "beatloop": self._cmd_beatloop,
            # 表演键
            "set_keylock": self._cmd_set_keylock,
            "set_key_shift": self._cmd_set_key_shift,
            "slip": self._cmd_slip,
            "censor": self._cmd_censor,
            "stutter": self._cmd_stutter,
            "tap": self._cmd_tap,
            # Mixer
            "set_pregain": self._cmd_set_pregain,
            "set_eq": self._cmd_set_eq,
            "fader_start": self._cmd_fader_start,
            "instant_doubles": self._cmd_instant_doubles,
            "set_target": self._cmd_set_target,
            # Jog
            "jog_touch": self._cmd_jog_touch,
            "jog_scratch": self._cmd_jog_scratch,
            "jog_bend": self._cmd_jog_bend,
            "jog_search": self._cmd_jog_search,
            # Pad
            "pad": self._cmd_pad,
            # Beat FX
            "set_fx": self._cmd_set_fx,
            "set_fx_channel": self._cmd_set_fx_channel,
            "set_fx_beats": self._cmd_set_fx_beats,
            "fx_auto": self._cmd_fx_auto,
            "fx_tap": self._cmd_fx_tap,
            # Phones 监听
            "phones_preview": self._cmd_phones_preview,
            "set_phones_volume": self._cmd_set_phones_volume,
            # 推荐 / Automix
            "recommend": self._cmd_recommend,
            "set_automix": self._cmd_set_automix,
            "prepare_next": self._cmd_prepare_next,
            # 曲库 / 波形（PL005）
            "library_scan": self._cmd_library_scan,
            "waveform": self._cmd_waveform,
        }

    async def serve(self, host: str = "127.0.0.1", port: int = 0) -> int:
        # 启动 WS 服务与推流协程；port=0 动态分配，返回实际端口
        self._loop = asyncio.get_running_loop()
        self._server = await websockets.serve(self._client_loop, host, port)
        actual = int(self._server.sockets[0].getsockname()[1])
        self._tick_task = asyncio.create_task(self._tick_loop())
        _logger.info("gateway 就绪 %s:%s tick=%sHz", host, actual, self.tick_hz)
        return actual

    async def stop(self) -> None:
        # 停止推流与服务（侧车退出路径；客户端连接随 server close 断开）
        if self._tick_task is not None:
            self._tick_task.cancel()
            self._tick_task = None
        for conn in list(self._clients):
            conn.alive = False
        self._clients.clear()
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    # --- 连接生命周期 ---

    async def _client_loop(self, ws) -> None:
        # 单连接主协程：入站消息处理；出站经队列由唯一 sender 协程写出
        conn = _ClientConn(ws)
        self._clients.add(conn)
        sender = asyncio.create_task(self._sender(conn))
        try:
            conn.queue.put_nowait(self._hello_frame())
            async for raw in ws:
                await self._on_message(conn, raw)
        except websockets.ConnectionClosed:
            pass
        finally:
            conn.alive = False
            sender.cancel()
            self._clients.discard(conn)
            _logger.info("客户端断开（剩余 %s）", len(self._clients))

    async def _sender(self, conn: _ClientConn) -> None:
        # 唯一写出者：串行发送出站帧（避免多协程并发 send 冲突）
        try:
            while conn.alive:
                frame = await conn.queue.get()
                await conn.ws.send(frame)
        except (websockets.ConnectionClosed, asyncio.CancelledError):
            pass

    async def _on_message(self, conn: _ClientConn, raw) -> None:
        # 入站分发：文本帧 → JSON → RPC 路由 → 响应帧入队
        if isinstance(raw, bytes):
            return  # v1 入站仅文本（二进制为服务端下行峰值帧，PL005 启用）
        try:
            msg = json.loads(raw)
        except (ValueError, TypeError):
            self._respond(conn, None, GatewayError(E_BAD_JSON, "帧不是合法 JSON"))
            return
        if not isinstance(msg, dict) or "cmd" not in msg:
            return  # 无 cmd 的帧忽略（非 RPC 噪声不回错误）
        rid = msg.get("id")
        cmd = str(msg.get("cmd") or "")
        args = msg.get("args") if isinstance(msg.get("args"), dict) else {}
        try:
            result = await self._dispatch(cmd, args)
            self._respond(conn, rid, None, result)
        except GatewayError as exc:
            self._respond(conn, rid, exc)
        except Exception as exc:
            _logger.exception("指令 %s 执行异常", cmd)
            self._respond(conn, rid, GatewayError(E_ENGINE, f"引擎执行失败: {exc}"))

    async def _dispatch(self, cmd: str, args: dict):
        # 路由查找与调用：handler 同步返回结果或协程（load 走 to_thread）
        handler = self._routes.get(cmd)
        if handler is None:
            raise GatewayError(E_UNKNOWN_CMD, f"未知指令: {cmd}")
        result = handler(args or {})
        if asyncio.iscoroutine(result):
            result = await result
        return result

    def _respond(self, conn: _ClientConn, rid, error: GatewayError | None = None, result=None) -> None:
        # 响应帧入队：ok/error 二态；队列满（客户端堵死）时丢弃并记日志
        frame = {"id": rid}
        if error is not None:
            frame["ok"] = False
            frame["error"] = {"code": error.code, "message": error.message}
        else:
            frame["ok"] = True
            frame["result"] = result
        try:
            conn.queue.put_nowait(json.dumps(frame))
        except asyncio.QueueFull:
            _logger.warning("客户端出站队列满，响应帧丢弃")

    def _hello_frame(self) -> str:
        # 握手帧：连接建立即推（协议版本/应用版本/采样率/推流频率）
        return json.dumps(
            {
                "type": "hello",
                "protocol_version": PROTOCOL_VERSION,
                "version": APP_VERSION,
                "sample_rate": SAMPLE_RATE,
                "tick_hz": self.tick_hz,
            }
        )

    # --- 30Hz 状态推流（PL003.3：绝不进音频回调，纯事件循环读锁内状态） ---

    async def _tick_loop(self) -> None:
        # 固定步长推流：向所有客户端广播状态帧；慢客户端队列满丢帧（容错登记见说明区）
        interval = 1.0 / self.tick_hz
        next_t = time.monotonic()
        while True:
            try:
                self._poll_mix_finished()  # mix 完成消费（meta 滚动 + 自动接歌链式）
            except Exception:
                _logger.exception("mix 完成消费异常（本轮跳过）")
                self._pending_prepare = {"a": None, "b": None}
            frame = json.dumps(self._tick_frame())
            for conn in list(self._clients):
                try:
                    conn.queue.put_nowait(frame)
                except asyncio.QueueFull:
                    pass  # 慢客户端丢 tick 帧（状态可自愈，下一帧即最新）
            next_t += interval
            delay = next_t - time.monotonic()
            if delay < -interval:
                next_t = time.monotonic()  # 落后超过一个周期则重对齐，防雪崩追赶
                delay = 0.0
            await asyncio.sleep(max(0.0, delay))

    def _poll_mix_finished(self) -> None:
        # mix 完成消费（对齐 UI _tick 的消费段）：take_mix_finished → 来曲 meta
        # 滚动 + 自动模式 on_mix_started 链式装填 + mix_started 事件帧
        for letter in ("a", "b"):
            deck = getattr(self.engine, f"deck_{letter}")
            if not deck.take_mix_finished():
                continue
            incoming = self._pending_prepare.get(letter)
            finished_meta = self._deck_meta.get(letter)
            if incoming is not None:
                # 来曲 meta 滚动（entry 含 record——automix 评分字段齐）
                self._deck_meta[letter] = {
                    "path": incoming["path"],
                    "bpm": float(incoming.get("bpm") or 0.0),
                    "key": str(incoming.get("key") or "?"),
                    "energy": incoming.get("energy", 0),
                    "timbre": incoming.get("timbre"),
                    "downbeats": list(incoming.get("record", {}).get("downbeats", [])),
                }
                self._pending_prepare[letter] = None
            finished_path = (finished_meta or {}).get("path", "")
            now_meta = self._deck_meta.get(letter) or {}
            chain: dict | None = None
            if self.automix is not None and self.automix.auto_mode:
                chain = self.automix.on_mix_started(deck, finished_path)
                if chain is not None:
                    self._pending_prepare[letter] = chain
            self._broadcast_json(
                {
                    "type": "mix_started",
                    "deck": letter,
                    "now": now_meta.get("path", ""),
                    "now_name": Path(now_meta.get("path", "未装载")).name,
                    "finished": finished_path,
                    "chained": bool(chain),
                }
            )
            _logger.info("mix 完成 DECK %s：now=%s", letter.upper(), now_meta.get("path", ""))

    def _tick_frame(self) -> dict:
        # 组装状态帧：两盘状态 + 顶级 UI 状态回显（target/量程/sync/fx/监听）
        vu = self.engine.vu_levels() or []
        return {
            "type": "tick",
            "t": time.monotonic(),
            "a": self._deck_state(self.engine.deck_a, vu[0] if len(vu) > 0 else 0.0),
            "b": self._deck_state(self.engine.deck_b, vu[1] if len(vu) > 1 else 0.0),
            "target": self._target,
            "tempo_range": dict(self._tempo_range),
            "sync": dict(self._sync_on),
            "fx": dict(self._fx),
            "cue_active": self._cue_active,
        }

    def _deck_state(self, deck, vu: float) -> dict:
        # 单盘状态快照：position/duration 样本转秒（前端友好）+ 灯态数组
        state = getattr(deck, "state", "idle")
        if hasattr(state, "value"):
            state = state.value
        slots = self.slot_count
        return {
            "state": str(state),
            "paused": bool(getattr(deck, "paused", True)),
            "position": float(getattr(deck, "position", 0)) / SAMPLE_RATE,
            "duration": float(getattr(deck, "duration", 0)) / SAMPLE_RATE,
            "bpm": float(getattr(deck, "bpm", 0.0) or 0.0),
            "cue": float(getattr(deck, "cue_seconds", 0.0) or 0.0),
            "vu": round(float(vu), 3),
            "tempo_rate": float(getattr(deck, "tempo_rate", 1.0)),
            "key_shift": int(getattr(deck, "key_shift", 0)),
            "keylock": bool(getattr(deck, "_keylock_on", False)),
            "loop": bool(deck.loop_active()) if hasattr(deck, "loop_active") else False,
            "slip": bool(deck.slip_active()) if hasattr(deck, "slip_active") else False,
            "hot_cues": [
                bool(deck.hot_cue_state(i)["has"]) for i in range(slots)
            ],
            "sampler_loaded": [
                bool(deck.sample_state(i)["loaded"]) for i in range(slots)
            ],
        }

    # --- 指令实现（v1 路由 8 条） ---

    def _req_deck(self, args: dict):
        # 盘参数校验：'a'/'b' → 引擎 deck 对象（非法即 bad_args）
        letter = str(args.get("deck") or "").lower()
        if letter not in ("a", "b"):
            raise GatewayError(E_BAD_ARGS, "deck 必须是 'a' 或 'b'")
        return getattr(self.engine, f"deck_{letter}")

    @staticmethod
    def _req_float(args: dict, key: str) -> float:
        # 必填浮点参数宽容解析：None/非数值即 bad_args
        try:
            return float(args.get(key))
        except (TypeError, ValueError):
            raise GatewayError(E_BAD_ARGS, f"{key} 必须是数值") from None

    @staticmethod
    def _clamp01(v: float) -> float:
        # 音量/横推域钳制 0..1
        return max(0.0, min(1.0, float(v)))

    async def _cmd_load(self, args: dict) -> dict:
        # load {deck, path, bpm?}：解码（线程池）→ 装填播放 → BPM 对齐；
        # 曲库命中时补全 bpm/downbeats 并记录盘 meta（automix now_meta 数据源）
        deck = self._req_deck(args)
        letter = str(args.get("deck") or "").lower()
        path = str(args.get("path") or "").strip()
        if not path:
            raise GatewayError(E_BAD_ARGS, "path 不能为空")
        try:
            audio = await asyncio.to_thread(self.engine.load_audio, path)
        except GatewayError:
            raise
        except Exception as exc:
            raise GatewayError(E_ENGINE, f"加载失败: {exc}") from exc
        deck.play(audio)
        entry = self._entry_by_path(path)
        bpm = args.get("bpm")
        if bpm is None and entry is not None:
            bpm = entry.get("bpm") or 0.0
        if bpm:
            deck.set_tempo(float(bpm))
        downbeats = list((entry or {}).get("record", {}).get("downbeats", []))
        # 记录盘 meta（对齐 UI _make_deck_meta：automix 评分与 mix 完成滚动用）
        self._deck_meta[letter] = {
            "path": path,
            "bpm": float(bpm or 0.0),
            "key": str((entry or {}).get("key", "?")),
            "energy": (entry or {}).get("energy", 0),
            "timbre": (entry or {}).get("timbre"),
            "downbeats": downbeats,
        }
        duration = len(audio) / SAMPLE_RATE
        _logger.info("load %s（%.1fs）", path, duration)
        return {
            "duration": duration,
            "bpm": float(getattr(deck, "bpm", 0.0) or 0.0),
            "downbeats": downbeats,
            "name": str((entry or {}).get("name") or Path(path).name),
        }

    def _entry_by_path(self, path: str) -> dict | None:
        # 曲库条目查找（path 精确匹配）
        return next((e for e in self._entries if e["path"] == path), None)

    # --- 曲库 / 分析 / 波形（PL005：扫描即读缓存，后台分析事件帧回填） ---

    def _entry_from_record(self, path: str, rec: dict | None) -> dict:
        # 缓存记录/空记录 → 曲库条目（name/record 全量保留，前端与 automix 共用）
        rec = rec or {}
        return {
            "path": path,
            "name": Path(path).name,
            "bpm": float(rec.get("bpm") or 0.0),
            "key": str(rec.get("key") or "?"),
            "energy": rec.get("energy", 0),
            "timbre": rec.get("timbre"),
            "record": {
                "downbeats": list(rec.get("downbeats", [])),
                "cues": list(rec.get("cues", [])),
            },
            "analyzed": bool(rec),
        }

    def _cmd_library_scan(self, args: dict) -> dict:
        # library_scan {folder}：扫描目录 → 缓存命中填充 → 启动后台分析
        # （事件帧 analysis 逐曲回填 + analysis_done；fake 模式合成条目即时回填）
        folder = str(args.get("folder") or "").strip()
        if not folder:
            raise GatewayError(E_BAD_ARGS, "folder 不能为空")
        if self._analyzing:
            raise GatewayError(E_BAD_STATE, "已有分析任务进行中（等待完成或重启网关）")
        if self.use_fake:
            # 假件快速模式：合成 5 条条目（不触盘不分析，评分链路可跑）
            self._entries = [self._fake_entry(f"{folder.rstrip('/\\')}/track_{i}.mp3") for i in range(1, 6)]
            return {"files": [self._public_entry(e) for e in self._entries], "analyzing": False}
        from modules.analyzer import AnalysisCache, scan_folder  # 重依赖延迟导入

        try:
            paths = scan_folder(folder)
        except Exception as exc:
            raise GatewayError(E_ENGINE, f"扫描失败: {exc}") from exc
        cache = AnalysisCache()
        try:
            self._entries = []
            for p in paths:
                rec = cache.get(p, require_cues=False)
                self._entries.append(self._entry_from_record(p, rec))
        finally:
            cache.close()
        self._start_analysis([e["path"] for e in self._entries if not e["analyzed"]])
        return {"files": [self._public_entry(e) for e in self._entries], "analyzing": self._analyzing}

    @staticmethod
    def _fake_entry(path: str) -> dict:
        # 假条目：固定 BPM 梯度（120 起）+ 标准调性（评分可跑）
        i = abs(hash(path)) % 12
        bpm = 120.0 + (i % 6) * 2.0
        rec = {
            "bpm": bpm,
            "key": f"{(i % 12) + 1}A",
            "energy": 3 + (i % 3),
            "timbre": [0.4 + 0.01 * (i % 5)] * 13,
            "downbeats": [int(k * 60.0 / bpm * SAMPLE_RATE) for k in range(32)],
        }
        return {
            "path": path,
            "name": Path(path).name,
            "bpm": bpm,
            "key": rec["key"],
            "energy": rec["energy"],
            "timbre": rec["timbre"],
            "record": {"downbeats": rec["downbeats"], "cues": []},
            "analyzed": True,
        }

    @staticmethod
    def _public_entry(e: dict) -> dict:
        # 条目 → 前端视图（record 内层不外发，downbeats 由 load/waveform 传递）
        return {
            "path": e["path"],
            "name": e["name"],
            "bpm": e["bpm"],
            "key": e["key"],
            "energy": e["energy"],
            "analyzed": e["analyzed"],
        }

    def _start_analysis(self, paths: list[str]) -> None:
        # 后台线程分析编排：analyze_many 回调 → 事件帧（asyncio.run_coroutine_threadsafe
        # 跨线程投递）；单曲失败事件帧 error 不中断整批（analyzer 内建降级）
        if not paths:
            return
        loop = asyncio.get_running_loop()
        self._analyzing = True
        self._analysis_stop = False

        def on_result(path: str, rec: dict | None, err: Exception | None) -> None:
            # 分析回调（工作线程）：更新条目 + 事件帧（跨线程投递到事件循环）
            entry = self._entry_by_path(path)
            if entry is not None and rec is not None:
                upd = self._entry_from_record(path, rec)
                entry.update({k: upd[k] for k in ("bpm", "key", "energy", "timbre", "record", "analyzed")})
            frame = {
                "type": "analysis",
                "path": path,
                "name": Path(path).name,
                "ok": err is None and rec is not None,
                "bpm": float((rec or {}).get("bpm") or 0.0),
                "key": str((rec or {}).get("key") or "?"),
                "energy": (rec or {}).get("energy", 0),
                "error": "" if err is None else str(err),
            }
            loop.call_soon_threadsafe(self._broadcast_json, frame)

        def worker() -> None:
            from modules.analyzer import analyze_many  # 重依赖延迟导入（工作线程内）

            try:
                succeeded = analyze_many(
                    paths,
                    on_result,
                    use_cache=True,
                    should_stop=lambda: self._analysis_stop,
                )
                loop.call_soon_threadsafe(
                    self._broadcast_json,
                    {"type": "analysis_done", "succeeded": succeeded, "total": len(paths)},
                )
            finally:
                loop.call_soon_threadsafe(self._analysis_finished)

        threading.Thread(target=worker, name="gateway-analysis", daemon=True).start()

    def _analysis_finished(self) -> None:
        # 分析收尾（事件循环线程）
        self._analyzing = False

    def _broadcast_json(self, frame: dict) -> None:
        # 广播 JSON 帧（工作线程经 call_soon_threadsafe 进入；队列满丢弃+warning）
        raw = json.dumps(frame)
        for conn in list(self._clients):
            try:
                conn.queue.put_nowait(raw)
            except asyncio.QueueFull:
                _logger.warning("客户端出站队列满，事件帧丢弃")

    async def _cmd_waveform(self, args: dict) -> dict:
        # waveform {path}：解码 → 峰值降采样 → 元数据帧 + 二进制帧成对下发
        # （复用 build_peaks 公共实现；峰值列数取请求 width 钳 200..4000）
        path = str(args.get("path") or "").strip()
        if not path:
            raise GatewayError(E_BAD_ARGS, "path 不能为空")
        width = int(args.get("width") or 2000)
        width = max(200, min(4000, width))
        try:
            audio = await asyncio.to_thread(self.engine.load_audio, path)
        except Exception as exc:
            raise GatewayError(E_ENGINE, f"解码失败: {exc}") from exc
        peaks = await asyncio.to_thread(build_peaks, audio, width)
        entry = self._entry_by_path(path)
        # 二进制帧入队必须在元数据帧之后（同队列顺序保证成对到达）
        meta = {
            "type": "wave",
            "path": path,
            "width": width,
            "duration": len(audio) / SAMPLE_RATE,
            "bpm": float((entry or {}).get("bpm") or 0.0),
            "downbeats": list((entry or {}).get("record", {}).get("downbeats", [])),
        }
        for conn in list(self._clients):
            try:
                conn.queue.put_nowait(json.dumps(meta))
                conn.queue.put_nowait(peaks_bytes(peaks))
            except asyncio.QueueFull:
                pass  # 慢客户端丢整对（前端可重新请求，容错登记见说明区）
        return {"width": width, "duration": len(audio) / SAMPLE_RATE}

    def _cmd_play(self, args: dict) -> dict:
        # play {deck}：幂等播放（已播放则无操作；pause 为 toggle，故仅暂停时翻转）
        deck = self._req_deck(args)
        if deck.paused:
            deck.pause()
        return {"playing": not deck.paused}

    def _cmd_pause(self, args: dict) -> dict:
        # pause {deck}：幂等暂停（已暂停则无操作）
        deck = self._req_deck(args)
        if not deck.paused:
            deck.pause()
        return {"paused": deck.paused}

    def _cmd_cue(self, args: dict) -> dict:
        # cue {deck}：设置 CUE 并回到 CUE（对齐 UI 按钮语义：先设后回）
        deck = self._req_deck(args)
        deck.cue_set()
        deck.cue_play()
        return {"cue_seconds": float(getattr(deck, "cue_seconds", 0.0))}

    def _cmd_seek(self, args: dict) -> dict:
        # seek {deck, seconds}：秒 → 样本定位（负值钳 0）
        deck = self._req_deck(args)
        seconds = self._req_float(args, "seconds")
        samples = int(max(0.0, seconds) * SAMPLE_RATE)
        deck.set_position_samples(samples)
        return {"position": float(deck.position) / SAMPLE_RATE}

    def _cmd_set_volume(self, args: dict) -> dict:
        # set_volume {volume}：主音量 0..2（>1 boost；对齐 UI RotaryKnob(0,2) 域）
        v = self._req_float(args, "volume")
        v = max(0.0, min(2.0, v))
        self.engine.set_volume(v)
        return {"volume": v}

    def _cmd_set_xfader(self, args: dict) -> dict:
        # set_xfader {position}：横推 -1..1（-1=A 全出，0=居中，1=B 全出；
        # 对齐 Crossfader.set_position 的 [-1,1] 钳制）
        v = self._req_float(args, "position")
        v = max(-1.0, min(1.0, v))
        self.engine.crossfader.set_position(v)
        return {"position": v}

    def _cmd_mix(self, args: dict) -> dict:
        # mix {deck}：tm 未接入报 not_ready；接入后调 tm.mix_now(deck)
        deck = self._req_deck(args)
        if self.tm is None:
            raise GatewayError(E_NOT_READY, "转场管理未接入（PL005 曲库层接入时注入）")
        triggered = bool(self.tm.mix_now(deck))
        return {"triggered": triggered}

    # --- TEMPO / Sync / 循环（PL004 对照 main_window _on_tempo/_on_sync/_loop_action） ---

    def _cmd_set_tempo_rate(self, args: dict) -> dict:
        # set_tempo_rate {deck, rate}：乐速倍率（前端 TEMPO 推子按量程换算）；
        # 手动变速解除该盘 Beat Sync（UI 同款语义）
        deck = self._req_deck(args)
        rate = self._req_float(args, "rate")
        deck.set_tempo_rate(rate)
        letter = str(args.get("deck") or "").lower()
        if self._sync_on.get(letter):
            self._sync_on[letter] = False
        return {"rate": float(getattr(deck, "tempo_rate", rate))}

    def _cmd_cycle_tempo_range(self, args: dict) -> dict:
        # cycle_tempo_range {deck}：量程循环 ±6/±10/±16/WIDE（网关侧状态）
        letter = str(args.get("deck") or "").lower()
        if letter not in ("a", "b"):
            raise GatewayError(E_BAD_ARGS, "deck 必须是 'a' 或 'b'")
        ranges = self._tempo_ranges
        cur = self._tempo_range[letter]
        idx = ranges.index(cur) if cur in ranges else 0
        nxt = ranges[(idx + 1) % len(ranges)]
        self._tempo_range[letter] = nxt
        return {"range": nxt, "wide": nxt >= 100, "label": "WIDE" if nxt >= 100 else f"±{nxt}%"}

    def _cmd_set_sync(self, args: dict) -> dict:
        # set_sync {deck, on}：对齐另一盘有效 BPM（钳当前量程；BPM 未知报 bad_state）
        letter = str(args.get("deck") or "").lower()
        deck = self._req_deck(args)
        on = bool(args.get("on"))
        if not on:
            self._sync_on[letter] = False
            return {"synced": False}
        other_letter = "b" if letter == "a" else "a"
        other_deck = getattr(self.engine, f"deck_{other_letter}")
        target = float(getattr(other_deck, "effective_bpm", 0.0) or 0.0)
        my_bpm = float(getattr(deck, "bpm", 0.0) or 0.0)
        if my_bpm <= 0 or target <= 0:
            self._sync_on[letter] = False
            raise GatewayError(E_BAD_STATE, "Beat Sync 失败：双方需已知 BPM")
        pct = self._tempo_range[letter] / 100.0
        rate = max(1.0 - pct, min(1.0 + pct, target / my_bpm))
        deck.set_tempo_rate(rate)
        self._sync_on[letter] = True
        return {"synced": True, "rate": rate, "target": target}

    def _cmd_set_loop(self, args: dict) -> dict:
        # set_loop {deck, on}：循环开关
        self._req_deck(args).set_loop(bool(args.get("on")))
        return {"on": bool(args.get("on"))}

    def _cmd_loop(self, args: dict) -> dict:
        # loop {deck, action}：in/out/halve/double 四动作分发
        deck = self._req_deck(args)
        action = str(args.get("action") or "")
        actions = {
            "in": deck.loop_in,
            "out": deck.loop_out,
            "halve": deck.loop_halve,
            "double": deck.loop_double,
        }
        if action not in actions:
            raise GatewayError(E_BAD_ARGS, "action 必须是 in/out/halve/double")
        actions[action]()
        return {"action": action, "loop_active": bool(deck.loop_active())}

    def _cmd_beatloop(self, args: dict) -> dict:
        # beatloop {deck, beats}：按当前盘 BPM 设拍循环（BPM 未知报 bad_state）
        deck = self._req_deck(args)
        beats = int(args.get("beats") or 0)
        if beats <= 0:
            raise GatewayError(E_BAD_ARGS, "beats 必须为正整数")
        bpm = float(getattr(deck, "bpm", 0.0) or 0.0)
        if bpm <= 0:
            raise GatewayError(E_BAD_STATE, "当前盘 BPM 未知，无法 Beatloop")
        deck.set_beatloop(beats, bpm)
        return {"beats": beats, "bpm": bpm}

    # --- 表演键（PL004 对照 main_window 表演键区 + tap） ---

    def _cmd_set_keylock(self, args: dict) -> dict:
        # set_keylock {deck, on}：变速不变调开关（rubberband 后台重渲染）
        self._req_deck(args).set_keylock(bool(args.get("on")))
        return {"on": bool(args.get("on"))}

    def _cmd_set_key_shift(self, args: dict) -> dict:
        # set_key_shift {deck, semitones}：移调（钳 ±key_shift_max）
        deck = self._req_deck(args)
        semi = int(args.get("semitones") or 0)
        semi = max(-int(_BASE.get("key_shift_max", 12)), min(int(_BASE.get("key_shift_max", 12)), semi))
        deck.set_key_shift(semi)
        return {"semitones": int(getattr(deck, "key_shift", semi))}

    def _cmd_slip(self, args: dict) -> dict:
        # slip {deck, on}：滑行模式
        self._req_deck(args).slip_toggle(bool(args.get("on")))
        return {"on": bool(args.get("on"))}

    def _cmd_censor(self, args: dict) -> dict:
        # censor {deck, on}：消音
        self._req_deck(args).censor(bool(args.get("on")))
        return {"on": bool(args.get("on"))}

    def _cmd_stutter(self, args: dict) -> dict:
        # stutter {deck}：结巴重复（按下触发）
        self._req_deck(args).stutter()
        return {"ok_pressed": True}

    def _cmd_tap(self, args: dict) -> dict:
        # tap {deck}：点按测速（返回当前测得 BPM，0=未成拍）
        bpm = float(self._req_deck(args).tap() or 0.0)
        return {"bpm": bpm}

    # --- Mixer（PL004 对照 trim/EQ/fader start/instant doubles/目标盘） ---

    def _cmd_set_pregain(self, args: dict) -> dict:
        # set_pregain {deck, gain}：TRIM 前级增益
        deck = self._req_deck(args)
        gain = self._req_float(args, "gain")
        deck.set_pregain(gain)
        return {"gain": gain}

    def _cmd_set_eq(self, args: dict) -> dict:
        # set_eq {deck, band, gain}：三频 EQ（band = low/mid/high）
        deck = self._req_deck(args)
        band = str(args.get("band") or "")
        gain = self._req_float(args, "gain")
        setters = {"low": deck.eq.set_low, "mid": deck.eq.set_mid, "high": deck.eq.set_high}
        if band not in setters:
            raise GatewayError(E_BAD_ARGS, "band 必须是 low/mid/high")
        setters[band](gain)
        return {"band": band, "gain": gain}

    def _cmd_fader_start(self, args: dict) -> dict:
        # fader_start {on}：推子启动开关（全局）
        self.engine.set_fader_start(bool(args.get("on")))
        return {"on": bool(args.get("on"))}

    async def _cmd_instant_doubles(self, args: dict) -> dict:
        # instant_doubles {deck, path}：复制曲目到另一盘同位置（UI E2.6 语义）
        deck = self._req_deck(args)
        path = str(args.get("path") or "").strip()
        if not path:
            raise GatewayError(E_BAD_ARGS, "path 不能为空")
        letter = str(args.get("deck") or "").lower()
        other = getattr(self.engine, f"deck_{'b' if letter == 'a' else 'a'}")
        try:
            audio = await asyncio.to_thread(self.engine.load_audio, path)
        except Exception as exc:
            raise GatewayError(E_ENGINE, f"加载失败: {exc}") from exc
        other.play(audio)
        other.set_position_samples(int(getattr(deck, "position", 0)))
        return {"position": float(other.position) / SAMPLE_RATE}

    def _cmd_set_target(self, args: dict) -> dict:
        # set_target {deck}：目标盘切换（mix/prepare 的 now 盘语义）
        letter = str(args.get("deck") or "").lower()
        if letter not in ("a", "b"):
            raise GatewayError(E_BAD_ARGS, "deck 必须是 'a' 或 'b'")
        self._target = letter
        return {"target": self._target}

    # --- Jog（PL004 对照 jog 三类 + 弯音） ---

    def _cmd_jog_touch(self, args: dict) -> dict:
        # jog_touch {deck, on}：转盘触摸态（按下重置搓碟基准，松手 slip 落回）
        self._req_deck(args).jog_touch(bool(args.get("on")))
        return {"on": bool(args.get("on"))}

    def _cmd_jog_scratch(self, args: dict) -> dict:
        # jog_scratch {deck, delta}：搓碟位移（样本，块内平滑消费）
        self._req_deck(args).jog_scratch(int(args.get("delta") or 0))
        return {"position": float(self._req_deck(args).position) / SAMPLE_RATE}

    def _cmd_jog_bend(self, args: dict) -> dict:
        # jog_bend {deck, rate}：弯音速率（钳 ±jog_bend_max；前端管累积与超时归零）
        deck = self._req_deck(args)
        rate = self._req_float(args, "rate")
        bend_max = float(_BASE.get("jog_bend_max", 0.5))
        deck.jog_bend(max(-bend_max, min(bend_max, rate)))
        return {"rate": rate}

    def _cmd_jog_search(self, args: dict) -> dict:
        # jog_search {deck, rate}：SHIFT 高速搜索（钳 ±jog_search_max）
        deck = self._req_deck(args)
        rate = self._req_float(args, "rate")
        search_max = float(_BASE.get("jog_search_max", 16.0))
        deck.jog_search(max(-search_max, min(search_max, rate)))
        return {"rate": rate}

    # --- Pad（PL004 对照 _on_pad 五模式直译；shift 为显式参数） ---

    def _cmd_pad(self, args: dict) -> dict:
        # pad {deck, idx, mode, shift}：五模式分发（Hot Cue/Beat Loop/Beat Jump/
        # Sampler/Key Shift；语义逐条对齐 main_window._on_pad）
        deck = self._req_deck(args)
        letter = str(args.get("deck") or "").lower()
        idx = int(args.get("idx") or 0)
        mode = str(args.get("mode") or "")
        shift = bool(args.get("shift"))
        slots = self.slot_count
        if idx < 0 or idx >= slots:
            raise GatewayError(E_BAD_ARGS, f"idx 超出 0..{slots - 1}")
        if mode == "Hot Cue":
            if shift:
                deck.hot_cue_clear(idx)
            elif deck.hot_cue_state(idx)["has"]:
                deck.hot_cue_play(idx)
            else:
                deck.hot_cue_set(idx)
            return {"mode": mode, "idx": idx, "has": bool(deck.hot_cue_state(idx)["has"])}
        if mode == "Beat Loop":
            if shift:
                deck.set_loop(False)
                return {"mode": mode, "loop_off": True}
            # 拍梯（对齐 beat_fx_widget BEAT_LADDER [1,2,4,8,16,32]——UI 层常量，
            # 网关不可 import ui/，此处同值对齐并在协议文档注明）
            beat_ladder = [1, 2, 4, 8, 16, 32]
            bpm = float(getattr(deck, "bpm", 0.0) or 0.0)
            if bpm <= 0:
                raise GatewayError(E_BAD_STATE, "当前盘 BPM 未知，无法 Beatloop")
            deck.set_beatloop(beat_ladder[idx % len(beat_ladder)], bpm)
            return {"mode": mode, "idx": idx, "beats": beat_ladder[idx % len(beat_ladder)]}
        if mode == "Beat Jump":
            step = [1, 2, 4, 8][idx % 4]
            direction = -1 if idx < 4 else 1
            deck.beat_jump(direction * step, align=True)
            return {"mode": mode, "idx": idx, "jump": direction * step}
        if mode == "Sampler":
            if shift:
                deck.sample_unload(idx)
            elif deck.sample_state(idx)["loaded"]:
                deck.sample_play(idx)
            # 未装填且无 shift：仅返回 loaded=false 提示（UI 同款：无装填入口提示）
            return {"mode": mode, "idx": idx, "loaded": bool(deck.sample_state(idx)["loaded"])}
        if mode == "Key Shift":
            # FLX4 语义半音表（对齐 main_window：slot1-8 → 0/+1/+2/+3/-3/-2/-1/0）
            semitone_table = [0, 1, 2, 3, -3, -2, -1, 0]
            if idx >= len(semitone_table):
                return {"mode": mode, "idx": idx, "ignored": True}
            semitones = semitone_table[idx]
            if shift:
                deck.set_key_shift(int(getattr(deck, "key_shift", 0)) + semitones if semitones else 0)
            else:
                deck.set_key_shift(semitones)
            return {"mode": mode, "idx": idx, "key_shift": int(getattr(deck, "key_shift", 0))}
        raise GatewayError(E_BAD_ARGS, f"未知 Pad 模式: {mode}")

    # --- Beat FX（PL004 对照 beat fx 组状态 + 通道应用） ---

    def _fx_channel_decks(self) -> list:
        # FX 通道 → 目标盘列表（1/2/both，对齐 main_window._fx_channel_decks）
        return {
            "1": [self.engine.deck_a],
            "2": [self.engine.deck_b],
            "both": [self.engine.deck_a, self.engine.deck_b],
        }.get(self._fx["channel"], [self.engine.deck_a])

    def _apply_fx(self) -> None:
        # 按网关 fx 状态应用到通道盘（清非通道盘防残留——UI 同款）
        for d in (self.engine.deck_a, self.engine.deck_b):
            if d not in self._fx_channel_decks():
                d.set_fx("", 0.0)
        for d in self._fx_channel_decks():
            if self._fx["on"] and self._fx["effect"]:
                d.set_fx(self._fx["effect"], self._fx["depth"])
            else:
                d.set_fx("", 0.0)

    def _cmd_set_fx(self, args: dict) -> dict:
        # set_fx {effect, depth, on}：效果/深度/开关三参全量应用（前端持完整状态）
        if "effect" in args:
            self._fx["effect"] = str(args.get("effect") or "")
        if "depth" in args:
            self._fx["depth"] = max(0.0, min(1.0, float(args.get("depth") or 0.0)))
        if "on" in args:
            self._fx["on"] = bool(args.get("on"))
        self._apply_fx()
        return {"fx": dict(self._fx)}

    def _cmd_set_fx_channel(self, args: dict) -> dict:
        # set_fx_channel {channel}：通道切换（1/2/both；切后清旧+应用新）
        ch = str(args.get("channel") or "")
        if ch not in ("1", "2", "both"):
            raise GatewayError(E_BAD_ARGS, "channel 必须是 1/2/both")
        self._fx["channel"] = ch
        self._apply_fx()
        return {"fx": dict(self._fx)}

    def _cmd_set_fx_beats(self, args: dict) -> dict:
        # set_fx_beats {beats}：拍数（Echo/Delay 延迟 = beats/4 拍）
        beats = int(args.get("beats") or 0)
        if beats <= 0:
            raise GatewayError(E_BAD_ARGS, "beats 必须为正整数")
        self._fx["beats"] = beats
        for d in (self.engine.deck_a, self.engine.deck_b):
            d.set_fx_beats(beats)
        return {"beats": beats}

    def _cmd_fx_auto(self, args: dict) -> dict:
        # fx_auto：以通道盘曲目 BPM 为 FX 时基（通道内存在无 BPM 盘报 bad_state）
        decks = self._fx_channel_decks()
        if any(float(getattr(d, "bpm", 0.0) or 0.0) <= 0 for d in decks):
            raise GatewayError(E_BAD_STATE, "FX AUTO：通道内存在无 BPM 的盘（先加载曲目或 Tap）")
        for d in decks:
            d.set_fx_beats(self._fx["beats"])
        return {"beats": self._fx["beats"]}

    def _cmd_fx_tap(self, args: dict) -> dict:
        # fx_tap：通道第一盘点按测速作为 FX 时基
        bpm = float(self._fx_channel_decks()[0].tap() or 0.0)
        if bpm <= 0:
            raise GatewayError(E_BAD_STATE, "FX TAP：连续点按至少 2 次")
        return {"bpm": bpm}

    # --- Phones 监听（PL004 对照独占切换 + 音量） ---

    def _cmd_phones_preview(self, args: dict) -> dict:
        # phones_preview {deck}：独占切换（再点同盘停止；切盘换源）
        letter = str(args.get("deck") or "").lower()
        if letter not in ("a", "b"):
            raise GatewayError(E_BAD_ARGS, "deck 必须是 'a' 或 'b'")
        player = self.engine.ensure_cue_player()
        if player is None or getattr(player, "is_dead", False):
            raise GatewayError(E_NOT_READY, "耳机监听不可用（无可用输出设备）")
        if self._cue_active == letter:
            player.stop()
            self._cue_active = None
            return {"active": None}
        deck = getattr(self.engine, f"deck_{letter}")
        buf = deck.cue_buffer()
        if buf is None or len(buf) == 0:
            raise GatewayError(E_BAD_STATE, f"DECK {letter.upper()} 无音频可监听")
        player.play(buf)
        self._cue_active = letter
        return {"active": self._cue_active}

    def _cmd_set_phones_volume(self, args: dict) -> dict:
        # set_phones_volume {volume}：监听音量 0..1
        v = self._clamp01(self._req_float(args, "volume"))
        player = self.engine.ensure_cue_player()
        if player is not None:
            player.set_volume(v)
        return {"volume": v}

    # --- 推荐 / Automix（PL004 协议占位；automix 注入后激活——曲库数据 PL005） ---

    def _req_automix(self):
        # automix 控制器校验（未注入报 not_ready——推荐区依赖曲库数据层）
        if self.automix is None:
            raise GatewayError(E_NOT_READY, "自动编排未接入（曲库数据层接入时注入）")
        return self.automix

    def _cmd_recommend(self, args: dict) -> dict:
        # recommend：推荐下一曲（名称 + 中文理由）
        rec = self._req_automix().recommend()
        if rec is None:
            raise GatewayError(E_BAD_STATE, "无可用推荐（当前盘需已知 BPM 且曲库有其他曲目）")
        return {"name": rec["entry"]["name"], "explanation": rec["explanation"]}

    def _cmd_set_automix(self, args: dict) -> dict:
        # set_automix {on}：AUTO 自动接歌开关
        automix = self._req_automix()
        automix.auto_mode = bool(args.get("on"))
        return {"on": bool(automix.auto_mode)}

    def _cmd_prepare_next(self, args: dict) -> dict:
        # prepare_next：以目标盘为 now 预备下一曲（rubberband 烘焙异步——
        # on_done 跨线程投递 prepared 事件帧；返回 entry 即"已受理"）
        automix = self._req_automix()
        now_deck = getattr(self.engine, f"deck_{self._target}")
        target = self._target

        def on_done(err: Exception | None = None) -> None:
            # 闭包捕获 target/entry（prepare_next 返回后迟绑定生效）
            self._on_prepared(target, entry, err)  # noqa: F821

        entry = automix.prepare_next(now_deck, on_done=on_done)
        if entry is None:
            raise GatewayError(E_BAD_STATE, "推荐预备失败（当前盘需 PLAYING 且已知 BPM）")
        self._pending_prepare[target] = entry
        return {"entry": {"path": entry["path"], "name": entry.get("name", "")}}

    def _on_prepared(self, target: str, entry: dict | None, err: Exception | None = None) -> None:
        # 烘焙完成回调（tm 工作线程）：prepared 事件帧跨线程投递（成功/失败中文化）
        frame = {
            "type": "prepared",
            "deck": target,
            "ok": err is None,
            "path": (entry or {}).get("path", ""),
            "name": (entry or {}).get("name", ""),
            "error": "" if err is None else f"烘焙失败: {err}",
        }
        self._loop.call_soon_threadsafe(self._broadcast_json, frame)


async def _run_main(host: str, port: int, use_fake: bool) -> None:
    # CLI 主协程：默认真引擎（真机出声）；--fake 换假引擎（无设备联调）；
    # 真引擎构造/退出全程 try/finally 保证 close（释放音频设备）
    engine = None
    if not use_fake:
        from modules.engine import AudioEngine  # 重依赖延迟导入（sounddevice 设备初始化）

        engine = AudioEngine()
    gw = Gateway(engine=engine, use_fake=use_fake)
    if not use_fake:
        # 真引擎注入 tm 与 automix（mix/推荐/自动接歌指令激活；曲库数据
        # 来自 library_scan 填充的 _entries——闭包迟绑定）
        from modules.automix import AutomixController
        from modules.transition_manager import TransitionManager

        gw.tm = TransitionManager(engine)
        gw.automix = AutomixController(
            gw.tm,
            entries_getter=lambda: gw._entries,
            now_meta_getter=lambda: gw._deck_meta.get(gw._target) or {},
        )
    try:
        actual = await gw.serve(host, port)
        print(f"gateway ready port={actual}", flush=True)  # 就绪握手行（Tauri 读取）
        await asyncio.Event().wait()
    finally:
        await gw.stop()
        if engine is not None:
            engine.close()


def main() -> None:
    # CLI 入口：--host/--port/--fake（--fake 为无音频设备的假引擎模式）
    parser = argparse.ArgumentParser(description="MrAutoDJ WS 网关（Tauri sidecar）")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址（默认 127.0.0.1）")
    parser.add_argument("--port", type=int, default=0, help="监听端口，0=动态分配（默认）")
    parser.add_argument("--fake", action="store_true", help="注入假引擎（无音频设备演示/联调）")
    args = parser.parse_args()
    try:
        asyncio.run(_run_main(args.host, args.port, args.fake))
    except KeyboardInterrupt:
        pass  # Ctrl+C 正常退出


if __name__ == "__main__":
    main()


# ===== modules/gateway.py 模块说明 =====
# 类型：
#   GatewayError(Exception)：网关业务错误（code 协议错误码 + message 中文）
#   FakeDeck/FakeCrossfader/FakeEngine：假引擎族（接口鸭子对齐真引擎，路由不分支）
#   _ClientConn：单客户端出站队列（唯一写出者 sender 协程）
#   Gateway：WS 网关本体（RPC 路由 + 30Hz 推流）
# 协议帧：
#   hello {type, protocol_version, version, sample_rate, tick_hz}——连接即推
#   RPC 入 {id, cmd, args} → 出 {id, ok, result} / {id, ok:false, error:{code,message}}
#   tick {type, t, a:{state,paused,position,duration,bpm,cue,vu}, b:{...}}——30Hz 广播
# 方法：
#   serve(host, port)：启动 WS 服务与推流协程，返回实际端口（port=0 动态分配）
#   stop()：停推流/断客户端/关服务（sidecar 退出路径）
#   _client_loop/_sender/_on_message/_dispatch：连接生命周期与入站分发
#   _tick_loop/_tick_frame/_deck_state：30Hz 固定步长状态推流
#   _cmd_load/play/pause/cue/seek/set_volume/set_xfader/mix：v1 路由 8 条
# 设计理由：
#   引擎零改动——网关只做"读锁内状态 + 调引擎公开方法"，音频回调线程完全独立；
#   出站队列 + 唯一写出者——慢客户端不阻塞 30Hz 推流与其他客户端；
#   假引擎鸭子对齐——CLI --fake 与探针注入复用同一套路由代码，无双分支维护
# 异常处理：
#   指令异常分类归一为错误帧（unknown_cmd/bad_args/not_ready/engine_error/bad_json），
#   绝不向外抛出杀死事件循环；连接断开静默清理（ConnectionClosed 常态）
# 容错登记（对齐 AGENTS.md 错误策略——容错白名单）：
#   ① 慢客户端丢 tick 帧——场景：客户端消费慢于 30Hz 推流；降级行为：队列满时
#      丢弃 tick（状态可自愈，下一帧即最新）；理由：状态推流是装饰层，丢帧优于
#      阻塞推流线程拖垮全部客户端；RPC 响应不丢（满时记 warning）
#   ② 无 cmd 的入站帧静默忽略——场景：非 RPC 噪声/未来帧类型；降级行为：忽略
#      不回错误；理由：协议扩展兼容（事件订阅等后续帧型无需回错误）
# 关联配置：
#   config/static/base.json：gateway_tick_hz（推流频率）、sample_rate（秒↔样本换算）、
#   version（hello 应用版本）
# 关联文档：docs/ipc_protocol.md（协议权威定义，PL003.4）

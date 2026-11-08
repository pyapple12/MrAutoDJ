# WS 网关（PL003）：Tauri sidecar 的 asyncio WebSocket 服务
# 职责：接收 RPC 指令映射引擎方法 + 30Hz 状态推流；引擎零改动（锁语义沿用引擎内部锁）
# 协议：docs/ipc_protocol.md（protocol_version=1）

from __future__ import annotations

import argparse
import asyncio
import json
import time

import numpy as np
import websockets

from config.static.static_config import get_static_config
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


class FakeDeck:
    # 假打碟机：wall-clock 位置推进 + 状态翻转，接口对齐 engine.Deck 公开面
    def __init__(self, lock):
        self._lock = lock
        self._n = 0
        self._pos0 = 0
        self._t0 = 0.0
        self._is_paused = True
        self._cue = 0.0
        self.bpm = 0.0

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

    def set_position_samples(self, samples: int) -> None:
        # seek：重定位（播放中重置推进起点）
        self._pos0 = max(0, int(samples))
        self._t0 = time.monotonic()

    def set_tempo(self, bpm: float) -> None:
        self.bpm = float(bpm or 0.0)

    def cue_set(self) -> None:
        self._cue = self.position / SAMPLE_RATE

    def cue_play(self) -> None:
        self.set_position_samples(int(self._cue * SAMPLE_RATE))

    @property
    def cue_seconds(self) -> float:
        return self._cue


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

    def ensure_cue_player(self) -> None:
        pass

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
    # WS 网关：RPC 路由 + 30Hz 状态推流（引擎注入，tm 可选）
    def __init__(self, engine, tick_hz: int = DEFAULT_TICK_HZ, tm=None, use_fake: bool = False):
        # 引擎注入：use_fake 或 engine 为 None 时用假引擎（CLI --fake / 探针）
        if use_fake or engine is None:
            engine = FakeEngine()
            _logger.info("gateway 使用假引擎（--fake 模式）")
        self.engine = engine
        self.tm = tm
        self.tick_hz = max(1, int(tick_hz))
        self._clients: set[_ClientConn] = set()
        self._server = None
        self._tick_task: asyncio.Task | None = None
        # 指令路由表 v1（PL003.2：8 条，逐条映射引擎方法；锁语义沿用引擎内部锁）
        self._routes = {
            "load": self._cmd_load,
            "play": self._cmd_play,
            "pause": self._cmd_pause,
            "cue": self._cmd_cue,
            "seek": self._cmd_seek,
            "set_volume": self._cmd_set_volume,
            "set_xfader": self._cmd_set_xfader,
            "mix": self._cmd_mix,
        }

    async def serve(self, host: str = "127.0.0.1", port: int = 0) -> int:
        # 启动 WS 服务与推流协程；port=0 动态分配，返回实际端口
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

    def _tick_frame(self) -> dict:
        # 组装状态帧：两盘位置/状态/BPM/CUE/VU（vu_levels 引擎锁内读，短）
        vu = self.engine.vu_levels() or []
        return {
            "type": "tick",
            "t": time.monotonic(),
            "a": self._deck_state(self.engine.deck_a, vu[0] if len(vu) > 0 else 0.0),
            "b": self._deck_state(self.engine.deck_b, vu[1] if len(vu) > 1 else 0.0),
        }

    def _deck_state(self, deck, vu: float) -> dict:
        # 单盘状态快照：position/duration 样本转秒（前端友好）
        state = getattr(deck, "state", "idle")
        if hasattr(state, "value"):
            state = state.value
        return {
            "state": str(state),
            "paused": bool(getattr(deck, "paused", True)),
            "position": float(getattr(deck, "position", 0)) / SAMPLE_RATE,
            "duration": float(getattr(deck, "duration", 0)) / SAMPLE_RATE,
            "bpm": float(getattr(deck, "bpm", 0.0) or 0.0),
            "cue": float(getattr(deck, "cue_seconds", 0.0) or 0.0),
            "vu": round(float(vu), 3),
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
        # load {deck, path, bpm?}：解码（线程池）→ 装填播放 → 可选 BPM 对齐
        deck = self._req_deck(args)
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
        bpm = args.get("bpm")
        if bpm:
            deck.set_tempo(float(bpm))
        duration = len(audio) / SAMPLE_RATE
        _logger.info("load %s（%.1fs）", path, duration)
        return {"duration": duration, "bpm": float(getattr(deck, "bpm", 0.0) or 0.0)}

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
        # set_volume {volume}：主音量 0..1
        v = self._clamp01(self._req_float(args, "volume"))
        self.engine.set_volume(v)
        return {"volume": v}

    def _cmd_set_xfader(self, args: dict) -> dict:
        # set_xfader {position}：横推 0..1（0=A 全出，1=B 全出）
        v = self._clamp01(self._req_float(args, "position"))
        self.engine.crossfader.set_position(v)
        return {"position": v}

    def _cmd_mix(self, args: dict) -> dict:
        # mix {deck}：v1 协议占位——tm 未接入报 not_ready；接入后调 tm.mix_now(deck)
        deck = self._req_deck(args)
        if self.tm is None:
            raise GatewayError(E_NOT_READY, "转场管理未接入（PL003 v1 仅协议占位）")
        triggered = bool(self.tm.mix_now(deck))
        return {"triggered": triggered}


async def _run_main(host: str, port: int, use_fake: bool) -> None:
    # CLI 主协程：默认真引擎（真机出声）；--fake 换假引擎（无设备联调）；
    # 真引擎构造/退出全程 try/finally 保证 close（释放音频设备）
    engine = None
    if not use_fake:
        from modules.engine import AudioEngine  # 重依赖延迟导入（sounddevice 设备初始化）

        engine = AudioEngine()
    gw = Gateway(engine=engine, use_fake=use_fake)
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

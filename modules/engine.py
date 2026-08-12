# 音频引擎模块：双打碟机 + 三频 EQ + 横推 + 主混音 + 双输出监听（M1 核心）

from __future__ import annotations

import threading
from enum import Enum
from typing import Optional

import numpy as np
import sounddevice as sd

from config.static.static_config import get_static_config
from modules.transition import plan_transition, tempo_compatible

# 静态配置解包（AGENTS.md 参数约定：采样率/块大小/通道数零硬编码）
_SC = get_static_config()
SAMPLE_RATE = int(_SC.base.get("sample_rate", 44100))
CHANNELS = int(_SC.base.get("channels", 2))
BLOCK_SIZE = int(_SC.base.get("block_size", 2048))

# 主增益上限（+6dB boost 能力；输出硬限幅 ±1.0 保护设备，B1 约定）
MAX_GAIN = 2.0

# VU 电平环形缓冲长度（每盘；回调每块写一个峰值，UI 定时器读最近值）
VU_BUFFER = 32


class State(Enum):
    # 引擎状态（B1 约定）：IDLE 空闲 / PLAYING 播放 / MIXING 交叉淡化混音中
    IDLE = "idle"
    PLAYING = "playing"
    MIXING = "mixing"


# ---------------------------------------------------------------------------
# RBJ 三频 EQ（D2.7，参考 B1 fx.py：系数 setter 线程算、回调只跑差分方程）
# ---------------------------------------------------------------------------


class Biquad:
    # 通用双二阶滤波器（RBJ audio EQ cookbook 系数；zi 跨块持久）
    def __init__(self, sr: int):
        # 初始化：采样率、系数置 None（旁通）、延迟状态置 None（静止）
        self.sr = sr
        self._b: np.ndarray | None = None
        self._a: np.ndarray | None = None
        self._zi: np.ndarray | None = None

    def _set_coeffs(self, b: np.ndarray, a: np.ndarray) -> None:
        # 更新系数（按 a[0] 归一化；旁通 None 时保持旧 zi；新系数从静止开始防咔嗒）
        if b is None:
            self._b, self._a = None, None
            return
        a0 = a[0]
        self._b = b / a0
        self._a = a / a0
        self._zi = np.zeros((2, 2), dtype=np.float64)

    def low_shelf(self, gain_db: float, freq: float, q: float = 0.707) -> None:
        # 低频架：增益 -30..+6dB（RBJ 公式），旋钮低段用
        A = 10.0 ** (gain_db / 40.0)
        w0 = 2.0 * np.pi * freq / self.sr
        alpha = (
            np.sin(w0) / (2.0 * q) * np.sqrt((A + 1.0 / A) * (1.0 / 1.0 - 1.0) + 2.0)
        )
        cos_w0 = np.cos(w0)
        b = np.array(
            [
                A * ((A + 1.0) - (A - 1.0) * cos_w0 + 2.0 * np.sqrt(A) * alpha),
                2.0 * A * ((A - 1.0) - (A + 1.0) * cos_w0),
                A * ((A + 1.0) - (A - 1.0) * cos_w0 - 2.0 * np.sqrt(A) * alpha),
            ]
        )
        a = np.array(
            [
                (A + 1.0) + (A - 1.0) * cos_w0 + 2.0 * np.sqrt(A) * alpha,
                -2.0 * ((A - 1.0) + (A + 1.0) * cos_w0),
                (A + 1.0) + (A - 1.0) * cos_w0 - 2.0 * np.sqrt(A) * alpha,
            ]
        )
        self._set_coeffs(b, a)

    def high_shelf(self, gain_db: float, freq: float, q: float = 0.707) -> None:
        # 高频架：增益 -30..+6dB（RBJ 公式），旋钮高段用
        A = 10.0 ** (gain_db / 40.0)
        w0 = 2.0 * np.pi * freq / self.sr
        alpha = (
            np.sin(w0) / (2.0 * q) * np.sqrt((A + 1.0 / A) * (1.0 / 1.0 - 1.0) + 2.0)
        )
        cos_w0 = np.cos(w0)
        b = np.array(
            [
                A * ((A + 1.0) + (A - 1.0) * cos_w0 + 2.0 * np.sqrt(A) * alpha),
                -2.0 * A * ((A - 1.0) + (A + 1.0) * cos_w0),
                A * ((A + 1.0) + (A - 1.0) * cos_w0 - 2.0 * np.sqrt(A) * alpha),
            ]
        )
        a = np.array(
            [
                (A + 1.0) - (A - 1.0) * cos_w0 + 2.0 * np.sqrt(A) * alpha,
                2.0 * ((A - 1.0) - (A + 1.0) * cos_w0),
                (A + 1.0) - (A - 1.0) * cos_w0 - 2.0 * np.sqrt(A) * alpha,
            ]
        )
        self._set_coeffs(b, a)

    def peaking(self, gain_db: float, freq: float, q: float = 0.707) -> None:
        # 峰形滤波：增益 -30..+6dB（RBJ 公式），中频段用
        A = 10.0 ** (gain_db / 40.0)
        w0 = 2.0 * np.pi * freq / self.sr
        alpha = np.sin(w0) / (2.0 * q)
        cos_w0 = np.cos(w0)
        b = np.array([1.0 + alpha * A, -2.0 * cos_w0, 1.0 - alpha * A])
        a = np.array([1.0 + alpha / A, -2.0 * cos_w0, 1.0 - alpha / A])
        self._set_coeffs(b, a)

    def highpass(self, cutoff: float, q: float = 0.707) -> None:
        # 高通滤波（RBJ 直接型；Beat FX HPF 用）
        w0 = 2.0 * np.pi * cutoff / self.sr
        alpha = np.sin(w0) / (2.0 * q)
        cos_w0 = np.cos(w0)
        b = np.array([(1.0 + cos_w0) / 2.0, -(1.0 + cos_w0), (1.0 + cos_w0) / 2.0])
        a = np.array([1.0 + alpha, -2.0 * cos_w0, 1.0 - alpha])
        self._set_coeffs(b, a)

    def lowpass(self, cutoff: float, q: float = 0.707) -> None:
        # 低通滤波（RBJ 直接型；Beat FX LPF 用）
        w0 = 2.0 * np.pi * cutoff / self.sr
        alpha = np.sin(w0) / (2.0 * q)
        cos_w0 = np.cos(w0)
        b = np.array([(1.0 - cos_w0) / 2.0, 1.0 - cos_w0, (1.0 - cos_w0) / 2.0])
        a = np.array([1.0 + alpha, -2.0 * cos_w0, 1.0 - alpha])
        self._set_coeffs(b, a)

    def reset(self) -> None:
        # 清除延迟状态（换曲/重开时防滤波振铃串音）
        self._zi = None

    def process(self, x: np.ndarray) -> None:
        # 就地滤波（回调线程；系数 None=旁通）。float64 递归防浮点底噪
        if self._b is None or self._a is None:
            return
        y, self._zi = self._run(x)
        x[:] = y

    def _run(self, x: np.ndarray) -> tuple:
        # 直接 II 型转置（DF2T）差分递推；float64 防浮点底噪；返回 (输出, 状态)
        xd = x.astype(np.float64)
        b, a = self._b, self._a
        if self._zi is None:
            self._zi = np.zeros((2, 2), dtype=np.float64)
        out = np.empty_like(xd)
        for ch in range(2):
            d1, d2 = self._zi[ch]
            for i in range(len(xd)):
                xi = xd[i, ch]
                y = b[0] * xi + d1
                d1 = b[1] * xi - a[1] * y + d2
                d2 = b[2] * xi - a[2] * y
                out[i, ch] = y
            self._zi[ch] = (d1, d2)
        return out.astype(np.float32), self._zi


class DeckEQ:
    # 三频 EQ（DJ 旋钮语义）：low/mid/high 各 [-1,1]，0=unity，+1=+6dB，-1=-30dB 全切
    def __init__(self, sr: int):
        # 初始化三个 RBJ 滤波器（低架 100Hz / 峰形 1kHz / 高架 10kHz）
        self.sr = sr
        self.low = Biquad(sr)
        self.mid = Biquad(sr)
        self.high = Biquad(sr)
        self.low_amt = 0.0
        self.mid_amt = 0.0
        self.high_amt = 0.0

    def set_low(self, amt: float) -> None:
        # 低段旋钮 [-1,1]：系数在 UI 线程算（-30dB..+6dB 映射），回调只跑差分
        self.low_amt = float(np.clip(amt, -1.0, 1.0))
        gain = 6.0 * self.low_amt if self.low_amt >= 0 else -30.0 * abs(self.low_amt)
        if abs(self.low_amt) < 0.01:
            self.low._set_coeffs(None, None)
        else:
            self.low.low_shelf(gain, 100.0)

    def set_mid(self, amt: float) -> None:
        # 中段旋钮（同 set_low 语义）
        self.mid_amt = float(np.clip(amt, -1.0, 1.0))
        gain = 6.0 * self.mid_amt if self.mid_amt >= 0 else -30.0 * abs(self.mid_amt)
        if abs(self.mid_amt) < 0.01:
            self.mid._set_coeffs(None, None)
        else:
            self.mid.peaking(gain, 1000.0)

    def set_high(self, amt: float) -> None:
        # 高段旋钮（同 set_low 语义）
        self.high_amt = float(np.clip(amt, -1.0, 1.0))
        gain = 6.0 * self.high_amt if self.high_amt >= 0 else -30.0 * abs(self.high_amt)
        if abs(self.high_amt) < 0.01:
            self.high._set_coeffs(None, None)
        else:
            self.high.high_shelf(gain, 10000.0)

    def reset(self) -> None:
        # 全部滤波器状态清零（换曲时调用）
        self.low.reset()
        self.mid.reset()
        self.high.reset()

    def process(self, x: np.ndarray) -> None:
        # 就地处理链：低→中→高（回调线程；系数 None 自动旁通）
        self.low.process(x)
        self.mid.process(x)
        self.high.process(x)


# ---------------------------------------------------------------------------
# E1.8 效果库扩展：反馈延迟线（Echo/Delay）
# ---------------------------------------------------------------------------


class FeedbackDelay:
    # 反馈延迟线（Echo/Delay 共用）：预分配环形缓冲，零运行时分配
    # Echo=短延迟高反馈；Delay=长延迟低反馈（多 tap）
    def __init__(self, sr: int, max_delay_seconds: float = 2.0):
        # 初始化：缓冲 = 最大延迟 + 2 块（防读切片越界）；输出缓冲预分配
        self.sr = sr
        self._buf_len = int(max_delay_seconds * sr) + 2 * BLOCK_SIZE
        self._buf = np.zeros((self._buf_len, CHANNELS), dtype=np.float32)
        self._out = np.zeros((BLOCK_SIZE, CHANNELS), dtype=np.float32)
        self._pos = 0
        self._delay = int(0.25 * sr)
        self._feedback = 0.4
        self._n_taps = 1

    def configure(self, delay_seconds: float, feedback: float, n_taps: int = 1) -> None:
        # 配置延迟时长/反馈量/多 tap 数（参数变更防咔嗒：旧缓冲保留继续写）
        self._delay = max(1, int(delay_seconds * self.sr))
        self._feedback = max(0.0, min(0.95, float(feedback)))
        self._n_taps = max(1, min(4, int(n_taps)))

    def process(self, x: np.ndarray, frames: int) -> np.ndarray:
        # 就地处理：out = x + Σ(feedback^tap × 延迟 tap 采样)；返回 x
        # 环形缓冲整块读取（零初始化天然提供初始"未充满"：pos<delay 时读到的
        # 是缓冲尾部零区，无需 start 判断；回绕后恒有效，P1 修复）
        out = self._out[:frames]
        out[:] = x
        for tap in range(1, self._n_taps + 1):
            delay = self._delay * tap
            fb = self._feedback**tap
            read = (self._pos - delay) % self._buf_len
            n1 = min(frames, self._buf_len - read)
            out[:n1] += fb * self._buf[read : read + n1]
            if n1 < frames:  # 回绕到缓冲开头
                out[n1:] += fb * self._buf[0 : frames - n1]
        # 写入（同样处理回绕）
        n1 = min(frames, self._buf_len - self._pos)
        self._buf[self._pos : self._pos + n1] = out[:n1]
        if n1 < frames:
            self._buf[0 : frames - n1] = out[n1:]
        self._pos = (self._pos + frames) % self._buf_len
        x[:] = out
        return x

    def reset(self) -> None:
        # 清空延迟缓冲（换曲/重开时防旧回声）
        self._buf[:] = 0
        self._pos = 0


class Echo(FeedbackDelay):
    # Echo：短延迟（250ms）+ 高反馈（0.6），经典回声
    def __init__(self, sr: int):
        # 初始化反馈延迟线并配置 Echo 参数
        super().__init__(sr)
        self.configure(0.25, 0.6)


class Delay(FeedbackDelay):
    # Delay：长延迟（0.375s≈120BPM 八分音符）+ 中反馈（0.4）+ 3 tap
    def __init__(self, sr: int):
        # 初始化反馈延迟线并配置 Delay 参数
        super().__init__(sr)
        self.configure(0.375, 0.4, n_taps=3)


# ---------------------------------------------------------------------------
# 打碟机（双实例，共享引擎锁）
# ---------------------------------------------------------------------------


class Deck:
    # 单打碟机：状态机 + 播放头 + CUE + 循环 + EQ（锁由 AudioEngine 持有传入）
    def __init__(self, lock: threading.Lock, sr: int = SAMPLE_RATE):
        # 初始化播放状态（全部由引擎锁保护）
        self._lock = lock
        self.sr = sr
        self.state = State.IDLE
        self._now_audio: Optional[np.ndarray] = None
        self._next_audio: Optional[np.ndarray] = None
        self._position: int = 0
        self._mix_pos: int = 0
        self._fade_samples: int = 0
        self._paused: bool = False
        self._pending_mix_at: Optional[int] = None
        self._cue_sample: int = 0
        self._loop_active: bool = False
        self._loop_start: int = 0
        self._loop_end: int = 0
        self.eq = DeckEQ(sr)
        # --- E2 支撑：TRIM 预增益与 Beat FX 链（E1.8 效果库应用） ---
        self._pregain: float = 1.0
        self._fx_effect: str = ""  # "" | HPF | LPF | Trans | Echo | Delay
        self._fx_depth: float = 0.0
        self._fx_filter = Biquad(sr)  # HPF/LPF 复用
        self._fx_delay = FeedbackDelay(sr)
        # --- E1 扩展状态（FLX4 复刻） ---
        # Hot Cue 槽位：slot(0-7) → 样本位置
        self._hot_cues: dict[int, int] = {}
        # 当前曲 BPM（Beat Jump/Tap 用；UI 加载曲目时设置）
        self._bpm: float = 0.0
        # Key Shift 半音（±12，-12..0..+12；实际渲染由预渲染管线执行）
        self._key_shift: int = 0
        # Jog：触摸态 / 弯音速率（±0.5）/ 高速搜索速率（含符号，±16 倍）
        self._jog_touched: bool = False
        self._jog_bend_rate: float = 0.0
        self._jog_search_rate: float = 0.0
        self._last_out_pos: int = -1  # 上次触摸输出位置（手停判定，P3）
        self._scratch_pending: int = 0  # 未消费的搓碟位移（平滑刮擦队列）
        self._scratch_fpos: float = 0.0  # 搓碟浮点播放位置（逐帧渐变）
        # Slip 模式：真实位置暗中推进，播放位置（_position）可被搓碟自由移动
        self._slip_active: bool = False
        self._slip_actual: int = 0
        # Sampler：8 槽音频 + 当前播放 (slot, pos)
        self._samples: dict[int, np.ndarray] = {}
        self._sample_playing: Optional[tuple] = None
        # Tap BPM：时间戳队列（秒）
        self._tap_times: list = []
        # Censor：按住期间反向播放
        self._reverse: bool = False
        # Trans 门控相位（跨块持续）
        self._trans_phase: int = 0

    # --- 传输控制 ---

    def play(self, audio: np.ndarray) -> None:
        # 从头播放整段音频（清状态/CUE 保持/循环关闭/EQ 状态清零）
        with self._lock:
            self._now_audio = audio
            self._position = 0
            self._paused = False
            self.state = State.PLAYING
            self._pending_mix_at = None
            self._next_audio = None
            self._loop_active = False
            self.eq.reset()

    def pause(self) -> None:
        # 暂停/恢复切换
        with self._lock:
            self._paused = not self._paused

    def stop(self) -> None:
        # 停止：清空音频与状态（CUE 保留，EQ 状态清零）
        with self._lock:
            self.state = State.IDLE
            self._now_audio = None
            self._next_audio = None
            self._position = 0
            self._paused = False
            self._pending_mix_at = None
            self._loop_active = False
            self.eq.reset()

    # --- CUE（D2.10） ---

    def cue_set(self) -> None:
        # 在当前播放位置设置 CUE 点
        with self._lock:
            self._cue_sample = self._position

    def cue_set_position(self, seconds: float) -> None:
        # 按秒设置 CUE 点（供 UI 先做 downbeat 吸附再设置）
        with self._lock:
            self._cue_sample = max(0, int(seconds * self.sr))

    def cue_play(self) -> None:
        # 从 CUE 点播放（无音频则忽略）
        with self._lock:
            if self._now_audio is None:
                return
            self._position = min(self._cue_sample, len(self._now_audio))
            self._paused = False
            if self.state == State.IDLE:
                self.state = State.PLAYING
            self._pending_mix_at = None

    @property
    def cue_seconds(self) -> float:
        # CUE 点秒数（UI 显示用）
        return self._cue_sample / self.sr

    # --- E1.1 Hot Cue（8 槽） ---

    def hot_cue_set(self, slot: int) -> None:
        # 存储当前位置到热 CUE 槽（0-7；越界忽略）
        with self._lock:
            if 0 <= slot < 8:
                self._hot_cues[slot] = self._position

    def hot_cue_play(self, slot: int) -> None:
        # 跳转到热 CUE 槽并播放（无音频/槽空忽略）
        with self._lock:
            if 0 <= slot < 8 and slot in self._hot_cues and self._now_audio is not None:
                self._position = min(self._hot_cues[slot], len(self._now_audio))
                self._paused = False
                if self.state == State.IDLE:
                    self.state = State.PLAYING
                self._pending_mix_at = None

    def hot_cue_clear(self, slot: int) -> None:
        # 清除热 CUE 槽（越界忽略）
        with self._lock:
            if 0 <= slot < 8:
                self._hot_cues.pop(slot, None)

    def hot_cue_state(self, slot: int) -> dict:
        # 热 CUE 槽状态（UI 灯态用）：{has, seconds}
        with self._lock:
            sample = self._hot_cues.get(slot)
            return {"has": sample is not None, "seconds": (sample or 0) / self.sr}

    # --- E1.2 Beatgrid 跳转 ---

    def set_tempo(self, bpm: float) -> None:
        # 设置当前曲 BPM（Beat Jump/Tap 计算用；UI 加载曲目时调用）
        with self._lock:
            self._bpm = max(0.0, float(bpm))

    def beat_jump(self, beats: int, align: bool = False) -> None:
        # 按拍跳转：±beats 拍；align=True（Skip 模式）时先对齐最近拍边界
        with self._lock:
            if self._now_audio is None or self._bpm <= 0:
                return
            beat_len = int(60.0 / self._bpm * self.sr)
            target = self._position + beats * beat_len
            if align:
                target = target - (target % beat_len)
            self._position = max(0, min(target, len(self._now_audio)))

    # --- E1.3 Key Shift 半音 ---

    def set_key_shift(self, semitones: int) -> None:
        # 设置 Key Shift（钳制 ±12；仅存状态，实际变调渲染由预渲染管线执行）
        with self._lock:
            self._key_shift = max(-12, min(12, int(semitones)))

    @property
    def key_shift(self) -> int:
        # 当前 Key Shift 半音数（UI 显示/灯态）
        return self._key_shift

    # --- E1.4 Jog 转盘接口 ---

    def jog_touch(self, on: bool) -> None:
        # 设置转盘触摸态（搓碟/弯音判定依据）；按下时重置浮点基准
        # （未拖动即静音）；Slip 中松手 → 播放位置落回暗中前进的真实位置
        with self._lock:
            self._jog_touched = bool(on)
            if on:
                self._scratch_fpos = float(self._position)
                self._scratch_pending = 0
            if not on and self._slip_active and self._now_audio is not None:
                self._position = min(self._slip_actual, len(self._now_audio))

    def jog_scratch(self, delta_samples: int) -> None:
        # 搓碟：位移入队（平滑刮擦在音频块内逐帧消费；正=向前/负=倒放）
        with self._lock:
            if self._now_audio is None:
                return
            self._scratch_pending += int(delta_samples)

    def jog_bend(self, rate: float) -> None:
        # 弯音：临时播放速率偏移（±0.5；0=恢复原速）
        with self._lock:
            self._jog_bend_rate = max(-0.5, min(0.5, float(rate)))

    def jog_search(self, rate: float) -> None:
        # SHIFT 高速搜索：速率倍数（±16；0=停止）
        with self._lock:
            self._jog_search_rate = max(-16.0, min(16.0, float(rate)))

    # --- E1.6 Slip 模式 ---

    def slip_toggle(self, active: bool) -> None:
        # 开关 Slip：开启时记录真实位置（暗中推进），关闭时播放位置落回真实位置
        with self._lock:
            if active and not self._slip_active:
                self._slip_actual = self._position
            elif not active and self._slip_active:
                if self._now_audio is not None:
                    self._position = min(self._slip_actual, len(self._now_audio))
            self._slip_active = bool(active)

    @property
    def slip_active(self) -> bool:
        # Slip 状态（UI 灯态）
        return self._slip_active

    # --- E1.7 Sampler 槽位 ---

    def sample_load(self, slot: int, audio: np.ndarray) -> None:
        # 载入采样到槽位（0-7；停止当前播放并替换）
        with self._lock:
            if 0 <= slot < 8 and audio is not None and len(audio) > 0:
                self._samples[slot] = audio
                if self._sample_playing is not None and self._sample_playing[0] == slot:
                    self._sample_playing = None

    def sample_play(self, slot: int) -> None:
        # 播放槽位采样（若已在播则从头重播；只同时播一个）
        with self._lock:
            if 0 <= slot < 8 and slot in self._samples:
                self._sample_playing = (slot, 0)

    def sample_stop(self, slot: int) -> None:
        # 停止槽位采样播放
        with self._lock:
            if self._sample_playing is not None and self._sample_playing[0] == slot:
                self._sample_playing = None

    def sample_unload(self, slot: int) -> None:
        # 卸载槽位采样（同时停止播放）
        with self._lock:
            if 0 <= slot < 8:
                self._samples.pop(slot, None)
                if self._sample_playing is not None and self._sample_playing[0] == slot:
                    self._sample_playing = None

    def sample_state(self, slot: int) -> dict:
        # 槽位状态（UI 灯态）：{loaded, playing}
        with self._lock:
            return {
                "loaded": slot in self._samples,
                "playing": self._sample_playing is not None
                and self._sample_playing[0] == slot,
            }

    # --- E1.9 传输辅助 ---

    def tap(self) -> float:
        # Tap BPM：记录时间戳，用最近间隔中值算 BPM（返回 0 表示样本不足）
        import time

        with self._lock:
            now = time.time()
            self._tap_times.append(now)
            if len(self._tap_times) > 8:
                self._tap_times.pop(0)
            if len(self._tap_times) < 2:
                return 0.0
            intervals = sorted(
                self._tap_times[i + 1] - self._tap_times[i]
                for i in range(len(self._tap_times) - 1)
            )
            median = intervals[len(intervals) // 2]
            if median <= 0.0:
                return 0.0
            bpm = 60.0 / median
            if bpm > 0:
                self._bpm = bpm
            return bpm

    def censor(self, active: bool) -> None:
        # Censor：按住期间反向播放（释放恢复正向）
        with self._lock:
            self._reverse = bool(active)

    def stutter(self) -> None:
        # Stutter：回到 CUE 点立即播放（重复触发产生顿挫）
        with self._lock:
            if self._now_audio is None:
                return
            self._position = min(self._cue_sample, len(self._now_audio))
            self._paused = False
            if self.state == State.IDLE:
                self.state = State.PLAYING

    # --- 循环（D2.11） ---

    def set_loop(self, active: bool) -> None:
        # 开关循环：开启时以当前位置为循环起点（长度保持原区间或整段）
        with self._lock:
            if active and not self._loop_active:
                if self._now_audio is not None:
                    self._loop_start = self._position
                    self._loop_end = len(self._now_audio)
            self._loop_active = active

    def set_beatloop(self, beats: int, bpm: float) -> None:
        # 设置拍循环：beats 拍长度，起点对齐到最近拍边界
        with self._lock:
            if self._now_audio is None or bpm <= 0:
                return
            beat_len = int(60.0 / bpm * self.sr)
            self._loop_start = self._position - (self._position % beat_len)
            self._loop_end = min(
                len(self._now_audio), self._loop_start + beats * beat_len
            )
            self._loop_active = True

    def set_loop_range(self, start_seconds: float, end_seconds: float) -> None:
        # 手动设置循环区间（秒）
        with self._lock:
            self._loop_start = int(start_seconds * self.sr)
            self._loop_end = int(end_seconds * self.sr)
            self._loop_active = True

    # --- 混音（D2.5） ---

    def start_mix(
        self,
        next_audio: np.ndarray,
        fade_seconds: float,
        scheduled_start_sample: Optional[int] = None,
    ) -> None:
        # 混入下一段音频：fade 秒交叉淡化；scheduled_start_sample 指定时在到达该
        # 样本的同一音频帧内切换（样本级精确，无静音缝隙，M2 对拍基础）
        with self._lock:
            if self.state != State.PLAYING:
                return
            self._next_audio = next_audio
            self._fade_samples = int(fade_seconds * self.sr)
            self._mix_pos = 0
            if (
                scheduled_start_sample is None
                or scheduled_start_sample <= self._position
            ):
                self._pending_mix_at = None
                self.state = State.MIXING
            else:
                self._pending_mix_at = int(scheduled_start_sample)

    # --- 状态只读 ---

    @property
    def position(self) -> int:
        # 当前播放位置（样本，引擎采样率）
        return self._position

    @property
    def paused(self) -> bool:
        # 暂停标记
        return self._paused

    @property
    def duration(self) -> int:
        # 当前音频总样本数（无音频 0）
        audio = self._now_audio
        return len(audio) if audio is not None else 0

    # --- 回调填充（实时线程，引擎锁内调用） ---

    def fill(self, out: np.ndarray, frames: int) -> None:
        # 按状态填充输出块（PLAYING 或 MIXING；IDLE/暂停输出静音）
        if self._paused or self.state == State.IDLE:
            out[:] = 0
            return
        if self.state == State.PLAYING:
            self._fill_playing(out, frames)
        else:
            self._fill_mixing(out, frames)
        self.eq.process(out)
        # TRIM 预增益（EQ 后、FX 前；回调内零分配）
        if self._pregain != 1.0:
            out *= self._pregain
        # Beat FX 链应用（E2.4 面板驱动）
        self._apply_fx(out)

    def _fill_playing(self, out: np.ndarray, frames: int) -> None:
        # 播放填充：定时切歌分割、循环回绕、弯音/搜索步长、反向(Censor)、
        # Slip 双位置、采样叠加、自然结尾置 IDLE
        if self._now_audio is None:
            out[:] = 0
            return

        # 定时切歌：触发点落在本帧内则先填前段再转 MIXING 处理剩余
        if (
            self._pending_mix_at is not None
            and self._pending_mix_at < self._position + frames
        ):
            trigger = max(self._pending_mix_at, self._position)
            frames_before = trigger - self._position
            if frames_before > 0:
                chunk = self._get_chunk(frames_before)
                out[:frames_before] = chunk
                self._position += frames_before
            self.state = State.MIXING
            self._mix_pos = 0
            self._pending_mix_at = None
            frames_after = frames - frames_before
            if frames_after > 0:
                self._fill_mixing(out[frames_before:], frames_after)
            return

        # Censor：反向播放（按住期间）
        if self._reverse:
            self._position -= frames
            if self._position <= 0:
                self._position = 0
                self._reverse = False
            out[:] = self._get_chunk_reverse(frames)
            return

        # Slip 未搓碟：正常播放（position 与真实位置同步推进，修 P3 实测
        # "Slip 点击后滴滴滴"——原实现 Slip 激活即锁死 position）
        if self._slip_active and not self._jog_touched:
            self._slip_actual = min(self._slip_actual + frames, len(self._now_audio))
            out[:] = self._get_chunk(frames)
            self._mix_sample(out)
            self._position += frames
            return

        # 触摸锁定（P3 修复）：Vinyl 搓碟时位置由平滑刮擦驱动（_scratch_fill
        # 逐帧渐变=变速播放，向前加速/向后倒放，音高随速变化=真实刮擦声）；
        # 手停无增量 → 静音（唱盘停转）；Slip 激活时真实位置继续暗中推进
        if self._jog_touched or self._slip_active:
            if self._slip_active:
                self._slip_actual = min(
                    self._slip_actual + frames, len(self._now_audio)
                )
                self._position = max(0, min(self._position, len(self._now_audio)))
            self._scratch_fill(out, frames)
            self._mix_sample(out)
            return

        # 步长：高速搜索 > 弯音 > 原速
        step = frames
        if self._jog_search_rate != 0.0:
            step = int(round(frames * abs(self._jog_search_rate)))
            if self._jog_search_rate < 0:
                self._position = max(0, self._position - step)
                out[:] = self._get_chunk_reverse(frames)
                return
        elif self._jog_bend_rate != 0.0:
            step = int(round(frames * (1.0 + self._jog_bend_rate)))
            if step != frames:
                # 弯音变速：step 样本线性插值到 frames（防 step<frames 形状
                # 错误致静音卡顿，且块内变速更平滑；分配取舍见文件尾说明）
                src = self._get_chunk(step)
                idx = np.linspace(0.0, step - 1.0, frames)
                i0 = idx.astype(np.int64)
                i1 = np.minimum(i0 + 1, step - 1)
                w = (idx - i0).astype(np.float32)[:, None]
                out[:] = src[i0] * (1.0 - w) + src[i1] * w
            else:
                out[:] = self._get_chunk(frames)
            self._position += step
            # Sampler 叠加（在 EQ 前混入采样）
            self._mix_sample(out)
            if not self._loop_active and self._position >= len(self._now_audio):
                self.state = State.IDLE
            return

        if step != frames:
            chunk = self._get_chunk(step)
            out[:] = chunk[:frames]
        else:
            out[:] = self._get_chunk(frames)
        self._position += step

        # Sampler 叠加（在 EQ 前混入采样）
        self._mix_sample(out)

        if not self._loop_active and self._position >= len(self._now_audio):
            self.state = State.IDLE

    def _scratch_fill(self, out: np.ndarray, frames: int) -> None:
        # 平滑刮擦填充（P3 增强）：把未消费的搓碟位移在块内逐帧均匀渐变
        # （线性插值变速播放——向前=加速、向后=倒放，音高随速变化即真实
        # 刮擦声）；位移钳制曲内；无位移 → 静音（手停）
        audio = self._now_audio
        if audio is None or len(audio) == 0:
            out[:] = 0
            return
        pending = self._scratch_pending
        if pending == 0:
            out[:] = 0
            return
        # 钳制：播放头停在曲内边界（反向 0 / 正向 len-1）；未消费部分丢弃
        # （刮过头 = 手停住，下一块重新等新增量）
        hi = len(audio) - 1
        fpos = self._scratch_fpos
        if pending > 0:
            pending = min(pending, hi - fpos)
        else:
            pending = max(pending, -fpos)
        self._scratch_pending = 0
        if pending == 0:
            out[:] = 0
            return
        # 每帧位置 = fpos + i×(pending/frames)，线性插值取样本
        vel = pending / frames
        idx = fpos + np.arange(frames, dtype=np.float32) * vel
        i0 = idx.astype(np.int64)
        i1 = np.minimum(i0 + 1, hi)
        frac = (idx - i0).astype(np.float32)[:, None]
        out[:] = audio[i0] * (1.0 - frac) + audio[i1] * frac
        self._scratch_fpos = fpos + pending
        self._position = max(0, min(int(round(self._scratch_fpos)), len(audio)))
        self._last_out_pos = self._position

    def _fill_mixing(self, out: np.ndarray, frames: int) -> None:
        # 交叉淡化填充：逐帧线性渐变（可叠加等功率由外层调用方换算）
        now_chunk = self._get_chunk(frames)
        nxt_chunk = self._get_next_chunk(frames)

        t0 = min(self._mix_pos / self._fade_samples, 1.0)
        t1 = min((self._mix_pos + frames) / self._fade_samples, 1.0)
        fade_in = np.linspace(t0, t1, frames, dtype=np.float32).reshape(-1, 1)
        fade_out = 1.0 - fade_in

        out[:] = now_chunk * fade_out + nxt_chunk * fade_in

        self._position += frames
        self._mix_pos += frames

        if self._mix_pos >= self._fade_samples:
            self._now_audio = self._next_audio
            self._position = self._mix_pos
            self._next_audio = None
            self._mix_pos = 0
            self.state = State.PLAYING

    def _get_chunk(self, frames: int) -> np.ndarray:
        # 取当前音频块（循环回绕 + 越界补零）；返回 (frames, 2) float32
        audio = self._now_audio
        if audio is None:
            return np.zeros((frames, CHANNELS), dtype=np.float32)
        if self._loop_active and self._loop_end > self._loop_start:
            loop_len = self._loop_end - self._loop_start
            pos = self._loop_start + ((self._position - self._loop_start) % loop_len)
        else:
            pos = self._position
        chunk = audio[pos : pos + frames]
        if len(chunk) < frames:
            pad = np.zeros((frames - len(chunk), CHANNELS), dtype=np.float32)
            chunk = np.concatenate([chunk, pad], axis=0)
        return chunk

    def _get_next_chunk(self, frames: int) -> np.ndarray:
        # 取来曲缓冲块（越界补零）
        audio = self._next_audio
        if audio is None:
            return np.zeros((frames, CHANNELS), dtype=np.float32)
        chunk = audio[self._mix_pos : self._mix_pos + frames]
        if len(chunk) < frames:
            pad = np.zeros((frames - len(chunk), CHANNELS), dtype=np.float32)
            chunk = np.concatenate([chunk, pad], axis=0)
        return chunk

    def _get_chunk_reverse(self, frames: int) -> np.ndarray:
        # 反向取块（Censor/负向搜索）：从当前位置向前取 frames 样本并倒序
        audio = self._now_audio
        if audio is None:
            return np.zeros((frames, CHANNELS), dtype=np.float32)
        start = max(0, self._position - frames)
        chunk = audio[start : self._position]
        # 不足补零后倒序
        if len(chunk) < frames:
            pad = np.zeros((frames - len(chunk), CHANNELS), dtype=np.float32)
            chunk = np.concatenate([pad, chunk], axis=0)
        return chunk[::-1].copy()

    def _mix_sample(self, out: np.ndarray) -> None:
        # 采样叠加：把正在播放的采样混入输出块（单槽同时播放）
        if self._sample_playing is None:
            return
        slot, pos = self._sample_playing
        audio = self._samples.get(slot)
        if audio is None:
            self._sample_playing = None
            return
        n = len(out)
        chunk = audio[pos : pos + n]
        if len(chunk) < n:
            out[: len(chunk)] += chunk
            self._sample_playing = None
        else:
            out[:] += chunk
            self._sample_playing = (slot, pos + n)

    # --- E2 支撑：TRIM / Beat FX ---

    def set_pregain(self, gain: float) -> None:
        # 设置 TRIM 预增益（0-2，1=unity）
        with self._lock:
            self._pregain = max(0.0, min(2.0, float(gain)))

    def set_fx(self, effect: str, depth: float) -> None:
        # 设置 Beat FX（effect ∈ ""/HPF/LPF/Trans/Echo/Delay；depth 0-1）
        # 系数在 UI 线程算（同 EQ 纪律），回调只执行
        with self._lock:
            self._fx_effect = effect
            self._fx_depth = max(0.0, min(1.0, float(depth)))
            if effect == "HPF" and depth > 0.01:
                # 截止随 depth 对数升高（300Hz → 4000Hz）
                cutoff = 300.0 * (4000.0 / 300.0) ** depth
                self._fx_filter = Biquad(self.sr)
                self._fx_filter.highpass(cutoff)
            elif effect == "LPF" and depth > 0.01:
                cutoff = 10000.0 * (250.0 / 10000.0) ** depth
                self._fx_filter = Biquad(self.sr)
                self._fx_filter.lowpass(cutoff)
            else:
                self._fx_filter = Biquad(self.sr)
            if effect == "Echo":
                self._fx_delay.configure(0.25, 0.3 + 0.4 * depth)
            elif effect == "Delay":
                self._fx_delay.configure(0.375, 0.2 + 0.3 * depth, n_taps=3)

    def _apply_fx(self, out: np.ndarray) -> None:
        # Beat FX 执行（回调内；depth=0 旁通）
        if self._fx_depth <= 0.01 or not self._fx_effect:
            return
        effect = self._fx_effect
        if effect in ("HPF", "LPF"):
            self._fx_filter.process(out)
        elif effect in ("Echo", "Delay"):
            self._fx_delay.process(out, len(out))
        elif effect == "Trans" and self._bpm > 0:
            # 节拍门控：50% 占空比，随 depth 变密（1/4 → 1/32 阶梯）
            div = [0, 4, 8, 16, 32][min(4, int(self._fx_depth * 5))]
            if div > 0:
                beat = self.sr * 60.0 / self._bpm
                period = max(2.0, beat * 4.0 / div)
                n = len(out)
                phase = np.arange(0, n, dtype=np.float64)
                pos = np.mod(phase + self._trans_phase, period)
                gain = np.where(pos < period * 0.5, 1.0, 0.0).astype(np.float32)
                out *= gain[:, None]
                self._trans_phase = int((self._trans_phase + n) % (period * 64))


# ---------------------------------------------------------------------------
# 横推（D2.8，参考 mixxx enginexfader 常量功率曲线）
# ---------------------------------------------------------------------------


class Crossfader:
    # 横推：位置 [-1,1]（-1=全左盘 / +1=全右盘）；常量功率或线性曲线
    def __init__(self, curve: str = "const_power"):
        # 初始化曲线类型（const_power 等功率 / linear 线性）
        self.curve = curve
        self._position = 0.0

    def set_position(self, pos: float) -> None:
        # 设置横推位置（钳制 [-1,1]）
        self._position = float(np.clip(pos, -1.0, 1.0))

    @property
    def position(self) -> float:
        # 当前横推位置
        return self._position

    def get_gains(self) -> tuple:
        # 计算左右盘增益（theta=0→全左，theta=π/2→全右；中点等功率 √2/2）
        theta = (self._position + 1.0) / 2.0 * (np.pi / 2.0)
        if self.curve == "linear":
            return (1.0 - self._position) / 2.0, (1.0 + self._position) / 2.0
        return float(np.cos(theta)), float(np.sin(theta))


# ---------------------------------------------------------------------------
# 主引擎（D2.1/D2.4/D2.9/D2.15）
# ---------------------------------------------------------------------------


class AudioEngine:
    # 主音频引擎：两个打碟机 + 横推混合 + 主音量 + 通道推子 + VU 采集；常驻 OutputStream
    def __init__(self, device=None, master_volume: float = 1.0):
        # 初始化：锁、双 deck、横推、主音量、预分配缓冲；开输出流
        self._lock = threading.Lock()
        self.deck_a = Deck(self._lock)
        self.deck_b = Deck(self._lock)
        self.crossfader = Crossfader()
        self._volume = master_volume
        # 回调内复用的中间缓冲（预分配，实时线程零分配纪律）
        self._buf_a = np.zeros((BLOCK_SIZE, CHANNELS), dtype=np.float32)
        self._buf_b = np.zeros((BLOCK_SIZE, CHANNELS), dtype=np.float32)
        # --- E1.5 VU 电平（方案 C）：每盘峰值环形数组（预分配）+ 写指针 ---
        self._vu_peaks = np.zeros((2, VU_BUFFER), dtype=np.float32)
        self._vu_idx = 0
        # --- E1.9 通道推子与 Fader Start ---
        self._ch_fader = [1.0, 1.0]
        self._fader_start = False
        self._stream = sd.OutputStream(
            device=device,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            callback=self._callback,
            blocksize=BLOCK_SIZE,
        )
        self._stream.start()

    # --- E1.5 VU 电平 ---

    def vu_levels(self) -> list:
        # 当前两盘峰值电平（UI 定时器读取；最近槽位）
        with self._lock:
            idx = (self._vu_idx - 1) % VU_BUFFER
            return [float(self._vu_peaks[0, idx]), float(self._vu_peaks[1, idx])]

    # --- E1.9 通道推子 / Fader Start ---

    def set_channel_fader(self, deck_index: int, value: float) -> None:
        # 设置通道推子（0-1）；Fader Start 开启时联动播放/停止
        # 注意：锁已持有，内部直接操作状态（不可调 stop() 等锁内方法，防重入死锁）
        with self._lock:
            self._ch_fader[deck_index] = max(0.0, min(1.0, float(value)))
            if self._fader_start:
                deck = self.deck_a if deck_index == 0 else self.deck_b
                if self._ch_fader[deck_index] > 0.01:
                    deck._paused = False
                    if deck.state == State.IDLE and deck._now_audio is not None:
                        deck.state = State.PLAYING
                else:
                    # 拉到底停止（锁内联实现，等价 deck.stop() 的清理）
                    deck.state = State.IDLE
                    deck._now_audio = None
                    deck._next_audio = None
                    deck._position = 0
                    deck._paused = False
                    deck._pending_mix_at = None
                    deck._loop_active = False
                    deck.eq.reset()

    def set_fader_start(self, enabled: bool) -> None:
        # 开关 Fader Start 模式（推子从 0 推起=播放、拉到底=停止）
        with self._lock:
            self._fader_start = bool(enabled)

    # --- 主音量（D2.9） ---

    def set_volume(self, v: float) -> None:
        # 设置主增益 [0, MAX_GAIN]（>1 boost；回调内硬限幅 ±1.0 护设备）
        with self._lock:
            self._volume = max(0.0, min(MAX_GAIN, v))

    @property
    def volume(self) -> float:
        # 当前主增益
        return self._volume

    # --- 解码（D2.2） ---

    def load_audio(self, path: str) -> np.ndarray:
        # 解码任意 ffmpeg 支持格式为 (N,2) float32 @44100；按位深动态归一化
        # （16-bit PCM /32768；32-bit float wav 解码为 int32 /2^31，B1 只处理了 16-bit）
        from pydub import AudioSegment

        seg = AudioSegment.from_file(path)
        seg = seg.set_channels(CHANNELS).set_frame_rate(SAMPLE_RATE)
        raw = np.array(seg.get_array_of_samples(), dtype=np.float32)
        if seg.sample_width <= 2:
            norm = 32768.0
        else:
            norm = float(2 ** (8 * seg.sample_width - 1))
        return raw.reshape(-1, CHANNELS) / norm

    # --- 关闭 ---

    def close(self) -> None:
        # 停止并关闭输出流
        try:
            self._stream.stop()
            self._stream.close()
        except Exception:
            pass

    # --- 实时回调（D2.15：零 IO、锁内短、异常 fail-soft 静音） ---

    def _callback(self, outdata: np.ndarray, frames: int, time, status) -> None:
        # 实时线程回调：填双盘 → 各盘 EQ → 通道推子 → 横推混合 → VU 采集 → 主音量限幅
        try:
            with self._lock:
                self.deck_a.fill(self._buf_a, frames)
                self.deck_b.fill(self._buf_b, frames)
                gain_a, gain_b = self.crossfader.get_gains()
                fa, fb = self._ch_fader[0], self._ch_fader[1]
                if gain_a == 1.0 and gain_b == 0.0:
                    outdata[:] = self._buf_a * fa
                elif gain_b == 1.0 and gain_a == 0.0:
                    outdata[:] = self._buf_b * fb
                else:
                    outdata[:] = self._buf_a * gain_a * fa + self._buf_b * gain_b * fb
                # VU 采集（方案 C）：峰值写预分配环形数组（max/min 组合，无新数组）
                self._vu_peaks[0, self._vu_idx % VU_BUFFER] = max(
                    float(self._buf_a.max()), -float(self._buf_a.min())
                )
                self._vu_peaks[1, self._vu_idx % VU_BUFFER] = max(
                    float(self._buf_b.max()), -float(self._buf_b.min())
                )
                self._vu_idx += 1
                if self._volume != 1.0:
                    outdata *= self._volume
                    if self._volume > 1.0:
                        np.clip(outdata, -1.0, 1.0, out=outdata)
        except Exception:
            # fail-soft：任何异常静音输出，绝不抛出到 UI 线程（B1 纪律）
            try:
                outdata[:] = 0
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 双输出监听（D2.14，参考 B1 cue_player.py：独立流/锁/缓冲，完全解耦）
# ---------------------------------------------------------------------------


def _resample(audio: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    # 廉价逐通道线性重采样（仅当监听设备拒绝 44100 时的回退）
    if src_rate == dst_rate or audio.shape[0] == 0:
        return audio
    n_src = audio.shape[0]
    n_dst = int(round(n_src * dst_rate / src_rate))
    if n_dst <= 0:
        return np.zeros((0, audio.shape[1]), dtype=np.float32)
    xp = np.arange(n_src)
    src_idx = np.linspace(0.0, n_src - 1, n_dst)
    out = np.empty((n_dst, audio.shape[1]), dtype=np.float32)
    for ch in range(audio.shape[1]):
        out[:, ch] = np.interp(src_idx, xp, audio[:, ch])
    return out


class CuePlayer:
    # 耳机监听（PFL）：独立第二输出流，与主引擎完全解耦；设备故障静默置 is_dead
    def __init__(self, device, samplerate: int = SAMPLE_RATE, channels: int = CHANNELS):
        # 初始化独立流（PortAudioError 回退设备采样率）；失败置 is_dead
        self._lock = threading.Lock()
        self._audio: Optional[np.ndarray] = None
        self._pos: int = 0
        self._playing: bool = False
        self._dead: bool = False
        self._channels = channels
        self._volume: float = 1.0
        self._play_rate = samplerate
        try:
            self._stream = sd.OutputStream(
                device=device,
                samplerate=samplerate,
                channels=channels,
                dtype="float32",
                callback=self._callback,
                blocksize=BLOCK_SIZE,
            )
            self._stream.start()
        except sd.PortAudioError:
            dev_rate = int(round(sd.query_devices(device)["default_samplerate"]))
            self._play_rate = dev_rate
            self._stream = sd.OutputStream(
                device=device,
                samplerate=dev_rate,
                channels=channels,
                dtype="float32",
                callback=self._callback,
                blocksize=BLOCK_SIZE,
            )
            self._stream.start()

    @property
    def is_playing(self) -> bool:
        # 监听播放中
        return self._playing

    @property
    def is_dead(self) -> bool:
        # 设备故障标记（外部轮询提示）
        return self._dead

    def set_volume(self, v: float) -> None:
        # 监听增益 [0,1]（无 boost，护耳）
        with self._lock:
            self._volume = max(0.0, min(1.0, v))

    @property
    def position_seconds(self) -> float:
        # 监听播放位置（秒）
        return self._pos / self._play_rate

    def play(self, audio: np.ndarray) -> None:
        # 开始监听（按需重采样到设备采样率）
        buf = _resample(audio, SAMPLE_RATE, self._play_rate)
        with self._lock:
            self._audio = buf
            self._pos = 0
            self._playing = True

    def stop(self) -> None:
        # 停止监听
        with self._lock:
            self._playing = False
            self._audio = None
            self._pos = 0

    def seek(self, delta_seconds: float) -> None:
        # 监听位置 ± 秒（钳制 [0, 结尾]）
        with self._lock:
            if not self._playing or self._audio is None:
                return
            self._pos = int(
                min(
                    max(0, self._pos + int(delta_seconds * self._play_rate)),
                    len(self._audio),
                )
            )

    def close(self) -> None:
        # 关闭监听流
        try:
            self._stream.stop()
            self._stream.close()
        except sd.PortAudioError:
            pass

    def _callback(self, outdata: np.ndarray, frames: int, time, status) -> None:
        # 监听回调：fail-soft（设备消失置 is_dead 静音，绝不传染主引擎）
        try:
            with self._lock:
                if self._dead or not self._playing or self._audio is None:
                    outdata[:] = 0
                    return
                chunk = self._audio[self._pos : self._pos + frames]
                if len(chunk) < frames:
                    outdata[: len(chunk)] = chunk
                    outdata[len(chunk) :] = 0
                    self._pos += len(chunk)
                    self._playing = False
                else:
                    outdata[:] = chunk
                    self._pos += frames
                if self._volume != 1.0:
                    outdata *= self._volume
        except Exception:
            self._dead = True
            try:
                outdata[:] = 0
            except Exception:
                pass


# ===== modules/engine.py 模块说明 =====
# 模块级常量：
#   _SC：静态配置单例；SAMPLE_RATE=44100 / CHANNELS=2 / BLOCK_SIZE=2048（base.json）
#   MAX_GAIN=2.0：主增益上限（boost 输出硬限幅 ±1.0）
# 类型：
#   State(Enum)：IDLE/PLAYING/MIXING（B1 状态机）
#   Biquad：RBJ 双二阶（低架/高架/峰形；系数 setter 算、回调只跑差分；zi 持久）
#   DeckEQ：三频 EQ（low/mid/high 旋钮 [-1,1]，0=unity，-1=-30dB 全切）
#   Deck：单打碟机（状态机/CUE/循环/混音/EQ；锁由引擎传入共享）
#   Crossfader：横推（-1..1，常量功率或线性曲线）
#   AudioEngine：主引擎（双 deck + 横推 + 主音量 + 回调 fail-soft）
#   CuePlayer：耳机监听（独立流/锁/缓冲；故障 is_dead 静默）
# 函数（D2 编号）：
#   D2.1 AudioEngine.__init__（常驻流+锁+状态机+预分配缓冲）
#   D2.2 load_audio（pydub 解码 (N,2) float32 /32768）
#   D2.3 Deck.play/pause/stop（状态迁移+EQ reset）
#   D2.4 Deck._fill_playing（取块/补零/自然结尾置 IDLE/循环回绕）
#   D2.5 Deck.start_mix/_fill_mixing（样本级定时切歌 + 逐帧交叉淡化）
#   D2.6 交叉淡化线性渐变（等功率由外层曲线换算，见 Crossfader）
#   D2.7 DeckEQ（RBJ 三频；系数/处理分离；zi 连续性）
#   D2.8 Crossfader（常量功率 cos/sin）
#   D2.9 set_volume（boost 限幅 ±1.0）
#   D2.10 cue_set/cue_play/cue_set_position
#   D2.11 set_loop/set_beatloop/set_loop_range（循环回绕）
#   D2.12 modules/transition.py + modules/stretcher.py（转场规划与预渲染）
#   D2.13 modules/stretcher.py make_keylock_buffer（变调不变速）
#   D2.14 CuePlayer（独立第二输出，PortAudioError 回退重采样）
#   D2.15 _callback（try/except 静音降级，绝不抛出）
# 设计理由：双盘共用一把引擎锁（回调只取一次锁，临界区短）；
#   预分配中间缓冲满足实时线程零分配纪律；EQ 系数计算隔离在 setter 线程；
#   监听流完全解耦保证蓝牙/USB 掉线不卡主播放（B1 纪律）
# 异常处理：回调异常静音降级；解码失败抛异常由上层降级；
#   监听设备故障 is_dead 静默；音量与旋钮全部钳制
# 关联配置：config/static/base.json（sample_rate/block_size/channels）；
#   RUBBERBAND_BIN 环境变量（stretcher.py）；transition.py 复用

# 音频引擎模块：双打碟机 + 三频 EQ + 横推 + 主混音 + 双输出监听（M1 核心）

from __future__ import annotations

import threading
import time
from enum import Enum

import numpy as np
import sounddevice as sd

from config.static.static_config import get_static_config
from modules.stretcher import make_tempo_buffer, rubberband_available
from utils.audio_decode import decode_audio
from utils.logger import get_logger

_logger = get_logger(__name__)

# 静态配置解包（AGENTS.md 参数约定：采样率/块大小/通道数零硬编码）
_SC = get_static_config()
SAMPLE_RATE = int(_SC.base.get("sample_rate", 44100))
CHANNELS = int(_SC.base.get("channels", 2))
BLOCK_SIZE = int(_SC.base.get("block_size", 2048))

# 主增益上限（+6dB boost 能力；输出硬限幅 ±1.0 保护设备，配置驱动 G2.1）
MAX_GAIN = float(_SC.base.get("max_gain", 2.0))

# VU 电平环形缓冲长度（每盘；回调每块写一个峰值，UI 定时器读最近值）
VU_BUFFER = int(_SC.base.get("vu_buffer", 32))

# 三频 EQ 参数（G2.1）：频率 [低/中/高] Hz；增益斜率 [提升 dB, 衰减 dB]
EQ_FREQS = [float(f) for f in _SC.base.get("eq_freqs", [100.0, 1000.0, 10000.0])]
EQ_GAIN_DB = [float(g) for g in _SC.base.get("eq_gain_db", [6.0, -30.0])]

# 槽位上限（Hot Cue / Sampler，每盘；配置驱动 G2.1）
SLOT_COUNT = int(_SC.base.get("slot_count", 8))

# Jog 弯音/搜索钳制（配置驱动 G2.1）
JOG_BEND_MAX = float(_SC.base.get("jog_bend_max", 0.5))
JOG_SEARCH_MAX = float(_SC.base.get("jog_search_max", 16.0))

# 效果预置（Echo/Delay 参数，配置驱动 G2.1）
ECHO_PRESET = dict(_SC.base.get("fx_echo", {"delay": 0.25, "feedback": 0.6, "taps": 1}))
DELAY_PRESET = dict(
    _SC.base.get("fx_delay", {"delay": 0.375, "feedback": 0.4, "taps": 3})
)

# FX 参数群（H2.2：配置驱动 base.json）
KNOB_DEADZONE = float(
    _SC.base.get("knob_deadzone", 0.01)
)  # EQ 死区/FX 最小深度/Fader Start
FX_HPF_RANGE = [float(v) for v in _SC.base.get("fx_hpf_range", [300.0, 4000.0])]
FX_LPF_RANGE = [float(v) for v in _SC.base.get("fx_lpf_range", [10000.0, 250.0])]
FX_ECHO_DEPTH = [float(v) for v in _SC.base.get("fx_echo_depth", [0.3, 0.4])]
FX_DELAY_DEPTH = [float(v) for v in _SC.base.get("fx_delay_depth", [0.2, 0.3])]

# Key Shift 半音上限（H1.3：公开常量，transition_manager 引用，单处读键）
KEY_SHIFT_MAX = int(_SC.base.get("key_shift_max", 12))

# Keylock/Key Shift 重渲染去抖（J1.1：连续推 TEMPO/按 Pad 合并为最后一次渲染）
REBIAS_DEBOUNCE_S = float(_SC.base.get("keylock_debounce_ms", 300)) / 1000.0


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

    def _set_coeffs(self, b: np.ndarray, a: np.ndarray, keep_zi: bool = False) -> None:
        # 更新系数（按 a[0] 归一化；新系数默认 zi 归零防咔嗒；keep_zi=True 时保留
        # 延迟状态——I3.5：HPF/LPF 深度扫动复用 zi 防每次从静止开始的爆点）
        if b is None:
            self._b, self._a = None, None
            return
        a0 = a[0]
        # H0.2：单条元组赋值缩短新旧系数混配窗口（RHS 先整体求值，比两行赋值
        # 混配概率低；GIL 字节码间仍可能切换，彻底原子需指针交换，收益不匹配）
        self._b, self._a = b / a0, a / a0
        if not keep_zi or self._zi is None:
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

    def highpass(self, cutoff: float, q: float = 0.707, keep_zi: bool = False) -> None:
        # 高通滤波（RBJ 直接型；Beat FX HPF 用；keep_zi 语义见 _set_coeffs）
        w0 = 2.0 * np.pi * cutoff / self.sr
        alpha = np.sin(w0) / (2.0 * q)
        cos_w0 = np.cos(w0)
        b = np.array([(1.0 + cos_w0) / 2.0, -(1.0 + cos_w0), (1.0 + cos_w0) / 2.0])
        a = np.array([1.0 + alpha, -2.0 * cos_w0, 1.0 - alpha])
        self._set_coeffs(b, a, keep_zi)

    def lowpass(self, cutoff: float, q: float = 0.707, keep_zi: bool = False) -> None:
        # 低通滤波（RBJ 直接型；Beat FX LPF 用；keep_zi 语义见 _set_coeffs）
        w0 = 2.0 * np.pi * cutoff / self.sr
        alpha = np.sin(w0) / (2.0 * q)
        cos_w0 = np.cos(w0)
        b = np.array([(1.0 - cos_w0) / 2.0, 1.0 - cos_w0, (1.0 - cos_w0) / 2.0])
        a = np.array([1.0 + alpha, -2.0 * cos_w0, 1.0 - alpha])
        self._set_coeffs(b, a, keep_zi)

    def reset(self) -> None:
        # 清除延迟状态（换曲/重开时防滤波振铃串音）
        self._zi = None

    def bypass(self) -> None:
        # 置旁通（系数清 None + 状态清零；I3.5：set_fx 关闭时复用实例不再新建）
        self._b = None
        self._a = None
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
        gain = (
            EQ_GAIN_DB[0] * self.low_amt
            if self.low_amt >= 0
            else EQ_GAIN_DB[1] * abs(self.low_amt)
        )
        if abs(self.low_amt) < KNOB_DEADZONE:
            self.low._set_coeffs(None, None)
        else:
            self.low.low_shelf(gain, EQ_FREQS[0])

    def set_mid(self, amt: float) -> None:
        # 中段旋钮（同 set_low 语义）
        self.mid_amt = float(np.clip(amt, -1.0, 1.0))
        gain = (
            EQ_GAIN_DB[0] * self.mid_amt
            if self.mid_amt >= 0
            else EQ_GAIN_DB[1] * abs(self.mid_amt)
        )
        if abs(self.mid_amt) < KNOB_DEADZONE:
            self.mid._set_coeffs(None, None)
        else:
            self.mid.peaking(gain, EQ_FREQS[1])

    def set_high(self, amt: float) -> None:
        # 高段旋钮（同 set_low 语义）
        self.high_amt = float(np.clip(amt, -1.0, 1.0))
        gain = (
            EQ_GAIN_DB[0] * self.high_amt
            if self.high_amt >= 0
            else EQ_GAIN_DB[1] * abs(self.high_amt)
        )
        if abs(self.high_amt) < KNOB_DEADZONE:
            self.high._set_coeffs(None, None)
        else:
            self.high.high_shelf(gain, EQ_FREQS[2])

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
        # 配置延迟时长/反馈量/多 tap 数（参数变更防咔嗒：旧缓冲保留继续写）；
        # 延迟统一钳缓冲容量内（FIX004/E8：直通路径与 FX 延迟路径同一钳制，
        # 消除配置超 2s 时两路径行为分叉）
        max_delay = self._buf_len - 2 * BLOCK_SIZE
        self._delay = max(1, min(int(delay_seconds * self.sr), max_delay))
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
    # Echo：短延迟（250ms）+ 高反馈（0.6），经典回声（参数配置驱动 G2.1）
    def __init__(self, sr: int):
        # 初始化反馈延迟线并配置 Echo 参数（I2.5：缺键 .get 兜底）
        super().__init__(sr)
        self.configure(
            float(ECHO_PRESET.get("delay", 0.25)),
            float(ECHO_PRESET.get("feedback", 0.6)),
            n_taps=int(ECHO_PRESET.get("taps", 1)),
        )


class Delay(FeedbackDelay):
    # Delay：长延迟（0.375s≈120BPM 八分音符）+ 中反馈（0.4）+ 3 tap
    # （参数配置驱动 G2.1）
    def __init__(self, sr: int):
        # 初始化反馈延迟线并配置 Delay 参数（I2.5：缺键 .get 兜底）
        super().__init__(sr)
        self.configure(
            float(DELAY_PRESET.get("delay", 0.375)),
            float(DELAY_PRESET.get("feedback", 0.4)),
            n_taps=int(DELAY_PRESET.get("taps", 3)),
        )


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
        self._now_audio: np.ndarray | None = None
        self._next_audio: np.ndarray | None = None
        self._position: int = 0
        self._mix_pos: int = 0
        self._fade_samples: int = 0
        self._paused: bool = False
        self._pending_mix_at: int | None = None
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
        # TEMPO 乐速倍率（J1.1 P4：1.0=原速；Keylock 关=实时变速，开=经重渲染不变调）
        self._tempo_rate: float = 1.0
        # Keylock（变速不变调）与重渲染烘焙域：_baked_rate/_baked_semitones 为
        # 当前 _now_audio 已烘焙的拉伸/变调参数（fill 速率因子 = tempo_rate/baked_rate）
        self._keylock_on: bool = False
        self._baked_rate: float = 1.0
        self._baked_semitones: int = 0
        self._orig_audio: np.ndarray | None = None  # 原始缓冲（重渲染基准）
        self._rebias_epoch: int = 0  # 重渲染请求代次（新请求取代旧结果）
        self._rebias_timer: threading.Timer | None = None
        # Key Shift 半音（±12，-12..0..+12；经 rubberband 重渲染真实变调，J1.1）
        self._key_shift: int = 0
        # Jog：触摸态 / 弯音速率（±0.5）/ 高速搜索速率（含符号，±16 倍）
        self._jog_touched: bool = False
        self._jog_bend_rate: float = 0.0
        self._jog_search_rate: float = 0.0
        self._scratch_pending: int = 0  # 未消费的搓碟位移（平滑刮擦队列）
        self._scratch_fpos: float = 0.0  # 搓碟浮点播放位置（逐帧渐变）
        # Slip 模式：真实位置暗中推进，播放位置（_position）可被搓碟自由移动
        self._slip_active: bool = False
        self._slip_actual: int = 0
        # Sampler：8 槽音频 + 当前播放 (slot, pos)
        self._samples: dict[int, np.ndarray] = {}
        self._sample_playing: tuple[int, int] | None = None
        # Tap BPM：时间戳队列（秒）
        self._tap_times: list[float] = []
        # Censor：按住期间反向播放
        self._reverse: bool = False
        # Mix 完成标记（FIX004.1：_fill_mixing 淡出换缓冲时置位，UI 轮询消费——
        # 触发 _deck_meta 滚动与 AUTO 链式装填；消费方负责清零）
        self._mix_finished: bool = False
        # Trans 门控相位（跨块持续）
        self._trans_phase: int = 0
        # Beat FX 拍数（J1.1：Echo/Delay 延迟 = beats/4 拍、Trans 门控周期，BPM 驱动）
        self._fx_beats: int = 4

    # --- 传输控制 ---

    def play(self, audio: np.ndarray) -> None:
        # 从头播放整段音频（清状态/CUE 保持/循环关闭/EQ 状态清零；
        # 重置烘焙域与乐速/调移——新曲从原始缓冲开始，J1.1+FIX004.1/E6）
        with self._lock:
            self._now_audio = audio
            self._orig_audio = audio
            self._position = 0
            self._paused = False
            self.state = State.PLAYING
            self._pending_mix_at = None
            self._next_audio = None
            self._loop_active = False
            self._tempo_rate = 1.0
            self._baked_rate = 1.0
            self._baked_semitones = 0
            self._key_shift = 0  # E6：换曲调移清零（Pad 灯与新曲音频一致）
            self._scratch_fpos = 0.0
            self._scratch_pending = 0
            self._mix_finished = False
            self.eq.reset()

    def pause(self) -> None:
        # 暂停/恢复切换
        with self._lock:
            self._paused = not self._paused

    def stop(self) -> None:
        # 停止：清空音频与状态（CUE 保留，EQ 状态清零）；清原始缓冲并取消
        # 在途重渲染（FIX004/E3）与完成标记（FIX005.12：防 100ms stale 消费
        # 在 IDLE 盘上误滚 meta/误报 AUTO 提示）
        with self._lock:
            self._reset_playback_locked()

    def _reset_playback_locked(self) -> None:
        # 播放域清理（须持锁；FIX005/②-12：stop 与 fader 停止两处共用——
        # 原两处内联 8 行已两轮同步改，抽单点防继续漂移）
        self.state = State.IDLE
        self._now_audio = None
        self._next_audio = None
        self._orig_audio = None
        self._position = 0
        self._paused = False
        self._pending_mix_at = None
        self._loop_active = False
        self._mix_finished = False
        self._cancel_rebias()
        self.eq.reset()

    def _cancel_rebias(self) -> None:
        # 取消在途重渲染去抖定时器（须持锁；FIX004/E3）
        if self._rebias_timer is not None:
            self._rebias_timer.cancel()
            self._rebias_timer = None

    def take_mix_finished(self) -> bool:
        # mix 完成标记读取即清（FIX005.17：公开接口替代 UI 直访私有字段；
        # 原子读清——UI 100ms 轮询消费）
        with self._lock:
            flag = self._mix_finished
            self._mix_finished = False
            return flag

    # --- CUE（D2.10） ---

    def cue_set(self) -> None:
        # 在当前播放位置设置 CUE 点
        with self._lock:
            self._cue_sample = self._position

    def cue_set_position(self, seconds: float) -> None:
        # 按秒设置 CUE 点（供 UI 先做 downbeat 吸附再设置）
        with self._lock:
            self._cue_sample = max(0, int(seconds * self.sr))

    def set_position_samples(self, samples: int) -> None:
        # 公开 seek（H0.4）：持锁设置播放位置并钳制曲内（Instant Doubles 等用，
        # 取代外部直写 _position 私有字段）
        with self._lock:
            if self._now_audio is None:
                return
            self._position = max(0, min(int(samples), len(self._now_audio)))

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
            if 0 <= slot < SLOT_COUNT:
                self._hot_cues[slot] = self._position

    def hot_cue_play(self, slot: int) -> None:
        # 跳转到热 CUE 槽并播放（无音频/槽空忽略）
        with self._lock:
            if (
                0 <= slot < SLOT_COUNT
                and slot in self._hot_cues
                and self._now_audio is not None
            ):
                self._position = min(self._hot_cues[slot], len(self._now_audio))
                self._paused = False
                if self.state == State.IDLE:
                    self.state = State.PLAYING
                self._pending_mix_at = None

    def hot_cue_clear(self, slot: int) -> None:
        # 清除热 CUE 槽（越界忽略）
        with self._lock:
            if 0 <= slot < SLOT_COUNT:
                self._hot_cues.pop(slot, None)

    def hot_cue_state(self, slot: int) -> dict:
        # 热 CUE 槽状态（UI 灯态用）：{has, seconds}
        with self._lock:
            sample = self._hot_cues.get(slot)
            return {"has": sample is not None, "seconds": (sample or 0) / self.sr}

    # --- E1.2 Beatgrid 跳转 ---

    def set_tempo(self, bpm: float) -> None:
        # 设置当前曲 BPM（Beat Jump/Tap 计算用；UI 加载曲目时调用；
        # BPM 变化联动 Beat FX 延迟重配，J1.1）
        with self._lock:
            self._bpm = max(0.0, float(bpm))
            self._apply_fx_delay_locked()

    @property
    def bpm(self) -> float:
        # 当前曲 BPM 公开只读（I1.1：UI 统一走此 property，替代直读 _bpm 私有字段）
        with self._lock:
            return self._bpm

    @property
    def tempo_rate(self) -> float:
        # 当前乐速倍率（Beat Sync 计算/显示用，J1.0）
        with self._lock:
            return self._tempo_rate

    @property
    def effective_bpm(self) -> float:
        # 有效 BPM = 曲目 BPM × 乐速倍率（Beat Sync 目标值，J1.0）
        with self._lock:
            return self._bpm * self._tempo_rate

    def set_tempo_rate(self, rate: float) -> None:
        # 设置乐速倍率（TEMPO 推子，P4/J1.1）：Keylock 关 = 实时变速（弯音同路线，
        # 音高随速变化）；Keylock 开 = 触发 rubberband 重渲染烘焙（不变调），
        # 去抖合并连续变化
        with self._lock:
            self._tempo_rate = max(0.1, min(2.0, float(rate)))
            target = (self._tempo_rate if self._keylock_on else 1.0, self._key_shift)
        self._maybe_rebias(target)

    def set_keylock(self, on: bool) -> None:
        # Keylock 开关（J1.1）：开 = 乐速变化走重渲染（变速不变调）；
        # 关 = 回实时变速路线（已烘焙的拉伸卸载回原速域）
        with self._lock:
            self._keylock_on = bool(on)
            target = (self._tempo_rate if self._keylock_on else 1.0, self._key_shift)
        self._maybe_rebias(target)

    # --- J1.1 重渲染（Keylock/Key Shift 烘焙） ---

    def _maybe_rebias(self, target: tuple[float, int]) -> None:
        # 目标烘焙态与当前一致则跳过；否则去抖调度后台重渲染
        # （rubberband 渲染 ~1-2s，连续推 TEMPO/连打 Pad 合并为最后一次）
        if target == (self._baked_rate, self._baked_semitones):
            return
        if not rubberband_available():
            _logger.warning("rubberband 不可用：Keylock/Key Shift 保持实时变速路线")
            return
        timer = self._rebias_timer
        if timer is not None:
            timer.cancel()
        self._rebias_timer = threading.Timer(REBIAS_DEBOUNCE_S, self._apply_rebias)
        self._rebias_timer.daemon = True
        self._rebias_timer.start()

    def _apply_rebias(self) -> None:
        # 后台重渲染（worker 线程，允许 IO）：从原始缓冲渲染目标 (rate, 半音) →
        # epoch 校验 + MIXING 让路（短暂重试）→ 锁内换缓冲并重映射位置域
        with self._lock:
            if self._orig_audio is None:
                return
            target_rate = self._tempo_rate if self._keylock_on else 1.0
            target_shift = self._key_shift
            if (target_rate, target_shift) == (self._baked_rate, self._baked_semitones):
                return
            self._rebias_epoch += 1
            my_epoch = self._rebias_epoch
        try:
            buf = make_tempo_buffer(
                self._orig_audio,
                target_rate,
                semitones=float(target_shift),
                sample_rate=self.sr,
            )
        except Exception:
            # fail-soft：渲染失败保持当前缓冲（可能仍处于旧烘焙态），绝不崩溃
            _logger.warning("Keylock/Key Shift 重渲染失败（保持当前缓冲）", exc_info=True)
            return
        deadline = time.monotonic() + 10.0
        while True:
            with self._lock:
                if self._rebias_epoch != my_epoch:
                    return  # 已被新请求取代
                if self.state != State.MIXING:
                    break
            # MIXING 中换缓冲会破坏 _mix_pos 域映射——短暂等待淡出结束（上限 10s）
            if time.monotonic() > deadline:
                _logger.warning("重渲染换缓冲超时（MIXING 未结束），放弃本次应用")
                return
            time.sleep(0.1)
        with self._lock:
            if self._rebias_epoch != my_epoch:
                return
            # FIX005.11：终装二次守卫（E3 换入口防护——渲染 1-2s 窗内 stop()
            # 已清 orig/置 IDLE 时不得把缓冲装回已停盘，否则 cue_play/stutter
            # 可让"已停止"的盘出声）
            if self._orig_audio is None or self.state == State.IDLE:
                return
            if (target_rate, self._key_shift) != (target_rate, target_shift):
                return  # 渲染期间参数又变
            self._swap_buffer(buf, target_rate, target_shift)

    def _swap_buffer(self, new_audio: np.ndarray, rate: float, semitones: int) -> None:
        # 锁内换烘焙缓冲并重映射全部位置域（cue/hot cue/loop/slip/搓碟按拉伸比换算；
        # Key Shift 不改时长 factor=1 无损）
        factor = rate / self._baked_rate if self._baked_rate > 0 else 1.0
        self._now_audio = new_audio
        self._baked_rate = rate
        self._baked_semitones = semitones
        if factor != 1.0:
            self._position = int(self._position * factor)
            self._cue_sample = int(self._cue_sample * factor)
            self._hot_cues = {k: int(v * factor) for k, v in self._hot_cues.items()}
            self._loop_start = int(self._loop_start * factor)
            self._loop_end = int(self._loop_end * factor)
            self._slip_actual = int(self._slip_actual * factor)
            self._scratch_fpos *= factor
            self._scratch_pending = int(self._scratch_pending * factor)
            # FIX004.10：挂起定时切歌点同步换算（旧域样本 → 新烘焙域；
            # 越新曲尾则钳尾——触发丢失好过错位跳读）
            if self._pending_mix_at is not None:
                self._pending_mix_at = min(
                    len(new_audio), max(0, int(self._pending_mix_at * factor))
                )
        self._position = max(0, min(self._position, len(new_audio)))

    def _beat_len(self, bpm: float) -> int:
        # 拍长换算（样本数）：60/bpm×sr×烘焙拉伸比（G1.3 共用；J1.1 乘 _baked_rate
        # 使 beat_jump/set_beatloop 在 Keylock 烘焙域内仍按乐理拍长计算）
        return int(60.0 / bpm * self.sr * self._baked_rate)

    def beat_jump(self, beats: int, align: bool = False) -> None:
        # 按拍跳转：±beats 拍；align=True（Skip 模式）时先对齐最近拍边界
        with self._lock:
            if self._now_audio is None or self._bpm <= 0:
                return
            beat_len = self._beat_len(self._bpm)
            target = self._position + beats * beat_len
            if align:
                target = target - (target % beat_len)
            self._position = max(0, min(target, len(self._now_audio)))

    # --- E1.3 Key Shift 半音 ---

    def set_key_shift(self, semitones: int) -> None:
        # 设置 Key Shift（钳制 ±key_shift_max；J1.1 真实变调：经 rubberband 重渲染
        # 烘焙 --pitch，时长不变故位置域无需换算，去抖合并连打）
        with self._lock:
            self._key_shift = max(-KEY_SHIFT_MAX, min(KEY_SHIFT_MAX, int(semitones)))
            target = (self._tempo_rate if self._keylock_on else 1.0, self._key_shift)
        self._maybe_rebias(target)

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
        # 弯音：临时播放速率偏移（±JOG_BEND_MAX；0=恢复原速）
        with self._lock:
            self._jog_bend_rate = max(-JOG_BEND_MAX, min(JOG_BEND_MAX, float(rate)))

    def jog_search(self, rate: float) -> None:
        # SHIFT 高速搜索：速率倍数（±JOG_SEARCH_MAX；0=停止）
        with self._lock:
            self._jog_search_rate = max(
                -JOG_SEARCH_MAX, min(JOG_SEARCH_MAX, float(rate))
            )

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

    @property
    def loop_active(self) -> bool:
        # 循环激活状态（UI 提示用，J1.0）
        with self._lock:
            return self._loop_active

    @property
    def pending_mix(self) -> bool:
        # 定时切歌挂起中（FIX005/T3：tm.mix_now 重入拒绝的公开判据——
        # 原"MIXING 拒绝"注释无实现，pending 窗口二次 mix 会覆盖缓冲）
        with self._lock:
            return self._pending_mix_at is not None

    # --- E1.7 Sampler 槽位 ---

    def sample_load(self, slot: int, audio: np.ndarray) -> None:
        # 载入采样到槽位（0-7；停止当前播放并替换）
        with self._lock:
            if 0 <= slot < SLOT_COUNT and audio is not None and len(audio) > 0:
                self._samples[slot] = audio
                if self._sample_playing is not None and self._sample_playing[0] == slot:
                    self._sample_playing = None

    def sample_play(self, slot: int) -> None:
        # 播放槽位采样（若已在播则从头重播；只同时播一个）
        with self._lock:
            if 0 <= slot < SLOT_COUNT and slot in self._samples:
                self._sample_playing = (slot, 0)

    def sample_stop(self, slot: int) -> None:
        # 停止槽位采样播放
        with self._lock:
            if self._sample_playing is not None and self._sample_playing[0] == slot:
                self._sample_playing = None

    def sample_unload(self, slot: int) -> None:
        # 卸载槽位采样（同时停止播放）
        with self._lock:
            if 0 <= slot < SLOT_COUNT:
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
                self._apply_fx_delay_locked()  # FIX004/E7：Tap 定速后 FX 延迟随新 BPM 重配
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
            beat_len = self._beat_len(bpm)
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

    def loop_in(self) -> None:
        # 循环入点（J1.0 FLX4 LOOP IN）：当前位置为起点，暂不激活（等 OUT 闭合）
        with self._lock:
            if self._now_audio is not None:
                self._loop_start = self._position
                self._loop_end = len(self._now_audio)
                self._loop_active = False

    def loop_out(self) -> None:
        # 循环出点（J1.0 FLX4 LOOP OUT）：当前位置为终点并激活循环（需先 IN）
        with self._lock:
            if self._now_audio is not None and self._loop_start < self._position:
                self._loop_end = self._position
                self._loop_active = True

    def loop_halve(self) -> None:
        # 循环长度减半（J1.0 CALL ◀ 语义：减半）
        with self._lock:
            length = self._loop_end - self._loop_start
            if length >= 2:
                self._loop_end = self._loop_start + length // 2

    def loop_double(self) -> None:
        # 循环长度加倍（J1.0 CALL ▶ 语义：加倍，钳制曲尾）
        with self._lock:
            if self._now_audio is not None:
                length = self._loop_end - self._loop_start
                self._loop_end = min(
                    len(self._now_audio), self._loop_start + length * 2
                )

    def cue_buffer(self) -> np.ndarray | None:
        # 耳机预听缓冲（J1.0：当前位置到曲尾的切片视图；切片共享底层内存，
        # 后续烘焙换缓冲也不影响已取出的视图）
        with self._lock:
            if self._now_audio is None:
                return None
            return self._now_audio[self._position :]

    # --- 混音（D2.5） ---

    def start_mix(
        self,
        next_audio: np.ndarray,
        fade_seconds: float,
        scheduled_start_sample: int | None = None,
    ) -> None:
        # 混入下一段音频：fade 秒交叉淡化；scheduled_start_sample 指定时在到达该
        # 样本的同一音频帧内切换（样本级精确，无静音缝隙，M2 对拍基础）
        with self._lock:
            if self.state != State.PLAYING:
                return
            self._next_audio = next_audio
            # G0.3：fade_seconds<=0 时钳制为 1 样本（防 _fill_mixing 除零静音）
            self._fade_samples = max(1, int(fade_seconds * self.sr))
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

        # 乐速因子（J1.1）：烘焙域 → 乐速的换算比（Keylock 烘焙后 fill 恒 1.0；
        # 实时变速 >1 加速 <1 减速，音高随速变化 = 黑胶语义）
        factor = self._tempo_rate / self._baked_rate if self._baked_rate > 0 else 1.0

        # Censor：反向播放（按住期间）；到曲头保持反向停留（I0.3）；反向速度随乐速
        if self._reverse:
            self._position -= max(1, int(frames * factor))
            if self._position <= 0:
                self._position = 0
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

        # 步长：高速搜索 > 弯音×乐速 > 乐速 > 原速
        if self._jog_search_rate != 0.0:
            # I0.2：step 钳制 ≥1（|rate|<0.000244 时原 step==0 → _fill_resample
            # 空数组负索引 IndexError 静音卡死）；搜索为绝对速率（不乘乐速）
            step = max(1, int(round(frames * abs(self._jog_search_rate))))
            if self._jog_search_rate < 0:
                self._position = max(0, self._position - step)
                out[:] = self._get_chunk_reverse(frames)
                return
            # G0.2：正向搜索 step<frames（|rate|<1）时复用插值防形状错误
            self._fill_resample(out, frames, step)
            self._position += step
            self._mix_sample(out)
            if not self._loop_active and self._position >= len(self._now_audio):
                self.state = State.IDLE
            return
        elif self._jog_bend_rate != 0.0:
            # I0.2：step 钳制 ≥1；弯音乘乐速因子（J1.1，烘焙域内合成）
            step = max(1, int(round(frames * factor * (1.0 + self._jog_bend_rate))))
            self._fill_resample(out, frames, step)
            self._position += step
            # Sampler 叠加（在 EQ 前混入采样）
            self._mix_sample(out)
            if not self._loop_active and self._position >= len(self._now_audio):
                self.state = State.IDLE
            return
        elif factor != 1.0:
            # J1.1 P4：TEMPO 实时变速（插值填充，音高随速变化）
            step = max(1, int(round(frames * factor)))
            self._fill_resample(out, frames, step)
            self._position += step
            self._mix_sample(out)
            if not self._loop_active and self._position >= len(self._now_audio):
                self.state = State.IDLE
            return

        out[:] = self._get_chunk(frames)
        self._position += frames

        # Sampler 叠加（在 EQ 前混入采样）
        self._mix_sample(out)

        if not self._loop_active and self._position >= len(self._now_audio):
            self.state = State.IDLE

    def _fill_resample(self, out: np.ndarray, frames: int, step: int) -> None:
        # 变速填充（弯音/搜索共用，G0.2）：step 样本线性插值到 frames——
        # 防 step<frames 形状错误致静音卡顿（减速），且块内变速更平滑；
        # step==frames 直通无开销
        if step == frames:
            out[:] = self._get_chunk(frames)
            return
        src = self._get_chunk(step)
        idx = np.linspace(0.0, step - 1.0, frames)
        i0 = idx.astype(np.int64)
        i1 = np.minimum(i0 + 1, step - 1)
        w = (idx - i0).astype(np.float32)[:, None]
        out[:] = src[i0] * (1.0 - w) + src[i1] * w

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

    def _mix_source_chunk(self, audio: np.ndarray | None, pos: int, frames: int, factor: float) -> np.ndarray:
        # 混音源取块（FIX004.8）：factor==1 直通补零；≠1 时 step 插值到 frames
        # （出曲按实时变速因子继续）；FIX005.9：loop 激活按回绕位置取块并跨
        # loop_end 续读（原 _get_chunk 有回绕、插值路径丢失——loop 中转场出曲
        # 穿 loop 直冲曲尾静音的回归修复）
        if audio is None:
            return np.zeros((frames, CHANNELS), dtype=np.float32)
        need = frames if factor == 1.0 else max(1, int(round(frames * factor)))
        if self._loop_active and self._loop_end > self._loop_start and pos >= self._loop_start:
            loop_len = self._loop_end - self._loop_start
            pos = self._loop_start + ((pos - self._loop_start) % loop_len)
            chunk = audio[pos : pos + need]
            if len(chunk) < need:  # 跨 loop_end：回绕到 loop_start 续读
                wrap = audio[self._loop_start : self._loop_start + (need - len(chunk))]
                chunk = np.concatenate([chunk, wrap], axis=0)
        else:
            chunk = audio[pos : pos + need]
            if len(chunk) < need:
                pad = np.zeros((need - len(chunk), CHANNELS), dtype=np.float32)
                chunk = np.concatenate([chunk, pad], axis=0)
        if factor == 1.0:
            return chunk
        idx = np.linspace(0.0, need - 1.0, frames)
        i0 = idx.astype(np.int64)
        i1 = np.minimum(i0 + 1, need - 1)
        w = (idx - i0).astype(np.float32)[:, None]
        return chunk[i0] * (1.0 - w) + chunk[i1] * w

    def _fill_mixing(self, out: np.ndarray, frames: int) -> None:
        # 交叉淡化填充：逐帧线性渐变（等功率曲线作用于主输出 Crossfader）；
        # 出曲按乐速因子插值（FIX004.8：Keylock 关+TEMPO≠1 时混音期速度连续、
        # 弯音可用）；完成换缓冲按 play() 同款重置演奏/烘焙域（FIX004.1——
        # 旧曲循环/烘焙/刮擦域不得套在来曲上，_orig_audio 置 None 使后续
        # rebias 安全跳过）并置 _mix_finished 供 UI 消费（meta 滚动/AUTO 链）
        factor = self._tempo_rate / self._baked_rate if self._baked_rate > 0 else 1.0
        now_chunk = self._mix_source_chunk(self._now_audio, self._position, frames, factor)
        nxt_chunk = self._mix_source_chunk(self._next_audio, self._mix_pos, frames, 1.0)

        t0 = min(self._mix_pos / self._fade_samples, 1.0)
        t1 = min((self._mix_pos + frames) / self._fade_samples, 1.0)
        fade_in = np.linspace(t0, t1, frames, dtype=np.float32).reshape(-1, 1)
        fade_out = 1.0 - fade_in

        out[:] = now_chunk * fade_out + nxt_chunk * fade_in

        self._position += max(1, int(round(frames * factor)))
        self._mix_pos += frames

        if self._mix_pos >= self._fade_samples:
            self._now_audio = self._next_audio
            self._position = self._mix_pos
            self._next_audio = None
            self._mix_pos = 0
            self.state = State.PLAYING
            # FIX004.1：来曲成为 now——旧曲演奏/烘焙域全部失效；
            # FIX005.8 域语义裁决：**延续舞池速度**（_tempo_rate/_keylock_on
            # 不重置——mix 后 TEMPO 推子位置不变、音乐速度连续，DJ 惯例）；
            # 移调/Slip/Censor 不延续（换曲归零，与 play() 一致）
            self._baked_rate = 1.0
            self._baked_semitones = 0
            self._orig_audio = None
            self._loop_active = False
            self._loop_start = 0
            self._loop_end = 0
            self._pending_mix_at = None
            self._scratch_pending = 0
            self._scratch_fpos = float(self._position)
            self._key_shift = 0
            self._slip_active = False
            self._slip_actual = 0
            self._reverse = False
            self._mix_finished = True

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

    # FIX005/E 组：_get_next_chunk 删除（FIX004.8 后零调用——来曲块由
    # _mix_source_chunk 统一承担）

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
            if effect == "HPF" and depth > KNOB_DEADZONE:
                # 截止随 depth 对数升高（H2.2：范围配置驱动）
                # I3.5：复用实例换系数 + 保留 zi（原重建 Biquad 丢状态，
                # 深度扫动/反复开关产生咔嗒）
                lo, hi = FX_HPF_RANGE
                cutoff = lo * (hi / lo) ** depth
                self._fx_filter.highpass(cutoff, keep_zi=True)
            elif effect == "LPF" and depth > KNOB_DEADZONE:
                lo, hi = FX_LPF_RANGE
                cutoff = lo * (hi / lo) ** depth
                self._fx_filter.lowpass(cutoff, keep_zi=True)
            else:
                self._fx_filter.bypass()
            if effect == "Echo":
                base, slope = FX_ECHO_DEPTH
                self._fx_delay.configure(
                    float(ECHO_PRESET.get("delay", 0.25)), base + slope * depth
                )
                self._apply_fx_delay_locked()
            elif effect == "Delay":
                base, slope = FX_DELAY_DEPTH
                self._fx_delay.configure(
                    float(DELAY_PRESET.get("delay", 0.375)),
                    base + slope * depth,
                    n_taps=int(DELAY_PRESET.get("taps", 3)),
                )
                self._apply_fx_delay_locked()

    def set_fx_beats(self, beats: int) -> None:
        # Beat FX 拍数（J1.1）：Echo/Delay 延迟 = beats/4 拍（BPM 驱动）、
        # Trans 门控周期同步；BPM 未知时保持预置延迟
        with self._lock:
            self._fx_beats = max(1, min(32, int(beats)))
            self._apply_fx_delay_locked()

    def _apply_fx_delay_locked(self) -> None:
        # 锁内：按 BPM×拍数重配 Echo/Delay 延迟（须已持锁；BPM 未知/效果未开跳过）
        if self._fx_effect not in ("Echo", "Delay") or self._bpm <= 0:
            return
        delay = 60.0 / self._bpm * self._fx_beats / 4.0
        if self._fx_effect == "Echo":
            base, slope = FX_ECHO_DEPTH
            preset = ECHO_PRESET
        else:
            base, slope = FX_DELAY_DEPTH
            preset = DELAY_PRESET
        self._fx_delay.configure(
            min(delay, 1.9),  # 钳缓冲上限内（configure 亦钳，双保险）
            base + slope * self._fx_depth,
            n_taps=int(preset.get("taps", 1)),
        )

    def _apply_fx(self, out: np.ndarray) -> None:
        # Beat FX 执行（回调内；depth=0 旁通）
        if self._fx_depth <= KNOB_DEADZONE or not self._fx_effect:
            return
        effect = self._fx_effect
        if effect in ("HPF", "LPF"):
            self._fx_filter.process(out)
        elif effect in ("Echo", "Delay"):
            self._fx_delay.process(out, len(out))
        elif effect == "Trans" and self._bpm > 0:
            # 节拍门控：50% 占空比；周期 = beats/4 拍（J1.1 拍数接线；
            # BPM 未知时 Trans 不生效——无时基则门控无意义）
            beat = self.sr * 60.0 / self._bpm
            period = max(2.0, beat * self._fx_beats / 4.0)
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

    def get_gains(self) -> tuple[float, float]:
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
        # --- J1.0 耳机监听（CuePlayer 惰性创建：默认输出设备，失败降级 None） ---
        self._cue_player: CuePlayer | None = None
        self._cue_failed = False
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

    def vu_levels(self) -> list[float]:
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
                if self._ch_fader[deck_index] > KNOB_DEADZONE:
                    deck._paused = False
                    if deck.state == State.IDLE and deck._now_audio is not None:
                        deck.state = State.PLAYING
                else:
                    # 拉到底停止（FIX005/②-12：共用 _reset_playback_locked）
                    deck._reset_playback_locked()

    def set_fader_start(self, enabled: bool) -> None:
        # 开关 Fader Start 模式（推子从 0 推起=播放、拉到底=停止）
        with self._lock:
            self._fader_start = bool(enabled)

    def ensure_cue_player(self) -> "CuePlayer | None":
        # 耳机监听惰性创建（J1.0）：首次调用时开独立输出流（默认设备）；
        # 创建失败置 _cue_failed 不再重试，返回 None 由 UI 提示
        if self._cue_player is None and not self._cue_failed:
            try:
                self._cue_player = CuePlayer(device=None)
            except Exception:
                self._cue_failed = True
                _logger.warning("耳机监听流创建失败（监听功能不可用）", exc_info=True)
        return self._cue_player

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
        # 解码任意 ffmpeg 支持格式为 (N,2) float32 @44100
        # （G1.1 复用 utils 统一解码；H3.1：decode_audio 顶层导入）
        return decode_audio(path, CHANNELS, SAMPLE_RATE)

    # --- 关闭 ---

    def close(self) -> None:
        # 停止并关闭输出流（FIX005/E10：连带关闭监听流——原仅主流，
        # 第二输出流靠进程退出回收）
        try:
            self._stream.stop()
            self._stream.close()
        except Exception:
            pass
        if self._cue_player is not None:
            try:
                self._cue_player.close()
            except Exception:
                pass
            self._cue_player = None

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
        self._audio: np.ndarray | None = None
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
# 模块级常量（G3.3 同步：全部配置驱动 base.json）：
#   _SC：静态配置单例；SAMPLE_RATE=44100 / CHANNELS=2 / BLOCK_SIZE=2048
#   MAX_GAIN=2.0（max_gain）：主增益上限（boost 输出硬限幅 ±1.0）
#   VU_BUFFER=32（vu_buffer）：VU 峰值环形缓冲长度
#   EQ_FREQS=[100,1k,10k] / EQ_GAIN_DB=[6,-30]（eq_freqs/eq_gain_db）：三频 EQ 参数
#   SLOT_COUNT=8（slot_count）：Hot Cue/Sampler 槽位上限
#   JOG_BEND_MAX=0.5 / JOG_SEARCH_MAX=16（jog_bend_max/jog_search_max）：钳制
#   ECHO_PRESET / DELAY_PRESET（fx_echo/fx_delay）：效果预置
#   KEY_SHIFT_MAX=12（key_shift_max）：Key Shift 钳制（transition_manager 共用）
# 类型：
#   State(Enum)：IDLE/PLAYING/MIXING（B1 状态机）
#   Biquad：RBJ 双二阶（低架/高架/峰形；系数 setter 算、回调只跑差分；zi 持久）
#   DeckEQ：三频 EQ（low/mid/high 旋钮 [-1,1]，0=unity，-1=-30dB 全切）
#   FeedbackDelay/Echo/Delay：反馈延迟线（环形缓冲 + 多 tap；Echo 短延迟高反馈、
#     Delay 长延迟多 tap；P1 修复后恒从块头读取，零初始化提供初始静默）
#   Deck：单打碟机（状态机/CUE/循环/混音/EQ；锁由引擎传入共享）
#   Crossfader：横推（-1..1，常量功率或线性曲线）
#   AudioEngine：主引擎（双 deck + 横推 + 主音量 + 回调 fail-soft）
#   CuePlayer：耳机监听（独立流/锁/缓冲；故障 is_dead 静默）
# 函数（D2 编号）：
#   D2.1 AudioEngine.__init__（常驻流+锁+状态机+预分配缓冲）
#   D2.2 load_audio（G1.1 复用 utils/audio_decode.py 统一解码）
#   D2.3 Deck.play/pause/stop（状态迁移+EQ reset）
#   D2.4 Deck._fill_playing（取块/补零/自然结尾置 IDLE/循环回绕；
#     弯音/搜索经 _fill_resample 变速插值，触摸锁定经 _scratch_fill 平滑刮擦）
#   D2.5 Deck.start_mix/_fill_mixing（样本级定时切歌 + 逐帧交叉淡化；
#     fade 钳制 ≥1 防除零）
#   D2.6 交叉淡化线性渐变（等功率曲线在主输出 Crossfader，不在转场内部）
#   D2.7 DeckEQ（RBJ 三频；系数/处理分离；zi 连续性）
#   D2.8 Crossfader（常量功率 cos/sin）
#   D2.9 set_volume（boost 限幅 ±1.0）
#   D2.10 cue_set/cue_play/cue_set_position
#   D2.11 set_loop/set_beatloop/set_loop_range（循环回绕；拍长 _beat_len 共用）
#   D2.12 modules/transition.py + modules/stretcher.py（转场规划与预渲染）
#   D2.13 modules/stretcher.py make_keylock_buffer（变调不变速）
#   D2.14 CuePlayer（独立第二输出，PortAudioError 回退重采样）
#   D2.15 _callback（try/except 静音降级，绝不抛出）
#   E1.x jog_touch/jog_scratch/jog_bend/jog_search（触摸锁定 + 平滑刮擦
#     _scratch_fill：块内逐帧插值变速播放，手停静音）
# 设计理由：双盘共用一把引擎锁（回调只取一次锁，临界区短）；
#   静态外观一次渲染（控件侧）；回调内插值/补零存在小规模 numpy 分配
#   （linspace/索引数组/补零缓冲，块预算 46ms 内开销 <0.1ms，与弯音/刮擦
#   仅激活时发生，属可接受的取舍——完整零分配需预分配波形表，留待优化）；
#   EQ 系数计算隔离在 setter 线程；监听流完全解耦保证蓝牙/USB 掉线不卡主播放
# 异常处理：回调异常静音降级；解码失败抛异常由上层降级；
#   监听设备故障 is_dead 静默；音量与旋钮全部钳制
# 关联配置：config/static/base.json（sample_rate/block_size/channels/max_gain/
#   vu_buffer/eq_*/slot_count/jog_*/fx_*/key_shift_max）；
#   RUBBERBAND_BIN 环境变量（stretcher.py）；transition.py 复用

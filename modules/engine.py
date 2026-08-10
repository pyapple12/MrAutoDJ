# 音频引擎模块：双打碟机 + 三频 EQ + 横推 + 主混音 + 双输出监听（M1 核心）
# 参考：reference/dj-engine/songs-automixer_python（audio_engine.py 状态机与混音、
#   cue_player.py 双输出、fx.py 系数/处理分离纪律）；mixxx enginexfader 常量功率曲线

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

    def _fill_playing(self, out: np.ndarray, frames: int) -> None:
        # 播放填充：处理定时切歌分割、循环回绕、自然结尾置 IDLE
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

        chunk = self._get_chunk(frames)
        out[:] = chunk
        self._position += frames
        if not self._loop_active and self._position >= len(self._now_audio):
            self.state = State.IDLE

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
    # 主音频引擎：两个打碟机 + 横推混合 + 主音量；常驻 OutputStream 实时回调
    def __init__(self, device=None, master_volume: float = 1.0):
        # 初始化：锁、双 deck、横推、主音量、预分配混合缓冲；开输出流
        self._lock = threading.Lock()
        self.deck_a = Deck(self._lock)
        self.deck_b = Deck(self._lock)
        self.crossfader = Crossfader()
        self._volume = master_volume
        # 回调内复用的中间缓冲（预分配，实时线程零分配纪律）
        self._buf_a = np.zeros((BLOCK_SIZE, CHANNELS), dtype=np.float32)
        self._buf_b = np.zeros((BLOCK_SIZE, CHANNELS), dtype=np.float32)
        self._stream = sd.OutputStream(
            device=device,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            callback=self._callback,
            blocksize=BLOCK_SIZE,
        )
        self._stream.start()

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
        # 实时线程回调：填双盘 → 各盘 EQ → 横推混合 → 主音量 → 硬限幅
        try:
            with self._lock:
                self.deck_a.fill(self._buf_a, frames)
                self.deck_b.fill(self._buf_b, frames)
                gain_a, gain_b = self.crossfader.get_gains()
                if gain_a == 1.0 and gain_b == 0.0:
                    outdata[:] = self._buf_a
                elif gain_b == 1.0 and gain_a == 0.0:
                    outdata[:] = self._buf_b
                else:
                    outdata[:] = self._buf_a * gain_a + self._buf_b * gain_b
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

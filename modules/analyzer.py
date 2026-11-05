# 曲目分析模块：BPM/调性/能量/CUE 检测 + SQLite 缓存 + 进程池批处理 + CLI
# 约定：分析用 22050Hz mono；bpm=0/key="?" 表示"未记录"（empty_record 降级）

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import sqlite3
import sys
import tempfile
from concurrent import futures
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from config.static.static_config import get_static_config
from utils.audio_decode import decode_audio
from utils.file_utils import get_project_root

# 静态配置解包（采样率/跳帧/缓存路径/BPM 区间，AGENTS.md 参数约定：零硬编码）
_SC = get_static_config()
ANALYSIS_SAMPLE_RATE = int(_SC.base.get("analysis_sample_rate", 22050))
ANALYSIS_HOP = int(_SC.base.get("analysis_hop", 512))

# BPM 合理区间（DJ 折半/加倍折叠用，G2.1：配置驱动）
MIN_BPM = float(_SC.base.get("min_bpm", 70.0))
MAX_BPM = float(_SC.base.get("max_bpm", 180.0))

SUPPORTED_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".wav",
    ".ogg",
    ".m4a",
    ".aac",
    ".opus",
    ".wma",
    ".aiff",
    ".aif",
    ".mp4",
    ".webm",
}

# BPM 合理区间（DJ 用）：估计值折半/加倍进此区间（cuekey tempo.py 约定，
# G2.1 配置驱动：值见顶部 MIN_BPM/MAX_BPM）

# 能量评分权重（H2.1：配置驱动，base.json energy_weights）
ENERGY_WEIGHTS = [
    float(w) for w in _SC.base.get("energy_weights", [0.4, 0.25, 0.2, 0.15])
]

# CUE 检测参数（H2.1：配置驱动，base.json cue_params）
CUE_PARAMS = dict(
    _SC.base.get("cue_params", {"max_cues": 8, "min_spacing": 8.0, "n_mfcc": 13})
)

# 缓存算法版本：检测算法变更时 +1，旧缓存自动失效重算（PL002.4：+timbre 字段 → 2）
ANALYSIS_VERSION = 2

# Krumhansl-Kessler 调性谱（key.py 约定，24 键相关打分用）
_KK_MAJOR = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
)
_KK_MINOR = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
)
_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


# ---------------------------------------------------------------------------
# Camelot 轮盘（D1.7，参考 cuekey/camelot.py）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Key:
    # 调性领域对象：音级 0=C..11=B + 大小调；输出三种记谱
    pitch_class: int
    mode: str  # "major" | "minor"

    def __post_init__(self) -> None:
        # 构造校验：音级与调式越界直接报错（frozen dataclass 防误改）
        if not 0 <= self.pitch_class <= 11:
            raise ValueError(f"pitch_class out of range: {self.pitch_class}")
        if self.mode not in ("major", "minor"):
            raise ValueError(f"unknown mode: {self.mode}")

    @property
    def standard(self) -> str:
        # 标准记谱：C/Am/F#m 等
        suffix = "m" if self.mode == "minor" else ""
        return _NOTE_NAMES[self.pitch_class] + suffix

    @property
    def wheel_number(self) -> int:
        # 调和轮盘位置 1-12（小调用关系大调换算，五度圈公式）
        if self.mode == "major":
            tonic = self.pitch_class
        else:
            tonic = (self.pitch_class + 3) % 12  # 关系大调
        return (tonic * 7 + 7) % 12 + 1

    @property
    def camelot(self) -> str:
        # Camelot 记谱：8A（小调）/8B（大调），DJ 调和混音通用
        letter = "B" if self.mode == "major" else "A"
        return f"{self.wheel_number}{letter}"

    def notation(self, style: str) -> str:
        # 统一记谱入口：standard / camelot
        if style == "camelot":
            return self.camelot
        return self.standard


def parse_key(text: str) -> Key:
    # 从标准记谱解析 Key（"Am"/"C"/"F#m"），非法抛 ValueError
    text = text.strip()
    if not text:
        raise ValueError("empty key string")
    mode = "minor" if text.endswith("m") else "major"
    name = text[:-1] if text.endswith("m") else text
    try:
        pitch = _NOTE_NAMES.index(name)
    except ValueError:
        raise ValueError(f"unknown key name: {text!r}") from None
    return Key(pitch, mode)


# ---------------------------------------------------------------------------
# BPM 检测（D1.3，参考 cuekey/analysis/tempo.py）
# ---------------------------------------------------------------------------


def _fold_bpm(bpm: float) -> float:
    # 折半/加倍折进 [70,180] DJ 合理区间（含边界；bpm<=0 原样返回）
    if bpm <= 0:
        return bpm
    while bpm < MIN_BPM:
        bpm *= 2
    while bpm > MAX_BPM:
        bpm /= 2
    return bpm


def _snap_bpm(bpm: float, tolerance: float = 0.2) -> float:
    # 吸附到整数/半整数（DAW 曲目拍速精确；超出容差保留原值如黑胶转录）
    nearest_int = round(bpm)
    if abs(bpm - nearest_int) <= tolerance:
        return float(nearest_int)
    nearest_half = round(bpm * 2) / 2
    if abs(bpm - nearest_half) <= tolerance / 2:
        return nearest_half
    return bpm


def _refine_bpm(bpm: float, beat_times: np.ndarray) -> float:
    # 用拍子间隔中值重估 BPM：剔除偏离中值 20% 的漏拍/错拍间隔后取均值
    if beat_times.size < 16:
        return bpm
    intervals = np.diff(beat_times)
    median = float(np.median(intervals))
    if median <= 0:
        return bpm
    regular = intervals[np.abs(intervals - median) < 0.2 * median]
    if regular.size < 8:
        return bpm
    return 60.0 / float(regular.mean())


def _local_maxima(x: np.ndarray) -> np.ndarray:
    # 纯 numpy 局部极大值布尔掩码（供拍点与 onset 密度用）
    mask = np.zeros(len(x), dtype=bool)
    if len(x) >= 3:
        mask[1:-1] = (x[1:-1] > x[:-2]) & (x[1:-1] >= x[2:])
    return mask


def _tempo_prior(bpm: float) -> float:
    # Ellis 2007 对数正态拍速先验（中心 125BPM，鼓励俱乐部拍速，防半速误判）
    return float(np.exp(-0.5 * (np.log2(bpm / 125.0) / 1.0) ** 2))


def _estimate_bpm(onset_env: np.ndarray, sr: int) -> float:
    # 基础 BPM：onset 自相关，在 70-180 候选网格按 8 拍倍数打分 × 拍速先验
    import librosa

    ac = librosa.autocorrelate(onset_env)
    if ac.size == 0 or ac[0] <= 0:
        return 120.0
    ac = ac / ac[0]
    best_bpm, best_score = 120.0, -np.inf
    for candidate in np.arange(MIN_BPM, MAX_BPM + 0.5, 0.5):
        lag = 60.0 * sr / (ANALYSIS_HOP * candidate)
        total, used = 0.0, 0
        for k in range(1, 9):
            index = k * lag
            i0 = int(index)
            if i0 + 1 >= ac.size:
                break
            frac = index - i0
            total += (1 - frac) * ac[i0] + frac * ac[i0 + 1]
            used += 1
        if used:
            score = (total / used) * _tempo_prior(float(candidate))
            if score > best_score:
                best_bpm, best_score = float(candidate), score
    return best_bpm


def _pick_metrical_level(bpm: float, onset_env: np.ndarray, sr: int) -> float:
    # 修正节拍级误锁（3:2/倍频/4:3）：候选因子打分，仅当显著更优才切换（防抖）
    import librosa

    if bpm <= 0:
        return bpm
    ac = librosa.autocorrelate(onset_env)
    if ac.size == 0 or ac[0] <= 0:
        return bpm
    ac = ac / ac[0]

    def score(candidate: float) -> float:
        # 候选拍速在 onset 自相关前 8 个拍周期倍数处的加权吻合度
        lag = 60.0 * sr / (ANALYSIS_HOP * candidate)
        total, used = 0.0, 0
        for k in range(1, 9):
            index = k * lag
            i0 = int(index)
            if i0 + 1 >= ac.size:
                break
            frac = index - i0
            total += (1 - frac) * ac[i0] + frac * ac[i0 + 1]
            used += 1
        return (total / used) * _tempo_prior(candidate) if used else 0.0

    base_score = score(bpm)
    best_bpm, best_score = bpm, base_score
    for factor in (1.5, 2 / 3, 2.0, 0.5, 4 / 3, 0.75):
        candidate = _fold_bpm(bpm * factor)
        candidate_score = score(candidate)
        if candidate_score > best_score:
            best_bpm, best_score = candidate, candidate_score
    if best_bpm != bpm and best_score > 1.05 * base_score:
        return best_bpm
    return bpm


def _track_beats(
    onset_env: np.ndarray, sr: int, bpm: float, tightness: float = 100.0
) -> np.ndarray:
    # 纯 numpy Ellis 动态规划拍子追踪（避开 numba 内核，冻结/多进程环境安全）
    n = len(onset_env)
    if n == 0 or bpm <= 0:
        return np.array([], dtype=int)
    period = max(1, round(60.0 * sr / (ANALYSIS_HOP * bpm)))

    # 以拍长为高斯核平滑归一化 onset 包络
    std = onset_env.std(ddof=1)
    normalized = onset_env / std if std > 0 else onset_env
    window = np.exp(-0.5 * ((np.arange(-period, period + 1) * 32.0 / period) ** 2))
    localscore = np.convolve(normalized, window, mode="same")

    # DP：每帧回链约一个拍周期前的最佳前驱
    backlink = np.full(n, -1, dtype=int)
    cumscore = np.zeros(n)
    offsets = np.arange(-2 * period, -(period // 2) + 1)
    txcost = -tightness * np.log(-offsets / period) ** 2
    for i in range(n):
        window_idx = i + offsets
        valid = window_idx >= 0
        if not valid.any():
            cumscore[i] = localscore[i]
            continue
        scores = txcost[valid] + cumscore[window_idx[valid]]
        best = int(np.argmax(scores))
        cumscore[i] = localscore[i] + scores[best]
        backlink[i] = int(window_idx[valid][best])

    # 末拍取累计分的显著局部极大，沿回链回溯全部拍点
    maxima = _local_maxima(cumscore)
    if not maxima.any():
        return np.array([], dtype=int)
    threshold = (
        0.5 * np.median(cumscore[maxima][cumscore[maxima] > 0])
        if (cumscore[maxima] > 0).any()
        else 0.0
    )
    strong = np.flatnonzero(maxima & (cumscore >= threshold))
    if strong.size == 0:
        return np.array([], dtype=int)
    beats = [int(strong[-1])]
    while backlink[beats[-1]] >= 0:
        beats.append(int(backlink[beats[-1]]))
    return np.array(beats[::-1], dtype=int)


def _detect_tempo(y: np.ndarray, sr: int) -> dict:
    # BPM 检测总入口：onset 强度 → 估计 → 级修正 → DP 追踪 → 精修/吸附
    import librosa

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=ANALYSIS_HOP)
    bpm = _pick_metrical_level(_estimate_bpm(onset_env, sr), onset_env, sr)
    beat_frames = _track_beats(onset_env, sr, bpm)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=ANALYSIS_HOP)
    bpm = _snap_bpm(_fold_bpm(_refine_bpm(bpm, beat_times)))
    return {"bpm": round(float(bpm), 2), "beat_times": beat_times}


def _pick_downbeat_phase(beat_frames: np.ndarray, y: np.ndarray, sr: int) -> int:
    # downbeat 相位选择：4 拍相位中选低频（40-150Hz）STFT 能量总和最大者（假设 4/4）
    import librosa

    if len(beat_frames) < 4:
        return 0
    stft_mag = np.abs(librosa.stft(y, n_fft=2048, hop_length=ANALYSIS_HOP))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    low_band = (freqs >= 40.0) & (freqs <= 150.0)
    if not np.any(low_band):
        return 0
    low_energy = stft_mag[low_band, :].sum(axis=0)

    window_frames = max(1, int(round(0.075 * sr / ANALYSIS_HOP)))
    beat_energies = np.zeros(len(beat_frames), dtype=np.float64)
    for i, bf in enumerate(beat_frames):
        lo = max(0, int(bf) - window_frames)
        hi = min(len(low_energy), int(bf) + window_frames + 1)
        if hi > lo:
            beat_energies[i] = float(low_energy[lo:hi].mean())

    best_phase, best_score = 0, -1.0
    for phase in range(4):
        score = float(beat_energies[phase::4].sum())
        if score > best_score:
            best_phase, best_score = phase, score
    return best_phase


# ---------------------------------------------------------------------------
# 调性检测（D1.6，参考 cuekey/analysis/key.py）
# ---------------------------------------------------------------------------


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    # 皮尔逊相关系数（调性相关打分用）
    a = a - a.mean()
    b = b - b.mean()
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _detect_key(y: np.ndarray, sr: int) -> dict:
    # 调性检测：谐波分离 → chroma_cqt → 时间中位数 → 24 键 KK 相关
    import librosa

    y_harmonic = librosa.effects.harmonic(y)
    chroma = librosa.feature.chroma_cqt(y=y_harmonic, sr=sr, tuning=0.0)
    chroma_mean = np.median(chroma, axis=1)

    best_score, best_key, best_mode = -np.inf, "C", "major"
    runner_up = -np.inf
    for pitch in range(12):
        rotated = np.roll(chroma_mean, -pitch)
        s_maj = _pearson(rotated, _KK_MAJOR)
        s_min = _pearson(rotated, _KK_MINOR)
        if s_maj > best_score:
            runner_up = best_score
            best_score, best_key, best_mode = s_maj, _NOTE_NAMES[pitch], "major"
        else:
            runner_up = max(runner_up, s_maj)
        if s_min > best_score:
            runner_up = best_score
            best_score, best_key, best_mode = s_min, _NOTE_NAMES[pitch], "minor"
        else:
            runner_up = max(runner_up, s_min)
    confidence = float(np.clip((best_score - runner_up) / 0.2, 0.0, 1.0))
    return {
        "key": f"{best_key} {best_mode}",
        "key_pitch": best_key,
        "key_mode": best_mode,
        "key_confidence": round(confidence, 3),
    }


# ---------------------------------------------------------------------------
# 能量 1-10（D1.8，参考 cuekey/analysis/energy.py）
# ---------------------------------------------------------------------------


def _detect_energy(y: np.ndarray, sr: int, bpm: float) -> int:
    # 能量 1-10：响度 40% + onset 密度 25% + 低频占比 20% + 拍速 15%
    import librosa

    # 响度：90% 分位 RMS 映射（-28dB 温和 ~ -8dB 猛烈）
    rms = librosa.feature.rms(y=y)[0]
    loud = float(np.percentile(rms, 90))
    db = 20 * np.log10(max(loud, 1e-6))
    loud_score = float(np.clip((db + 28.0) / 20.0, 0.0, 1.0))

    # onset 密度：强峰数 / 秒（阈值=均值+标准差）
    envelope = librosa.onset.onset_strength(y=y, sr=sr)
    if envelope.size == 0:
        onset_score = 0.0
    else:
        threshold = envelope.mean() + envelope.std()
        duration = len(y) / sr
        peaks = int(np.count_nonzero(_local_maxima(envelope) & (envelope >= threshold)))
        onset_score = (
            float(np.clip((peaks / duration) / 4.0, 0.0, 1.0)) if duration > 0 else 0.0
        )

    # 低频占比（≤160Hz 能量比）
    spectrum = np.abs(np.fft.rfft(y)) ** 2
    freqs = np.fft.rfftfreq(len(y), d=1.0 / sr)
    total = float(spectrum.sum())
    bass_ratio = float(spectrum[freqs <= 160.0].sum()) / total if total > 0 else 0.0
    bass_score = float(np.clip(bass_ratio / 0.5, 0.0, 1.0))

    # 拍速分
    tempo_score = float(np.clip((bpm - 70.0) / 80.0, 0.0, 1.0))

    score = (
        ENERGY_WEIGHTS[0] * loud_score
        + ENERGY_WEIGHTS[1] * onset_score
        + ENERGY_WEIGHTS[2] * bass_score
        + ENERGY_WEIGHTS[3] * tempo_score
    )
    return int(np.clip(round(1 + 9 * score), 1, 10))


# ---------------------------------------------------------------------------
# 音色概要（PL002.4）：谱质心/带宽/滚降三维归一，供 automix 音色兼容分
# ---------------------------------------------------------------------------


def _detect_timbre(y: np.ndarray, sr: int) -> list[float]:
    # 音色概要三维 0-1 向量：谱质心/谱带宽/谱滚降(85%) 的全程均值，
    # 各按固定参考范围 min-max 归一（质心 [200,6000]Hz / 带宽 [200,4000]Hz /
    # 滚降 [1000,10000]Hz）——范围固定保证跨曲可比
    import librosa

    def _norm(series: np.ndarray, lo: float, hi: float) -> float:
        mean = float(np.mean(series)) if len(series) else 0.0
        return float(np.clip((mean - lo) / (hi - lo), 0.0, 1.0))

    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)[0]
    return [
        _norm(centroid, 200.0, 6000.0),
        _norm(bandwidth, 200.0, 4000.0),
        _norm(rolloff, 1000.0, 10000.0),
    ]


# ---------------------------------------------------------------------------
# 自动 CUE 点（D1.9，参考 cuekey/analysis/cues.py）
# ---------------------------------------------------------------------------


def _detect_cues(
    y: np.ndarray, sr: int, bpm: float, beat_times: np.ndarray
) -> list[dict]:
    # 自动 CUE：MFCC+chroma 聚合聚类分段 → 边界吸附最近拍点 → 8s 去重 → 最多 8 个
    import librosa

    # I2.5：缺键 .get() 兜底（cue_params 配置裁剪/半配置时不 KeyError 崩溃）
    max_cues = int(CUE_PARAMS.get("max_cues", 8))
    min_spacing = float(CUE_PARAMS.get("min_spacing", 8.0))
    n_mfcc = int(CUE_PARAMS.get("n_mfcc", 13))
    duration = len(y) / sr
    if duration < 8.0:
        return []

    # H0.1：hop 与配置常量统一（原局部 512 与 ANALYSIS_HOP 脱钩，配置变更 CUE 不跟随）
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc, hop_length=ANALYSIS_HOP)
    chroma = librosa.feature.chroma_stft(
        y=y, sr=sr, hop_length=ANALYSIS_HOP, tuning=0.0
    )
    features = np.vstack([mfcc, chroma])
    features = librosa.util.normalize(features, axis=1)

    n_frames = features.shape[1]
    n_segments = min(max_cues + 2, max(2, n_frames // 4))
    boundary_frames = librosa.segment.agglomerative(features, n_segments)
    # I0.1：hop_length 引用配置常量（原 hop 引用已删局部变量，CLI 批量分析 NameError）
    boundary_times = librosa.frames_to_time(
        boundary_frames, sr=sr, hop_length=ANALYSIS_HOP
    )

    # 边界吸附到最近拍点；忽略尾部 5s；8s 最小间距去重
    snapped = []
    for t in boundary_times:
        if t >= duration - 5.0:
            continue
        if beat_times.size == 0:
            snapped.append(float(t))
        else:
            index = int(np.argmin(np.abs(beat_times - t)))
            snapped.append(float(beat_times[index]))
    kept = []
    for t in sorted(snapped):
        if not kept or t - kept[-1] >= min_spacing:
            kept.append(t)
    return [{"seconds": round(t, 3)} for t in kept[:max_cues]]


# ---------------------------------------------------------------------------
# 记录结构与失败降级（D1.12）
# ---------------------------------------------------------------------------


def empty_record() -> dict:
    # 默认分析记录（bpm=0/key="?"/beats 空/timbre None）：分析失败或未缓存时的降级占位
    return {
        "bpm": 0.0,
        "key": "?",
        "beats": [],
        "downbeats": [],
        "energy": 0,
        "timbre": None,
        "cues": [],
    }


# ---------------------------------------------------------------------------
# 单曲分析组装（D1.2）
# ---------------------------------------------------------------------------


def _decode_mono(path: str, sr: int) -> np.ndarray:
    # 解码音频为 sr Hz mono float32 一维（G1.1 复用 utils 统一解码；
    # H3.1：decode_audio 顶层导入；失败抛异常由上层降级）
    return decode_audio(path, 1, sr)[:, 0]


def analyze_file(path: str, with_cues: bool = True) -> dict:
    # 分析单曲：解码 → tempo → key → energy → cues → 聚合记录（异常上抛由批处理降级）
    y = _decode_mono(path, ANALYSIS_SAMPLE_RATE)
    tempo = _detect_tempo(y, ANALYSIS_SAMPLE_RATE)
    key = _detect_key(y, ANALYSIS_SAMPLE_RATE)
    energy = _detect_energy(y, ANALYSIS_SAMPLE_RATE, tempo["bpm"])
    beat_times = tempo["beat_times"]
    # beats/downbeats 转引擎采样率样本索引（B1 约定：可直接对 engine.position 使用；
    # 采样率读 base.json，G0.1 修复——原硬编码 44100 与配置脱钩）
    engine_sr = int(_SC.base.get("sample_rate", 44100))
    beats = (beat_times * engine_sr).round().astype(int).tolist()
    # downbeat：低频能量相位选择（每 4 拍取强拍相位），至少 16 拍才判定
    if len(beats) >= 16:
        beat_frames = (beat_times / ANALYSIS_HOP).round().astype(int)
        phase = _pick_downbeat_phase(beat_frames, y, ANALYSIS_SAMPLE_RATE)
        downbeats = beats[phase::4]
    else:
        downbeats = beats[::4] if len(beats) >= 4 else []
    cues = (
        _detect_cues(y, ANALYSIS_SAMPLE_RATE, tempo["bpm"], beat_times)
        if with_cues
        else []
    )
    return {
        "bpm": tempo["bpm"],
        "key": key["key"],
        "beats": beats,
        "downbeats": downbeats,
        "energy": energy,
        "timbre": _detect_timbre(y, ANALYSIS_SAMPLE_RATE),
        "cues": cues,
    }


# ---------------------------------------------------------------------------
# 扫描（D1.1，参考 songs-automixer_python/automix/analyzer.py）
# ---------------------------------------------------------------------------


def scan_folder(root: str) -> list[str]:
    # 递归收集支持格式的音频文件（按路径排序；目录不存在返回空）
    root_path = Path(root)
    if not root_path.is_dir():
        return []
    found = []
    for dirpath, _, filenames in os.walk(root_path):
        for fname in sorted(filenames):
            if Path(fname).suffix.lower() in SUPPORTED_EXTENSIONS:
                found.append(str(Path(dirpath) / fname))
    return found


# ---------------------------------------------------------------------------
# SQLite 缓存（D1.10，参考 cuekey/cache.py）
# ---------------------------------------------------------------------------


def _cache_dir() -> Path:
    # 缓存目录：base.json cache_path（项目内 cache/，已 gitignore；
    # H3.1：get_project_root 顶层导入）
    cache_path = str(_SC.base.get("cache_path", "cache/analysis.sqlite"))
    return get_project_root() / Path(cache_path)


class AnalysisCache:
    # SQLite 分析缓存：key=绝对路径，size/mtime/算法版本三重校验，坏记录返回 None

    def __init__(self, db_path: Path | None = None):
        # 打开（必要时创建）缓存库并建表；连接失败降级为无缓存
        self._conn: sqlite3.Connection | None = None
        self._dead = False
        self._db_path = db_path or _cache_dir()
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self._db_path), timeout=5)
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS analysis (
                    path TEXT PRIMARY KEY,
                    size INTEGER NOT NULL,
                    mtime_ns INTEGER NOT NULL,
                    version INTEGER NOT NULL,
                    has_cues INTEGER NOT NULL,
                    payload TEXT NOT NULL
                )"""
            )
            self._conn.commit()
        except sqlite3.Error:
            self._dead = True  # 缓存不可用（只读目录等）：降级为无缓存，不阻断分析

    def get(self, path: str, require_cues: bool = True) -> dict | None:
        # 读缓存：文件变化/版本不符/解析失败一律返回 None（重分析）
        if self._dead or self._conn is None:
            return None
        try:
            stat = os.stat(path)
        except OSError:
            return None
        try:
            row = self._conn.execute(
                "SELECT size, mtime_ns, version, has_cues, payload FROM analysis WHERE path = ?",
                (path,),
            ).fetchone()
        except sqlite3.Error:
            return None
        if row is None:
            return None
        size, mtime_ns, version, has_cues, payload = row
        if (
            size != stat.st_size
            or mtime_ns != stat.st_mtime_ns
            or version != ANALYSIS_VERSION
        ):
            return None
        if require_cues and not has_cues:
            return None
        try:
            return json.loads(payload)
        except (ValueError, TypeError):
            return None

    def put(self, path: str, record: dict, has_cues: bool = True) -> None:
        # 写缓存（INSERT OR REPLACE）；失败静默（缓存是优化不是正确性依赖）
        if self._dead or self._conn is None:
            return
        try:
            stat = os.stat(path)
        except OSError:
            return
        try:
            self._conn.execute(
                "INSERT OR REPLACE INTO analysis (path, size, mtime_ns, version, has_cues, payload)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    path,
                    stat.st_size,
                    stat.st_mtime_ns,
                    ANALYSIS_VERSION,
                    int(has_cues),
                    json.dumps(record, ensure_ascii=False),
                ),
            )
            self._conn.commit()
        except sqlite3.Error:
            pass

    def close(self) -> None:
        # 关闭连接（进程池 worker 用后关闭）
        if self._conn is not None:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass


# ---------------------------------------------------------------------------
# 批处理（D1.11，参考 cuekey/analyzer.py：缓存先行 + 进程池 + 失败不中断）
# ---------------------------------------------------------------------------

# 回调类型：on_result(path, record|None, error|None)
OnResult = Callable[[str, dict | None, Exception | None], None]


def _default_workers() -> int:
    # 默认 worker 数：核数-2（留 UI/系统），至少 1
    return max(1, (os.cpu_count() or 2) - 2)


def _warm_worker() -> None:
    # worker 初始化：隔离 numba JIT 缓存（多进程并发写共享缓存会损坏导致段错误；
    # I3.3：tempfile 顶层导入，函数内 import 全清）
    os.environ["NUMBA_CACHE_DIR"] = tempfile.mkdtemp(prefix="mrautodj-numba-")


def _analyze_task(path: str, with_cues: bool) -> dict:
    # 进程池任务：单曲分析（返回记录；异常上抛由批处理回调 error）
    return analyze_file(path, with_cues=with_cues)


def analyze_many(
    paths: list[str],
    on_result: OnResult,
    with_cues: bool = True,
    max_workers: int | None = None,
    use_cache: bool = True,
    should_stop: Callable[[], bool] | None = None,
) -> int:
    # 批量分析：缓存命中先回（即时）→ 剩余串行/进程池分析 → 主进程统一写回缓存；
    # 单文件失败回调 error 不中断整批；返回成功数。should_stop 轮询可暂停/取消
    cache = AnalysisCache() if use_cache else None
    succeeded = 0
    misses = []
    for path in paths:
        if should_stop is not None and should_stop():
            if cache is not None:
                cache.close()
            return succeeded
        cached = cache.get(path, require_cues=with_cues) if cache is not None else None
        if cached is not None:
            succeeded += 1
            on_result(path, cached, None)
        else:
            misses.append(path)

    if not misses:
        if cache is not None:
            cache.close()
        return succeeded

    workers = max_workers if max_workers is not None else _default_workers()
    workers = min(workers, len(misses))

    def _record_success(path: str, record: dict) -> None:
        # 统一成功处理：写回缓存 + 计数 + 回调（主进程执行，SQLite 无并发写问题）
        nonlocal succeeded
        if cache is not None:
            cache.put(path, record, has_cues=with_cues)
        succeeded += 1
        on_result(path, record, None)

    if workers <= 1:
        # 单 worker 退化：直接串行（避免进程池开销）
        for path in misses:
            if should_stop is not None and should_stop():
                break
            try:
                record = analyze_file(path, with_cues=with_cues)
                _record_success(path, record)
            except Exception as error:
                on_result(path, None, error)
        if cache is not None:
            cache.close()
        return succeeded

    # 多 worker：spawn 进程池（Windows 必需）；分析结果由主进程写回缓存
    context = multiprocessing.get_context("spawn")
    pool = futures.ProcessPoolExecutor(
        max_workers=workers,
        mp_context=context,
        initializer=_warm_worker,
        max_tasks_per_child=16,  # 定期回收 worker 防内存爬升
    )
    pending = {pool.submit(_analyze_task, p, with_cues): p for p in misses}
    for future in futures.as_completed(pending):
        if should_stop is not None and should_stop():
            for f in pending:
                f.cancel()
            break
        path = pending[future]
        try:
            record = future.result()
            _record_success(path, record)
        except Exception as error:
            on_result(path, None, error)
    pool.shutdown(wait=False, cancel_futures=True)
    if cache is not None:
        cache.close()
    return succeeded


# ---------------------------------------------------------------------------
# CLI（D1.13）
# ---------------------------------------------------------------------------


def main() -> None:
    # CLI 入口：--folder 扫描分析（进度条 + JSON 汇总）；--no-cues 跳过 CUE 检测
    parser = argparse.ArgumentParser(
        prog="modules.analyzer", description="MrAutoDJ 曲目分析"
    )
    parser.add_argument("--folder", required=True, help="音乐文件夹路径")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--no-cues", action="store_true", help="跳过 CUE 检测")
    args = parser.parse_args()

    files = scan_folder(args.folder)
    if not files:
        print(f"未找到音频文件: {args.folder}")
        sys.exit(1)

    total = len(files)
    print(f"找到 {total} 个音频文件，开始分析（缓存命中即时返回）...")
    results = {}

    def _progress(path: str, record: dict | None, error: Exception | None) -> None:
        # 逐条进度：成功记录结果，失败打印警告（不中断）
        done = len(results)
        pct = int(done / total * 30) if total > 0 else 0
        bar = "#" * pct + "-" * (30 - pct)
        results[path] = record or empty_record()
        if error is not None:
            print(f"\r  [{bar}]  {done + 1}/{total}  FAIL {Path(path).name}: {error}")
        else:
            print(f"\r  [{bar}]  {done + 1}/{total}  {Path(path).name}")

    analyze_many(files, _progress, with_cues=not args.no_cues)
    print(f"\n分析完成：{len(results)}/{total}")

    if args.json:
        summary = {}
        for path, rec in results.items():
            summary[path] = {
                "bpm": rec.get("bpm", 0.0),
                "key": rec.get("key", "?"),
                "energy": rec.get("energy", 0),
                "cues": rec.get("cues", []),
            }
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


# ===== modules/analyzer.py 模块说明 =====
# 模块级常量：
#   _SC：静态配置单例（AGENTS.md 参数约定：采样率/跳帧/缓存路径零硬编码）
#   ANALYSIS_SAMPLE_RATE=22050 / ANALYSIS_HOP=512：分析路径参数（base.json）
#   SUPPORTED_EXTENSIONS：支持的音频扩展集合（D1.1）
#   MIN_BPM=70 / MAX_BPM=180：BPM 合理区间（DJ 折半/加倍折叠用）
#   ANALYSIS_VERSION=1：缓存算法版本（检测算法变更 +1，旧缓存自动失效）
#   _KK_MAJOR/_KK_MINOR：Krumhansl-Kessler 调性谱（24 键相关打分用）
# 类型：
#   Key(frozen dataclass)：调性对象（pitch_class/mode + standard/camelot 记谱）
#   AnalysisCache：SQLite 分析缓存（size/mtime/version 三重校验，失败降级无缓存）
# 函数（G3.3 补全）：
#   _decode_mono(path, sr)：解码为 sr Hz mono 一维（G1.1 复用 utils/audio_decode.py）
#   _pearson(x, y)：皮尔逊相关（KK 24 键打分用）
#   _cache_dir()：SQLite 缓存路径解析（cache_path 配置）
#   _default_workers()：进程池 worker 数（核数-2 受内存限制）
#   _warm_worker()：worker 初始化（numba 缓存隔离：每进程私有临时目录）
#   _analyze_task(path, with_cues)：进程池任务入口（返回 (path, record, error)）
#   main()：CLI 入口（--folder 批量分析 --json 输出）
#   parse_key(text)：标准记谱解析（"Am"/"C"/"F#m"）
#   _fold_bpm/_snap_bpm/_refine_bpm：BPM 折叠/吸附/精修（纯函数可单测）
#   _estimate_bpm/_pick_metrical_level：onset 自相关打分 + 节拍级修正（含 125BPM 先验）
#   _track_beats/_local_maxima：纯 numpy Ellis DP 拍子追踪
#   _detect_tempo(y, sr)：BPM 总入口（onset → 估计 → 修正 → DP → 精修）
#   _pick_downbeat_phase：4 拍相位低频能量最大化（D1.5；4/4 假设）
#   _detect_key(y, sr)：谐波分离 + chroma 中位数 + 24 键 KK 相关（含置信度）
#   _detect_energy(y, sr, bpm)：响度/onset 密度/低频占比/拍速加权 → 1-10
#   _detect_timbre(y, sr)：谱质心/带宽/滚降三维归一概要（PL002.4，automix 音色分）
#   _detect_cues(y, sr, bpm, beat_times)：结构聚类分段 → downbeat 吸附 → 去重
#   empty_record()：失败降级占位（bpm=0/key="?"，D1.12）
#   analyze_file(path, with_cues)：单曲分析组装（D1.2；异常上抛由批处理降级）
#   scan_folder(root)：递归扫描（D1.1）
#   analyze_many(paths, on_result, ...)：缓存先行 + 进程池批处理 + should_stop（D1.11）
# 设计理由：全部参考 cuekey（tempo/key/energy/cues/cache/analyzer 全套）；
#   纯函数与 I/O 分离保证可单测；缓存只读优化不影响正确性；
#   进程池用 spawn + numba 缓存隔离（Windows 多进程安全）
# 异常处理：单曲失败 → 批处理回调 error 继续（不中断）；缓存失败 → 降级无缓存；
#   解码失败 → 上层 empty_record 兜底（AGENTS.md 错误策略）
# 关联配置：config/static/base.json（analysis_sample_rate/analysis_hop/cache_path）


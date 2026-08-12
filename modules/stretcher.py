# 变速/变调预渲染模块：rubberband CLI 封装（唯一调用点）

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Callable

import numpy as np
import soundfile as sf

TIMEMAP_ANCHORS = 64
_PERCENT_RE = re.compile(r"^\s*(\d{1,3})%\s*$")

# R3 引擎 Pass1(Studying)≈1% 时间、Pass2(Processing)≈99%（进度权重标定）
_PASS1_WEIGHT = 0.05
_PASS2_WEIGHT = 0.95


def _bundled_rubberband() -> str | None:
    # 项目内置兜底：tools/rubberband/rubberband.exe（换电脑/未安装也可用）
    candidate = (
        Path(__file__).resolve().parents[1] / "tools" / "rubberband" / "rubberband.exe"
    )
    return str(candidate) if candidate.is_file() else None


def rubberband_bin() -> str | None:
    # 解析 rubberband 可执行文件（优先级从高到低）：
    # 1) RUBBERBAND_BIN 环境变量（显式指定） 2) 系统 PATH（用户安装优先）
    # 3) 项目内置 tools/rubberband/rubberband.exe（兜底） 4) 无 → None
    env = os.environ.get("RUBBERBAND_BIN")
    if env:
        return env
    from_path = shutil.which("rubberband")
    if from_path:
        return from_path
    return _bundled_rubberband()


def rubberband_available() -> bool:
    # 启动探测：rubberband 缺失时变速功能降级（返回 False，调用方提示）
    return rubberband_bin() is not None


def _smootherstep_integral(x: float) -> float:
    # smootherstep 原函数（S(0)=0），用于 timemap 输入帧精确换算
    return x**6 - 3 * x**5 + 2.5 * x**4


def _build_timemap(
    total_input_samples: int, start_rate: float, fade_samples: int, restore_samples: int
) -> list:
    # 构建 rubberband timemap 锚点（输出时间轴：恒速渐变段→smootherstep 恢复段→1.0）
    # 注意：首锚点必须严格晚于原点（rubberband 隐式锚定 (0,0)，显式 (0,0) 触发 NaN bug）
    points = []

    in_at_fade_end = int(round(fade_samples * start_rate))
    points.append((in_at_fade_end, fade_samples))

    if restore_samples > 0:
        for i in range(1, TIMEMAP_ANCHORS + 1):
            x = i / TIMEMAP_ANCHORS
            in_consumed_in_ramp = start_rate * x * restore_samples + (
                1.0 - start_rate
            ) * restore_samples * _smootherstep_integral(x)
            in_frame = in_at_fade_end + int(round(in_consumed_in_ramp))
            out_frame = fade_samples + int(round(x * restore_samples))
            points.append((in_frame, out_frame))

    in_at_ramp_end, out_at_ramp_end = points[-1]
    remaining_input = total_input_samples - in_at_ramp_end
    if remaining_input > 0:
        points.append((total_input_samples, out_at_ramp_end + remaining_input))

    # 严格单调 + 钳制到有效输入范围
    cleaned = []
    last_in, last_out = 0, 0
    for in_f, out_f in points:
        in_f = max(0, min(in_f, total_input_samples))
        if in_f > last_in and out_f > last_out:
            cleaned.append((in_f, out_f))
            last_in, last_out = in_f, out_f
    return cleaned


def _drain_stderr_with_progress(
    stderr, progress_callback: Callable[[float], None]
) -> None:
    # 逐字符读 rubberband stderr（CR 覆盖进度），解析 Pass N 与 <n>% 转发 0-1
    pass_idx = 0
    buf_chars = []
    while True:
        ch = stderr.read(1)
        if ch == "":
            break
        if ch in ("\r", "\n"):
            chunk = "".join(buf_chars)
            buf_chars.clear()
            if not chunk:
                continue
            if "Pass 1:" in chunk:
                pass_idx = 1
                _safe_progress(progress_callback, 0.0)
                continue
            if "Pass 2:" in chunk:
                pass_idx = 2
                _safe_progress(progress_callback, _PASS1_WEIGHT)
                continue
            m = _PERCENT_RE.match(chunk)
            if m and pass_idx in (1, 2):
                pct = min(100, int(m.group(1)))
                if pass_idx == 1:
                    frac = _PASS1_WEIGHT * (pct / 100.0)
                else:
                    frac = _PASS1_WEIGHT + _PASS2_WEIGHT * (pct / 100.0)
                _safe_progress(progress_callback, frac)
        else:
            buf_chars.append(ch)


def _safe_progress(cb: Callable[[float], None], frac: float) -> None:
    # UI 回调异常绝不允许杀死渲染线程
    try:
        cb(frac)
    except Exception:
        pass


def _run_rubberband(
    cmd: list, progress_callback: Callable[[float], None] | None
) -> None:
    # 执行 rubberband 命令（带进度解析或纯等待）；非零退出抛 RuntimeError
    if progress_callback is None:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"rubberband failed (exit {result.returncode}): {result.stderr.strip()}"
            )
        return
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    reader = threading.Thread(
        target=_drain_stderr_with_progress,
        args=(proc.stderr, progress_callback),
        daemon=True,
    )
    reader.start()
    proc.stdout.read()  # 排空 stdout 防管道阻塞
    rc = proc.wait()
    reader.join(timeout=2.0)
    _safe_progress(progress_callback, 1.0)
    if rc != 0:
        raise RuntimeError(f"rubberband failed (exit {rc})")


def _render_via_cli(
    audio: np.ndarray,
    sample_rate: int,
    args_fn: Callable[[str], list[str]],
    prefix: str,
    progress_callback: Callable[[float], None] | None = None,
) -> np.ndarray:
    # 公共渲染管道（H1.4）：tmpdir → 写 in.wav → 组命令 → 运行 → 读回校验 → 清理
    # args_fn(tmpdir) 返回额外命令行参数（如 -M timemap / --pitch）；prefix 为临时目录前缀
    if audio.ndim != 2 or audio.shape[1] != 2:
        raise ValueError(f"expected stereo (N, 2) audio, got shape {audio.shape}")
    tmpdir = tempfile.mkdtemp(prefix=prefix)
    in_path = os.path.join(tmpdir, "in.wav")
    out_path = os.path.join(tmpdir, "out.wav")
    try:
        sf.write(in_path, audio, sample_rate, subtype="FLOAT")
        cmd = [rubberband_bin(), "-3"] + args_fn(tmpdir) + [in_path, out_path]
        _run_rubberband(cmd, progress_callback)
        out, sr = sf.read(out_path, dtype="float32", always_2d=True)
        if sr != sample_rate:
            raise RuntimeError(f"rubberband returned wrong sample rate {sr}")
        if out.shape[1] == 1:
            out = np.repeat(out, 2, axis=1)
        return out.astype(np.float32)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def make_transition_buffer(
    audio: np.ndarray,
    start_rate: float,
    fade_seconds: float,
    restore_seconds: float,
    sample_rate: int = 44100,
    progress_callback: Callable[[float], None] | None = None,
) -> np.ndarray:
    # 变速渲染整段来曲余量：fade 秒恒速 start_rate → restore 秒 smootherstep 回 1.0 → 1.0 到结尾
    fade_samples = int(round(fade_seconds * sample_rate))
    restore_samples = int(round(restore_seconds * sample_rate))

    timemap = _build_timemap(len(audio), start_rate, fade_samples, restore_samples)
    total_output_samples = timemap[-1][1]
    total_duration_s = total_output_samples / sample_rate

    def _args(tmpdir: str) -> list[str]:
        # 写 timemap 文件并返回 -M/-D 参数（-3=R3；-M=timemap（-T 是恒速，勿混）；
        # -D=输出总时长（必配，否则不拉伸））
        map_path = os.path.join(tmpdir, "timemap.txt")
        with open(map_path, "w") as f:
            for in_f, out_f in timemap:
                f.write(f"{in_f} {out_f}\n")
        return ["--centre-focus", "-M", map_path, "-D", f"{total_duration_s:.6f}"]

    return _render_via_cli(audio, sample_rate, _args, "mrautodj_rb_", progress_callback)


def make_keylock_buffer(
    audio: np.ndarray,
    semitones: float,
    sample_rate: int = 44100,
    progress_callback: Callable[[float], None] | None = None,
) -> np.ndarray:
    # 变调不变速（Keylock）：rubberband --pitch 半音（保持时长，仅移动音高）
    def _args(tmpdir: str) -> list[str]:
        return ["--pitch", f"{semitones:.3f}"]

    return _render_via_cli(
        audio, sample_rate, _args, "mrautodj_keylock_", progress_callback
    )


# ===== modules/stretcher.py 模块说明 =====
# 模块级常量：
#   TIMEMAP_ANCHORS=64：timemap 恢复段锚点数
#   _PASS1_WEIGHT=0.05 / _PASS2_WEIGHT=0.95：R3 引擎两 Pass 时间占比标定
# 函数：
#   rubberband_bin()：解析可执行路径（优先级：RUBBERBAND_BIN 环境变量 →
#     系统 PATH → 项目内置 tools/rubberband/ 兜底 → None）
#   _bundled_rubberband()：项目内置路径探测（换电脑/未安装也可用）
#   rubberband_available()：启动探测（缺失返回 False，引擎降级为 skip 直混）
#   _build_timemap(...)：构建 64 锚点 timemap（恒速段→smootherstep 恢复段→1.0）
#   _smootherstep_integral(x)：smootherstep 曲线积分（恢复段位置映射，G3.3 补全）
#   _drain_stderr_with_progress/_safe_progress：CR 覆盖进度逐字符解析 + 异常隔离
#   _run_rubberband(cmd, cb)：执行命令（带进度或纯等待），非零退出抛 RuntimeError
#   make_transition_buffer(audio, start_rate, fade_s, restore_s, sr, cb)：
#     变速渲染（转场缓冲：渐变段匹配来曲 BPM，之后恢复到原速）
#   make_keylock_buffer(audio, semitones, sr, cb)：变调不变速（Keylock）
# 设计理由：唯一 rubberband 调用点（B1 纪律）；CLI 走文件临时目录渲染，
#   实时线程零依赖；timemap 首锚点必须晚于原点（(0,0) 触发 NaN bug）
# 异常处理：rubberband 非零退出/采样率不符抛 RuntimeError；进度回调异常被吞
# 关联配置：RUBBERBAND_BIN 环境变量（可选）；音频约定 (N,2) float32

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
    aux_files: dict[str, str] | None = None,
) -> np.ndarray:
    # 公共渲染管道（H1.4）：tmpdir → 写 in.wav → 附加临时文件 → 组命令 → 运行 →
    # 读回校验 → 清理；args_fn(tmpdir) 返回额外命令行参数（如 -M timemap / --pitch）；
    # aux_files 为附加临时文件（文件名→内容，文件名由调用方字面量给定），写入前
    # 规范化 + 包含校验（Mimosa 整改：写路径仅由本地 mkdtemp 目录 + 固定名构成）
    if audio.ndim != 2 or audio.shape[1] != 2:
        raise ValueError(f"expected stereo (N, 2) audio, got shape {audio.shape}")
    # I3.1：缺失前置检查（原 [None, ...] 进 subprocess 报晦涩 TypeError）
    rb = rubberband_bin()
    if rb is None:
        raise RuntimeError(
            "未找到 rubberband 可执行文件（变速/变调渲染不可用）："
            "请安装 rubberband、设置 RUBBERBAND_BIN 环境变量，"
            "或确认项目内置 tools/rubberband/ 存在"
        )
    tmpdir = tempfile.mkdtemp(prefix=prefix)
    base = Path(tmpdir).resolve()  # 规范化临时目录（防相对路径歧义）
    in_path = str(base / "in.wav")
    out_path = str(base / "out.wav")
    try:
        sf.write(in_path, audio, sample_rate, subtype="FLOAT")
        # 附加临时文件（如 timemap）：文件名固定、目录本地创建，越界即拒绝
        for fname, text in (aux_files or {}).items():
            aux = (base / fname).resolve()
            if aux.parent != base:
                raise RuntimeError(f"临时文件路径越界: {aux}")
            aux.write_text(text, encoding="utf-8")
        cmd = [rb, "-3"] + args_fn(str(base)) + [in_path, out_path]
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
    progress_callback: Callable[[float], None] | None = None,
    *,
    sample_rate: int,  # FIX005/S1：keyword-only 必填（调用方显式传 SAMPLE_RATE，防默认字面量与配置漂移）
) -> np.ndarray:
    # 变速渲染整段来曲余量：fade 秒恒速 start_rate → restore 秒 smootherstep 回 1.0 → 1.0 到结尾
    # I0.5：空输入/空 timemap 防御（CUE 越过曲尾时 cue 切片为空 → 原 timemap[-1]
    # IndexError 晦涩崩溃；改抛可读错误由 TransitionManager 回调 on_done(None, exc)）
    if audio.ndim != 2 or audio.shape[1] != 2 or audio.shape[0] <= 0:
        raise ValueError(f"变速渲染需要非空立体声输入，got shape {audio.shape}")
    fade_samples = int(round(fade_seconds * sample_rate))
    restore_samples = int(round(restore_seconds * sample_rate))

    timemap = _build_timemap(len(audio), start_rate, fade_samples, restore_samples)
    if not timemap:
        raise ValueError(
            "变速渲染 timemap 为空（输入过短或 CUE 越过曲尾），无法构建拉伸计划"
        )
    total_output_samples = timemap[-1][1]
    total_duration_s = total_output_samples / sample_rate

    def _args(tmpdir: str) -> list[str]:
        # 返回 -M/-D 参数（-3=R3；-M=timemap（-T 是恒速，勿混）；-D=输出总时长
        # （必配，否则不拉伸））；timemap 文件由 _render_via_cli 统一写入本目录
        return [
            "--centre-focus",
            "-M",
            str(Path(tmpdir) / "timemap.txt"),
            "-D",
            f"{total_duration_s:.6f}",
        ]

    timemap_text = "\n".join(f"{in_f} {out_f}" for in_f, out_f in timemap) + "\n"
    return _render_via_cli(
        audio,
        sample_rate,
        _args,
        "mrautodj_rb_",
        progress_callback,
        aux_files={"timemap.txt": timemap_text},
    )


def make_tempo_buffer(
    audio: np.ndarray,
    rate: float,
    semitones: float = 0.0,
    progress_callback: Callable[[float], None] | None = None,
    *,
    sample_rate: int,  # FIX005/S1：keyword-only 必填
) -> np.ndarray:
    # 恒速拉伸缓冲（J1.1 Keylock/Key Shift 重渲染）：整段按 rate 恒速映射
    # （输出时长 = 原时长/rate），可选 --pitch 半音变调；rate≈1 且不变调时
    # 快速路径直接返回拷贝（Keylock 开但原速的常见场景零开销）
    if audio.ndim != 2 or audio.shape[1] != 2 or audio.shape[0] < 2:
        raise ValueError(f"变速渲染需要≥2帧立体声输入，got shape {audio.shape}")
    r = float(rate)
    if not 0.05 <= r <= 20.0:
        raise ValueError(f"变速比例超界 [0.05, 20]: {r}")
    if abs(r - 1.0) < 1e-9 and semitones == 0:
        return audio.copy()
    n = audio.shape[0]
    timemap = [
        (1, max(1, int(round(1.0 / r)))),
        (n - 1, max(2, int(round((n - 1) / r)))),
    ]
    if timemap[1][1] <= timemap[0][1]:
        raise ValueError(f"变速比例过小无法构建 timemap：rate={r}")
    total_duration_s = (n / r) / sample_rate
    timemap_text = "\n".join(f"{in_f} {out_f}" for in_f, out_f in timemap) + "\n"

    def _args(tmpdir: str) -> list[str]:
        # 恒速 timemap + 输出时长（-D 必配）；--pitch 半音（Key Shift 同批渲染）
        args = [
            "--centre-focus",
            "-M",
            str(Path(tmpdir) / "timemap.txt"),
            "-D",
            f"{total_duration_s:.6f}",
        ]
        if semitones != 0:
            args += ["--pitch", f"{semitones:.3f}"]
        return args

    return _render_via_cli(
        audio,
        sample_rate,
        _args,
        "mrautodj_tempo_",
        progress_callback,
        aux_files={"timemap.txt": timemap_text},
    )


def make_keylock_buffer(
    audio: np.ndarray,
    semitones: float,
    progress_callback: Callable[[float], None] | None = None,
    *,
    sample_rate: int,  # FIX005/S1：keyword-only 必填
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

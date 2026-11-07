# 转场规划模块：判定来曲是否需要变速拉伸，以及拉伸速率（纯函数，可单测）

from __future__ import annotations

import math
from dataclasses import dataclass

from config.static.static_config import get_static_config

# 静态配置解包（转场调参，G2.1：配置驱动）
_SC = get_static_config()

# 渐变结束时可容忍的节拍漂移上限（拍）。≤0.25 拍则跳过拉伸直接混音
# 含义：±0.5BPM@30s 淡入、±1.0BPM@15s、±1.88BPM@8s；精确倍频（128↔64）恒 skip
MAX_DRIFT_BEATS = float(_SC.base.get("max_drift_beats", 0.25))

# 八度折叠后的拍速比可视为"可对拍混音"的容差（UI 匹配标记用，0.06≈手推转盘范围）
TEMPO_MATCH_TOLERANCE = float(_SC.base.get("tempo_match_tolerance", 0.06))


def fold_ratio(r: float) -> tuple[float, str]:
    # 八度折叠：把拍速比折到最接近 1.0 的解释（对数空间，每侧最多一个八度）
    # 返回 (r_eff, relation)，relation ∈ {"", "half-time", "double-time"}
    candidates = {"": r, "half-time": r / 2.0, "double-time": 2.0 * r}
    relation = min(candidates, key=lambda k: abs(math.log(candidates[k])))
    return candidates[relation], relation


def tempo_compatible(
    now_bpm: float, song_bpm: float, tolerance: float = TEMPO_MATCH_TOLERANCE
) -> bool:
    # 两曲八度折叠后是否可对拍混音（同速或近半速/双速）；任一拍速未知返回 False
    if now_bpm <= 0 or song_bpm <= 0:
        return False
    r_eff, _ = fold_ratio(now_bpm / song_bpm)
    return abs(r_eff - 1.0) <= tolerance


@dataclass
class TransitionPlan:
    # 转场计划：skip=True 直接混原始音频（不渲染）；否则按 start_rate 拉伸
    skip: bool  # True -> 不渲染 rubberband，直接混原始 CUE 音频
    start_rate: float  # r_eff，喂给拉伸器作为渐变起始速率
    matched_bpm: float  # 来曲在渐变期间的感知 BPM（next_bpm * r_eff）
    drift_beats: float  # 不拉伸时渐变结束的预计漂移拍数（诊断用）
    relation: str  # "" | "half-time" | "double-time"（状态文案）


def plan_transition(
    now_bpm: float, next_bpm: float, fade_seconds: float
) -> TransitionPlan:
    # 判定 skip-vs-stretch 与有效拉伸速率：
    # 漂移模型 drift_beats = (next_bpm/60)·|r_eff-1|·fade，≤MAX_DRIFT_BEATS 则 skip
    if now_bpm <= 0 or next_bpm <= 0:
        return TransitionPlan(
            skip=True,
            start_rate=1.0,
            matched_bpm=next_bpm,
            drift_beats=0.0,
            relation="",
        )

    r_eff, relation = fold_ratio(now_bpm / next_bpm)
    matched_bpm = next_bpm * r_eff
    drift_beats = (next_bpm / 60.0) * abs(r_eff - 1.0) * fade_seconds
    skip = drift_beats <= MAX_DRIFT_BEATS

    return TransitionPlan(
        skip=skip,
        start_rate=r_eff,
        matched_bpm=matched_bpm,
        drift_beats=drift_beats,
        relation=relation,
    )


# ===== modules/transition.py 模块说明 =====
# 模块级常量：
#   MAX_DRIFT_BEATS=0.25：skip/stretch 唯一调参点（渐变结束允许的最大漂移拍数）
#   TEMPO_MATCH_TOLERANCE=0.06：八度折叠后拍速比容差（UI "可对拍"标记）
# 类型：
#   TransitionPlan(dataclass)：skip/start_rate/matched_bpm/drift_beats/relation
# 函数：
#   fold_ratio(r)：八度折叠（对数空间最近 1.0，含 half-time/double-time 标记）
#   tempo_compatible(now_bpm, song_bpm, tolerance)：可对拍判定（列表 :) 标记用）
#   plan_transition(now_bpm, next_bpm, fade_seconds)：skip-vs-stretch 判定与速率
# 设计理由：纯函数无副作用（可单测）；漂移模型避免"半速/双速"误判
#   （64BPM 曲拉伸到 128 的经典 bug，用 r_eff 而非原始比值）
# 异常处理：无（拍速≤0 视为 skip 混音，不抛错）
# 关联配置：config/static/base.json（max_drift_beats/tempo_match_tolerance，
#   I3.4 补录——原"关联配置：无"失实）


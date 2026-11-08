# AI 自动编排模块：兼容性评分 / Set 规划 / 推荐桥（M2 核心）
# 设计：确定性编排算法（打分表 + 贪心链，非 LLM——可解释够用，KISS）；
# 纯逻辑零 GUI 依赖（分层红线），TransitionManager 桥经鸭子类型注入（不反向耦合）

from __future__ import annotations

import math
from typing import Callable

from config.static.static_config import get_static_config
from modules.analyzer import parse_key
from modules.transition import TEMPO_MATCH_TOLERANCE, fold_ratio
from utils.convert import to_float

# 静态配置解包（M2 编排参数，AGENTS.md 参数约定：零硬编码）
_SC = get_static_config()
_WEIGHTS = {
    k: float(v)
    for k, v in _SC.base.get(
        "automix_weights", {"bpm": 0.3, "key": 0.3, "energy": 0.2, "timbre": 0.2}
    ).items()
}
_TIMBRE_SIGMA = float(_SC.base.get("automix_timbre_sigma", 0.35))
_ENERGY_ARC = [float(v) for v in _SC.base.get("automix_energy_arc", [0.5, 0.8, 1.0, 1.0, 0.7])]
_SAME_ARTIST_GAP = int(_SC.base.get("automix_same_artist_gap", 3))

# Camelot 打分表（DJ 惯例）：同键 / 能量步进(同字母±1号) / 关系调(同号异字母) /
# 对角相邻(异字母±1号) / 其余 / 缺失中性
_KEY_SAME = 1.0
_KEY_ENERGY_STEP = 0.9
_KEY_RELATIVE = 0.85
_KEY_DIAGONAL = 0.6
_KEY_OTHER = 0.2
_KEY_NEUTRAL = 0.5

# 维度中性/未知哨兵分（缺数据的维度不奖励也不惩罚）
_BPM_UNKNOWN = 0.4
_DIM_UNKNOWN = 0.5


def key_score(key_a: str, key_b: str) -> float:
    # Camelot 兼容分：输入支持 Camelot 记谱（"8A"）与标准记谱（"Am"，经
    # parse_key 归一）；任一解析失败或 "?" → 中性 0.5（缺数据不奖励不惩罚）
    ka = _parse_key_any(key_a)
    kb = _parse_key_any(key_b)
    if ka is None or kb is None:
        return _KEY_NEUTRAL
    if ka[0] == kb[0]:  # 同 wheel number
        if ka[1] == kb[1]:
            return _KEY_SAME  # 同键
        return _KEY_RELATIVE  # 同号异字母 = 关系大小调
    if ka[1] == kb[1]:
        # 同字母（同调式）相邻号 = 能量步进（环形 12↔1）
        diff = abs(ka[0] - kb[0])
        if diff == 1 or diff == 11:
            return _KEY_ENERGY_STEP
        return _KEY_OTHER
    # 异字母异号：对角相邻（±1 号）或其余
    diff = abs(ka[0] - kb[0])
    if diff == 1 or diff == 11:
        return _KEY_DIAGONAL
    return _KEY_OTHER


def _parse_key_any(text: str | None):
    # 双记谱解析：Camelot（如 "8A"/"12B"）直接拆号字母；标准记谱（"Am"/"C"）经
    # analyzer.parse_key 换算 wheel/mode；非法返回 None
    text = (text or "").strip()
    if not text:
        return None
    upper = text.upper()
    if len(upper) >= 2 and upper[-1] in "AB" and upper[:-1].isdigit():
        return int(upper[:-1]), upper[-1]
    # 标准记谱两种形态："Am" 紧凑式 / "A minor" 带空格调式名（归一到紧凑式）
    compact = text
    parts = text.split()
    if len(parts) == 2 and parts[1].lower() in ("major", "minor", "maj", "min"):
        compact = parts[0] + ("m" if parts[1].lower() in ("minor", "min") else "")
    try:
        k = parse_key(compact)
    except ValueError:
        return None
    return k.wheel_number, "B" if k.mode == "major" else "A"


def bpm_score(bpm_a: float, bpm_b: float) -> float:
    # BPM 兼容分：八度折叠（复用 transition.fold_ratio）——同速 1.0；
    # half/double-time 0.75；近速线性衰减到 2×容差归零；未知 0.4
    if not bpm_a or not bpm_b or bpm_a <= 0 or bpm_b <= 0:
        return _BPM_UNKNOWN
    r_eff, relation = fold_ratio(bpm_a / bpm_b)
    if relation:
        return 0.75
    if abs(r_eff - 1.0) < 1e-9:
        return 1.0
    return max(0.0, 1.0 - abs(r_eff - 1.0) / (TEMPO_MATCH_TOLERANCE * 2))


def energy_score(energy_a: float, energy_b: float) -> float:
    # 能量兼容分：高斯衰减 σ=2（拍级相邻能量最兼容）；任一缺失（≤0）→ 0.5
    if not energy_a or not energy_b or energy_a <= 0 or energy_b <= 0:
        return _DIM_UNKNOWN
    return float(math.exp(-((energy_a - energy_b) / 2.0) ** 2))


def timbre_score(timbre_a, timbre_b) -> float:
    # 音色兼容分：三维谱概要欧氏距离高斯衰减（σ 配置 automix_timbre_sigma）；
    # 任一缺失/维度不齐 → 0.5（FIX004/M4：外部缓存宽容解析）
    if not timbre_a or not timbre_b or len(timbre_a) != 3 or len(timbre_b) != 3:
        return _DIM_UNKNOWN
    dist = math.sqrt(
        sum((to_float(x) - to_float(y)) ** 2 for x, y in zip(timbre_a, timbre_b))
    )
    return float(math.exp(-((dist / _TIMBRE_SIGMA) ** 2)))


def compatibility_score(track_a: dict, track_b: dict) -> dict:
    # 两曲兼容性评分：四维加权聚合（automix_weights 配置）；维度缺失该维取
    # 中性分并记入 warnings；返回 {overall, scores{bpm,key,energy,timbre}, warnings}
    warnings = []
    bpm_a, bpm_b = track_a.get("bpm", 0), track_b.get("bpm", 0)
    s_bpm = bpm_score(bpm_a, bpm_b)
    if not bpm_a or not bpm_b:
        warnings.append("BPM 缺失")
    key_a, key_b = track_a.get("key", "?"), track_b.get("key", "?")
    s_key = key_score(key_a, key_b)
    if key_a in ("?", None) or key_b in ("?", None):
        warnings.append("调性缺失")
    e_a, e_b = track_a.get("energy", 0), track_b.get("energy", 0)
    s_energy = energy_score(e_a, e_b)
    if not e_a or not e_b:
        warnings.append("能量缺失")
    t_a, t_b = track_a.get("timbre"), track_b.get("timbre")
    s_timbre = timbre_score(t_a, t_b)
    if not t_a or not t_b:
        warnings.append("音色缺失")

    overall = (
        _WEIGHTS.get("bpm", 0.0) * s_bpm
        + _WEIGHTS.get("key", 0.0) * s_key
        + _WEIGHTS.get("energy", 0.0) * s_energy
        + _WEIGHTS.get("timbre", 0.0) * s_timbre
    )
    return {
        "overall": float(overall),
        "scores": {"bpm": s_bpm, "key": s_key, "energy": s_energy, "timbre": s_timbre},
        "warnings": warnings,
    }


def _arc_targets(length: int) -> list[float]:
    # 能量弧线目标曲线：automix_energy_arc 模板按 length 均匀线性插值
    tmpl = _ENERGY_ARC
    if length <= 1:
        return [tmpl[0]]
    xs = [i / (length - 1) for i in range(length)]
    n = len(tmpl) - 1
    out = []
    for x in xs:
        pos = x * n
        k = min(int(pos), n - 1)
        t = pos - k
        out.append(tmpl[k] * (1.0 - t) + tmpl[k + 1] * t)
    return out


def _explanation(scores: dict) -> str:
    # 解释串：取贡献最高的两个维度（"Key 0.85；BPM 0.75" 式）
    top2 = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:2]
    return "；".join(f"{name} {val:.2f}" for name, val in top2)


def plan_set(entries: list[dict], start: dict | None = None, length: int = 8) -> dict:
    # Set 规划（贪心链）：每步从候选取 compatibility × 能量弧线贴合 最高者；
    # 约束 = 已播去重 + 同艺人间隔 automix_same_artist_gap（候选不足时放宽该
    # 约束并在 warnings 声明）；返回 {sequence, explanations, warnings, arc}
    length = max(1, int(length))
    arc = _arc_targets(length)
    sequence: list[dict] = []
    explanations: list[str] = []
    warnings: list[str] = []
    played: set[str] = set()
    if start is not None and start.get("path"):
        played.add(start["path"])

    for i in range(length):
        target = arc[i]
        relaxed = False
        picks = _pick_step(entries, played, sequence, start, target, strict=True)
        if picks is None:
            picks = _pick_step(entries, played, sequence, start, target, strict=False)
            relaxed = picks is not None
            if relaxed:
                warnings.append(f"第 {i + 1} 首候选不足，放宽同艺人约束")
        if picks is None:
            warnings.append(f"第 {i + 1} 首无可用候选，Set 提前结束")
            break
        fit, best, scores = picks
        if start is None and not sequence:
            explanations.append(f"开场：能量目标 {target:.2f}")
        elif relaxed:
            explanations.append(f"{_explanation(scores)}（降级选择）")
        else:
            explanations.append(_explanation(scores))
        sequence.append(best)
        played.add(best["path"])

    return {"sequence": sequence, "explanations": explanations, "warnings": warnings, "arc": arc}


def _pick_step(
    entries: list[dict],
    played: set[str],
    sequence: list[dict],
    start: dict | None,
    target: float,
    strict: bool,
):
    # 单步选曲：过滤（已播/同艺人间隔）→ 评分（兼容 × 弧线贴合）→ 最高者；
    # 无可用候选返回 None。当前曲 = start（首步）或 sequence[-1]
    if _SAME_ARTIST_GAP <= 1:
        recent_artists = []  # FIX004：间隔≤1 即无约束（sequence[-0:] 会成全序列；
        # start 艺人同样不排除——GAP=1 语义为"紧邻禁重复"已由顺序播放天然满足）
    else:
        recent_artists = [
            e.get("artist") for e in sequence[-(_SAME_ARTIST_GAP - 1) :] if e.get("artist")
        ]
        if start is not None and not sequence and start.get("artist"):
            recent_artists.append(start["artist"])
    current = sequence[-1] if sequence else start
    candidates = []
    for e in entries:
        if e["path"] in played:
            continue
        if strict and e.get("artist") and e["artist"] in recent_artists:
            continue
        if current is None:
            base = 0.6  # 冷启动：无兼容基准，给中性偏上（弧线主导）
            scores = {}
        else:
            comp = compatibility_score(current, e)
            base = comp["overall"]
            scores = comp["scores"]
        # FIX004/M5：能量缺失按中性 0.5 参与弧线拟合（原 0 会被高弧段
        # 权重趋 0 惩罚，违背"缺失中性"声明）
        e_now = e.get("energy") if e.get("energy") else 0.5
        fit = base * math.exp(-abs(e_now - target) / 0.3)
        candidates.append((fit, e, scores))
    if not candidates:
        return None
    # max 稳定取首个最高分（fit 相等时不比较 dict——合成曲库同分常见）
    return max(candidates, key=lambda t: t[0])


class AutomixController:
    # 推荐桥（M2 UI/自动模式入口）：持 TransitionManager（鸭子类型，不 import）+
    # 曲库/当前盘元数据的 getter（由 UI 注入 lambda）；recommend 单步推荐；
    # prepare_next 经 tm.prepare 装填；auto_mode 开 + on_mix_started = 链式自动
    def __init__(
        self,
        tm,
        entries_getter: Callable[[], list[dict]],
        now_meta_getter: Callable[[], dict],
    ):
        self._tm = tm
        self._entries_getter = entries_getter
        self._now_meta_getter = now_meta_getter
        self.auto_mode: bool = False
        self._played: list[str] = []  # 自动模式已播路径（防循环重复）

    def recommend(self, now_meta: dict | None = None) -> dict | None:
        # 推荐下一曲：排除当前曲与自动模式已播；兼容分最高者；
        # 无候选/当前 BPM 缺失 → None。返回 {entry, explanation, score}
        meta = now_meta if now_meta is not None else self._now_meta_getter()
        if not meta or not meta.get("bpm"):
            return None
        entries = self._entries_getter()
        best = None
        for e in entries:
            if meta.get("path") and e["path"] == meta.get("path"):
                continue
            if self.auto_mode and e["path"] in self._played:
                continue
            comp = compatibility_score(meta, e)
            if best is None or comp["overall"] > best[2]:
                best = (e, comp, comp["overall"])
        if best is None:
            return None
        entry, comp, score = best
        return {"entry": entry, "explanation": _explanation(comp["scores"]), "score": score}

    def prepare_next(self, now_deck, on_done=None) -> "dict | None":
        # 推荐并装填：经 tm.prepare（SKIP/STRETCH 与 downbeat 对齐全复用）；
        # 成功返回装填的 entry（调用方据此滚动 _deck_meta/pending），失败 None
        meta = self._now_meta_getter()
        rec = self.recommend(meta)
        if rec is None:
            return None
        entry = rec["entry"]
        ok = self._tm.prepare(
            now_deck,
            meta.get("bpm", 0.0),
            meta.get("downbeats", []),
            entry["path"],
            entry.get("bpm", 0.0),
            entry.get("record", {}).get("downbeats", []),
            cue_seconds=0.0,
            on_done=on_done,
        )
        return entry if ok else None

    def on_mix_started(self, now_deck, finished_path: "str | None" = None) -> "dict | None":
        # 自动模式钩子（mix 完成后由 UI 调用——FIX004.3 时序修正：原 mix_now
        # 置 MIXING 后立即调用被 tm.prepare 的 PLAYING 守卫恒拒）：
        # FIX005.2：记录**播完曲**（finished_path——旧曲，UI 在滚动 meta 前捕获）
        # 入已播（防 A→B→A 回环）；链式装填下一曲；返回装填 entry
        # （None=无推荐/守卫拒绝）。注意：正在播的来曲由 recommend 的
        # "排除当前曲"天然排除，不入 _played
        if not self.auto_mode:
            return None
        if finished_path:
            self._played.append(finished_path)
        return self.prepare_next(now_deck)


# ===== modules/automix.py 模块说明 =====
# 模块级常量：
#   _WEIGHTS：四维评分权重（base.json automix_weights，和=1）
#   _TIMBRE_SIGMA：音色高斯衰减 σ（automix_timbre_sigma）
#   _ENERGY_ARC：Set 能量弧线模板（automix_energy_arc，按 length 插值）
#   _SAME_ARTIST_GAP：同艺人间隔曲数（automix_same_artist_gap）
#   _KEY_SAME/_KEY_ENERGY_STEP/_KEY_RELATIVE/_KEY_DIAGONAL/_KEY_OTHER/_KEY_NEUTRAL：
#     Camelot 打分表（DJ 惯例：1.0/0.9/0.85/0.6/0.2/0.5）
#   _BPM_UNKNOWN=0.4 / _DIM_UNKNOWN=0.5：维度缺失中性哨兵
# 函数：
#   key_score(key_a, key_b)：Camelot 兼容分（parse_key 归一，支持标准/Camelot 记谱）
#   bpm_score(a, b)：八度折叠兼容分（复用 transition.fold_ratio）
#   energy_score(a, b)：能量差高斯衰减（σ=2）
#   timbre_score(a, b)：三维谱概要欧氏距离高斯衰减
#   compatibility_score(track_a, track_b)：四维加权聚合 + 缺失警告
#   _arc_targets(length)：弧线模板线性插值到 length 点
#   _explanation(scores)：贡献前二维度解释串
#   _pick_step(...)：单步选曲（过滤→评分→最高；strict=同艺人约束开关）
#   plan_set(entries, start, length)：贪心 Set 规划（弧线贴合 + 去重 + 间隔约束
#     + 降级声明）；返回 {sequence, explanations, warnings, arc}
# 类型：
#   AutomixController：推荐桥（recommend 单步 / prepare_next 装填（tm.prepare
#     全复用：skip-stretch 与 downbeat 对齐）/ auto_mode + on_mix_started 链式
#     自动模式；已播 _played 防自动 Set 循环重复）
# 设计理由：确定性打分 + 贪心（可解释够用，KISS）——非 LLM 路线；
#   纯逻辑零 GUI 依赖（分层红线）；tm 经鸭子类型注入不反向耦合；
#   缺失维度中性分（不奖励不惩罚）+ warnings 声明（可解释性）
# 异常处理：key 解析失败中性；bpm/energy/timbre 缺失中性；plan_set 候选耗尽
#   提前结束并声明；recommend 无候选返回 None
# 关联配置：config/static/base.json（automix_weights/automix_timbre_sigma/
#   automix_energy_arc/automix_same_artist_gap）；modules/analyzer（parse_key）、
#   modules/transition（fold_ratio/TEMPO_MATCH_TOLERANCE）复用

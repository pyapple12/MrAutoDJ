# 变速转场集成模块：双盘"预备→混音"编排（D3，参考 B1 app.py 的 prepare/mix/epoch/stale）
# 语义：在 now_deck 上用 B1 的单引擎混音机制无缝接歌（start_mix 样本级定时切歌），
# next_deck 作为"下一曲载体"（供监听/元数据）；epoch 计数器使陈旧预渲染失效

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Callable

from config.static.static_config import get_static_config
from modules.engine import KEY_SHIFT_MAX, SAMPLE_RATE, State
from modules.stretcher import make_keylock_buffer, make_transition_buffer
from modules.transition import TransitionPlan, plan_transition

if TYPE_CHECKING:
    import numpy as np  # 仅注解用（I3.2：运行时零使用，TYPE_CHECKING 守卫）

# 静态配置解包（对齐点余量：下拍触发前的最短提前量，秒）
_SC = get_static_config()

# 混音触发提前量：对齐点必须晚于当前播放位置 + 此余量（避免触发点在当前帧内）
MIX_TRIGGER_MARGIN_SECONDS = float(_SC.base.get("mix_trigger_margin_seconds", 0.1))

# 对拍失败时的默认淡化时长（秒，B1 默认 16s）
DEFAULT_FADE_SECONDS = float(_SC.base.get("default_fade_seconds", 16.0))
# 变速恢复时长（秒，B1 默认 30s：STRETCH 缓冲渐变回原速的时长）
DEFAULT_RESTORE_SECONDS = float(_SC.base.get("default_restore_seconds", 30.0))

# 转场 EQ 渐变（PL002.10）：步数配置 + 步进间隔 = fade/(steps*2)（8 步在
# 半程收尾，FIX004/T5 注释对齐实现）——low 从全切到 0 的斜坡，
# 经 UI 线程等价的 setter 分步执行（回调线程零改动）
EQ_RAMP_STEPS = int(_SC.base.get("eq_ramp_steps", 8))


def _prepare_work(manager, next_path: str, my_epoch: int, plan: TransitionPlan) -> None:
    # 预备后台线程（H3.2：原 prepare 内嵌套闭包 _work 提升为模块级函数）：
    # 解码 → 切 CUE → SKIP 原始缓冲 / STRETCH 变速渲染 → Key Shift 变调 →
    # epoch 校验后安装结果并回调 on_done(plan, error)
    try:
        audio = manager._engine.load_audio(next_path)
        cue_audio = audio[manager._cue_sample :]
        if plan.skip:
            buf = cue_audio
        else:
            buf = make_transition_buffer(
                cue_audio,
                plan.start_rate,
                manager._fade_seconds,
                manager._restore_seconds,
                sample_rate=SAMPLE_RATE,
            )
        # Key Shift：变速后按半音变调（Keylock 管线扩展）
        if manager._key_shift != 0:
            buf = make_keylock_buffer(
                buf, float(manager._key_shift), sample_rate=SAMPLE_RATE
            )
        with manager._lock:
            if manager._prep_epoch != my_epoch:
                return  # 已被新预备/参数变更取代，丢弃结果
            manager._next_prepared = buf
            manager._next_plan = plan
            manager._preparing = False
            cb = manager._on_prepared
        if cb is not None:
            cb(plan, None)
    except Exception as exc:
        with manager._lock:
            if manager._prep_epoch != my_epoch:
                return
            manager._preparing = False
            manager._next_prepared = None
            manager._next_plan = None
            cb = manager._on_prepared
        if cb is not None:
            cb(None, exc)


def _eq_ramp_worker(deck, fade_seconds: float, token: int, manager, delay: float) -> None:
    # 转场 EQ 渐变（PL002.10，worker 线程允许 IO）：delay（scheduled 对齐等待）
    # 后，low 从 -1（全切）分 EQ_RAMP_STEPS 步斜坡回 0——经典 low-cut 交接；
    # token 不匹配（新 mix/mark_stale 抢占）即退出
    if delay > 0:
        time.sleep(delay)
    interval = max(0.05, fade_seconds / (EQ_RAMP_STEPS * 2))
    for step in range(EQ_RAMP_STEPS + 1):
        with manager._lock:
            if manager._eq_ramp_token != token:
                return
        deck.eq.set_low(-1.0 + (1.0 / EQ_RAMP_STEPS) * step)
        time.sleep(interval)


class TransitionManager:
    # 转场管理器：prepare（SKIP/STRETCH 预渲染，后台线程 + epoch 防陈旧）→
    # mix_now（样本级对齐混音 + 守卫）→ mark_stale（参数变更失效旧缓冲）
    def __init__(self, engine):
        # 初始化：绑定引擎；转场状态由本管理器自己的锁保护（与引擎锁分离）
        self._engine = engine
        self._lock = threading.Lock()
        # 已预备的来曲缓冲与计划（None=无）
        self._next_prepared: np.ndarray | None = None
        self._next_plan: TransitionPlan | None = None
        # 预备中标记与参数快照（epoch 一致性校验用）
        self._preparing: bool = False
        self._prep_epoch: int = 0
        self._now_downbeats: list = []
        self._cue_sample: int = 0
        self._fade_seconds: float = DEFAULT_FADE_SECONDS
        self._restore_seconds: float = DEFAULT_RESTORE_SECONDS
        # 混音进度回调（on_done(plan, error)），由调用方保证线程安全（UI 用信号）
        self._on_prepared: Callable | None = None
        # 转场 EQ 渐换代次（PL002.10：新 mix/mark_stale 抢占旧渐变线程）
        self._eq_ramp_token: int = 0

    # --- 只读状态（UI 展示用） ---

    @property
    def is_preparing(self) -> bool:
        # 预备中（UI 显示进度/禁用按钮）
        with self._lock:
            return self._preparing

    @property
    def has_prepared(self) -> bool:
        # 已有可用缓冲（UI 显示"可以 Mix"）
        with self._lock:
            return self._next_prepared is not None

    def prepared_info(self) -> dict:
        # 当前预备状态摘要（UI 状态栏用）：skip/relation/bpm
        with self._lock:
            plan = self._next_plan
            if plan is None:
                return {"prepared": False}
            return {
                "prepared": True,
                "skip": plan.skip,
                "relation": plan.relation,
                "matched_bpm": plan.matched_bpm,
            }

    # --- D3.3 失效机制 ---

    def mark_stale(self) -> None:
        # 参数（CUE/Fade/换曲）变更后调用：epoch+1 丢弃 in-flight worker 结果，
        # 并清空已完成缓冲（旧缓冲依赖已变更参数，B1 真实 bug 教训）；
        # EQ 渐变 token+1（PL002.10：在途渐变线程退出）
        with self._lock:
            self._prep_epoch += 1
            self._preparing = False
            self._next_prepared = None
            self._next_plan = None
            self._eq_ramp_token += 1

    # --- D3.1 预备 ---

    def prepare(
        self,
        now_deck,
        now_bpm: float,
        now_downbeats: list,
        next_path: str,
        next_bpm: float,
        next_downbeats: list,
        cue_seconds: float = 0.0,
        fade_seconds: float = DEFAULT_FADE_SECONDS,
        restore_seconds: float = DEFAULT_RESTORE_SECONDS,
        key_shift: int = 0,
        on_done: Callable | None = None,
    ) -> bool:
        # 预备来曲：判定 SKIP/STRETCH → 后台线程解码+渲染（key_shift≠0 时再变调）
        # → 完成后校验 epoch 安装。on_done(plan, error)：成功 plan 非 None；失败 error 非 None
        with self._lock:
            # 守卫：当前盘必须在播且已知 BPM（无 BPM 无法判定拉伸速率）
            if now_deck.state != State.PLAYING or now_bpm <= 0:
                return False
            if self._preparing:
                return False
            plan = plan_transition(now_bpm, next_bpm, fade_seconds)
            self._preparing = True
            self._prep_epoch += 1
            my_epoch = self._prep_epoch
            self._on_prepared = on_done
            self._now_downbeats = list(now_downbeats)
            self._cue_sample = int(cue_seconds * SAMPLE_RATE)
            self._fade_seconds = fade_seconds
            self._restore_seconds = restore_seconds
            self._key_shift = max(-KEY_SHIFT_MAX, min(KEY_SHIFT_MAX, int(key_shift)))

        threading.Thread(
            target=_prepare_work, args=(self, next_path, my_epoch, plan), daemon=True
        ).start()
        return True

    # --- D3.2 混音 ---

    def mix_now(self, now_deck) -> bool:
        # 混入已预备的来曲：样本级对齐（now_deck 下一个 downbeat 触发，SKIP 才可对齐）
        # 或立即启动；非 PLAYING/挂起中/无缓冲/预备中一律拒绝（返回 False，B1 守卫纪律）
        with self._lock:
            # FIX005/T3：死条件删除（MIXING 已被首条件排除）；补挂起重入拒绝
            # （原注释声明但 pending 窗口未覆盖，二次 mix_now 覆盖缓冲）
            if now_deck.state != State.PLAYING or now_deck.pending_mix:
                return False
            if (
                self._preparing
                or self._next_prepared is None
                or self._next_plan is None
            ):
                return False
            buf = self._next_prepared
            plan = self._next_plan
            fade = self._fade_seconds
            downbeats = list(self._now_downbeats)  # FIX005/T4：随缓冲锁内取出
            # 取走缓冲后清空槽位（一次性消费，B1 纪律）
            self._next_prepared = None
            self._next_plan = None

        scheduled = None
        if plan.skip and downbeats:
            # 对齐：now_deck 下一个 downbeat（晚于当前位置+余量）；否则立即启动
            margin = int(MIX_TRIGGER_MARGIN_SECONDS * SAMPLE_RATE)
            candidates = [
                d for d in downbeats if d > now_deck.position + margin
            ]
            if candidates:
                scheduled = candidates[0]

        now_deck.start_mix(buf, fade, scheduled_start_sample=scheduled)
        # FIX005/T2：start_mix 守卫拒（取缓冲与调用间隙曲终置 IDLE）时如实
        # 返回 False——原无条件 True 使 UI 误报"Mix 开始"且 pending 滞留
        if now_deck.state == State.IDLE:
            return False
        # 转场 EQ 渐变（PL002.10）：low 全切→0 斜坡；scheduled 时先等对齐触发
        # （延迟 = 触发点距当前位置的时长，避免触发前就切低频）
        with self._lock:
            self._eq_ramp_token += 1
            token = self._eq_ramp_token
        delay = (
            max(0.0, (scheduled - now_deck.position) / SAMPLE_RATE)
            if scheduled is not None
            else 0.0
        )
        threading.Thread(
            target=_eq_ramp_worker,
            args=(now_deck, fade, token, self, delay),
            daemon=True,
        ).start()
        return True


# ===== modules/transition_manager.py 模块说明 =====
# 模块级常量：
#   MIX_TRIGGER_MARGIN_SECONDS=0.1：对齐触发提前量（防止触发点落在当前帧内）
#   DEFAULT_FADE_SECONDS=16.0 / DEFAULT_RESTORE_SECONDS=30.0：B1 默认淡入/恢复时长
# 类型：
#   TransitionManager：转场编排（prepare/mix_now/mark_stale + 只读状态）
# 函数/方法：
#   is_preparing / has_prepared / prepared_info：UI 状态只读（独立锁保护）
#   mark_stale()：D3.3 参数变更失效（epoch+1 丢弃 in-flight + 清空已完成缓冲）
#   prepare(now_deck, now_bpm, now_downbeats, next_path, next_bpm, next_downbeats,
#           cue_seconds, fade_seconds, restore_seconds, on_done) -> bool：
#     D3.1 守卫（当前盘 PLAYING 且 BPM 已知且未在预备）→ plan_transition 判定 →
#     后台线程解码+渲染（SKIP 原始切片 / STRETCH rubberband 变速）→ epoch 校验后安装
#   mix_now(now_deck) -> bool：
#     D3.2 守卫（PLAYING 且非 MIXING 且缓冲就绪）→ 取走缓冲 → SKIP 且 A 曲有
#     downbeat 时样本级定时启动（scheduled_start_sample），否则立即 → start_mix；
#     启动后 EQ 渐变线程（PL002.10：low -1→0 斜坡 8 步，scheduled 时延迟到触发；
#     token 抢占退出——mark_stale/新 mix 使在途渐变失效）
#   _eq_ramp_worker(deck, fade, token, manager, delay)：渐变 worker（模块级，
#     H3.2 纪律——def 内 def 不落；worker 线程允许 IO/setter，回调零改动）
# 设计理由：参考 B1 app.py（action_prepare_mix/action_mix_now/_commit_mix/_prep_epoch/
#   _mark_stale 机制），抽成无 GUI 依赖的类便于无头测试；epoch 计数器解决
#   "过期异步结果"（B1 Key invariants：worker 完成时比对启动时的 epoch，不一致即丢弃）
# 异常处理：解码/渲染失败 → on_done(None, exc) + 清状态（不崩溃）；
#   陈旧 worker 结果静默丢弃（不回调）
# 关联配置：config/static/base.json（sample_rate）；transition.py/stretcher.py 复用

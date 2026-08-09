# 音频引擎模块：双打碟机 + 混音 + EQ + 横推（M1 核心，占位待实现）
#
# 设计要点（参考 w.study.md B1/B12 研读结论）：
# - 一个常驻 sd.OutputStream + threading.Lock；状态机 IDLE/PLAYING/MIXING
# - 实时回调纪律：零 IO、零分配、锁内操作保持短；回调异常 fail-soft（静音降级）
# - 变速变调走离线预渲染（rubberband），实时线程只做混音/EQ/横推
# - 引擎内部控制对象（CO）总线思想：deck 控制全部走命名控制对象（对齐 Mixxx）

from enum import Enum


class DeckState(Enum):
    # 打碟机状态（占位，M1 实现）
    IDLE = "idle"
    LOADING = "loading"
    PLAYING = "playing"
    PAUSED = "paused"


class AudioEngine:
    # 音频引擎（占位：M1 实现双 deck 播放/混音/EQ/横推）
    pass


# ===== modules/engine.py 模块说明 =====
# 模块级类型：
#   DeckState(Enum)：打碟机状态（IDLE/LOADING/PLAYING/PAUSED）
# 类型：
#   AudioEngine：音频引擎占位（M1 实现）
# 关联配置：config/static/base.json（sample_rate/block_size/channels）

# 音频解码工具：pydub 解码 + 按位深动态归一化（engine/analyzer 共用，G1.1 去重）
# 约定：输出 (N, channels) float32 [-1,1]；位深归一化 16-bit /32768、24/32-bit /2^(8w-1)

from __future__ import annotations

import numpy as np


def decode_audio(path: str, channels: int, frame_rate: int) -> np.ndarray:
    # 解码任意 ffmpeg 支持格式 → (N, channels) float32 @ frame_rate；按位深归一化
    # （16-bit PCM /32768；24/32-bit int /2^(8*width-1)，B1 只处理了 16-bit 的扩展）
    from pydub import AudioSegment  # 重依赖延迟导入（AGENTS.md 例外条款）

    seg = AudioSegment.from_file(path)
    seg = seg.set_channels(channels).set_frame_rate(frame_rate)
    raw = np.array(seg.get_array_of_samples(), dtype=np.float32)
    if seg.sample_width <= 2:
        norm = 32768.0
    else:
        norm = float(2 ** (8 * seg.sample_width - 1))
    return raw.reshape(-1, channels) / norm


# ===== utils/audio_decode.py 模块说明 =====
# 函数：
#   decode_audio(path, channels, frame_rate)：pydub 解码 → 按位深归一化 →
#     (N, channels) float32；采样率/声道由调用方指定（引擎 44100 立体声、
#     分析 22050 mono 各自传参）
# 设计理由：engine.load_audio 与 analyzer._decode_mono 此前各写一份解码
#   且归一化不一致（固定 32768 vs 按位深），G1.1 统一为单一实现；
#   pydub 重依赖延迟导入（仅解码路径触发）
# 关联配置：无（参数由调用方传入）

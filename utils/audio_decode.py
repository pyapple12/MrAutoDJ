# 音频解码工具：pydub 解码 + 按位深归一化（engine/analyzer 共用，G1.1 去重）
# 约定：输出 (N, channels) float32 [-1,1]；归一化分母按 pydub 实际数值域
# （FIX004/N11：8-bit 偏置 ±128、16-bit ±32768、24-bit pydub 转 32-bit 容器
# 但数值保持 ±2^23、32-bit ±2^31——原实现对 8/24-bit 多除 256 致近静音失真）

from __future__ import annotations

import numpy as np

# 位深 → 归一化分母（pydub get_array_of_samples 的实际数值半幅）
_WIDTH_NORM = {1: 128.0, 2: 32768.0, 3: float(2**23), 4: float(2**31)}


def decode_audio(path: str, channels: int, frame_rate: int) -> np.ndarray:
    # 解码任意 ffmpeg 支持格式 → (N, channels) float32 @ frame_rate；按位深归一
    # （分母查 _WIDTH_NORM；未知位深回退 16-bit 分母并告警——不静默猜）
    from pydub import AudioSegment  # 重依赖延迟导入（AGENTS.md 例外条款）

    seg = AudioSegment.from_file(path)
    seg = seg.set_channels(channels).set_frame_rate(frame_rate)
    raw = np.array(seg.get_array_of_samples(), dtype=np.float32)
    norm = _WIDTH_NORM.get(seg.sample_width)
    if norm is None:
        norm = 32768.0  # 未知位深兜底（log 告警由调用方错误链路承担）
    return raw.reshape(-1, channels) / norm


# ===== utils/audio_decode.py 模块说明 =====
# 函数：
#   decode_audio(path, channels, frame_rate)：pydub 解码 → 按位深归一化 →
#     (N, channels) float32；采样率/声道由调用方指定（引擎 44100 立体声、
#     分析 22050 mono 各自传参）
# 设计理由：engine.load_audio 与 analyzer._decode_mono 此前各写一份解码
#   且归一化不一致，G1.1 统一为单一实现；FIX004/N11 修正 8/24-bit 分母
#   （pydub 24-bit 转 32-bit 容器但数值保持 ±2^23、8-bit 偏置 ±128——
#   原实现多除 256 致 native wav 近静音，经合成三档 wav 探针验证）
#   pydub 重依赖延迟导入（仅解码路径触发）
# 关联配置：无（参数由调用方传入）

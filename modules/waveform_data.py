# 波形数据服务（PL005.3）：峰值降采样与二进制帧打包
# 从 ui/waveform_widget._build_peaks 抽公共（UI 与 WS 网关共用同一算法；
# ui/ 允许 import modules/——单向分层 utils→config→modules→ui 不破坏）

from __future__ import annotations

import numpy as np

# 二进制峰值帧幻数（协议 §4.2：服务端下行 f32 LE，帧头校验用）
WAVE_MAGIC = b"MRWK"


def build_peaks(audio: np.ndarray | None, width: int) -> np.ndarray:
    # 双通道峰值降采样：每像素列取 [min, max]（返回 (width, 2) float32）
    # 逻辑与原 ui/waveform_widget._build_peaks 一致（含 1D mono 输入防护）
    if audio is None or len(audio) == 0 or width <= 0:
        return np.zeros((max(1, width), 2), dtype=np.float32)
    n = len(audio)
    mono = audio if audio.ndim == 1 else np.mean(audio, axis=1)
    mono = np.asarray(mono, dtype=np.float64)
    if n <= width:
        # 短音频：直接重采样到目标宽度
        idx = np.linspace(0, n - 1, width).astype(int)
        col = mono[idx]
        return np.stack([col, col], axis=1).astype(np.float32)
    per = n // width
    peaks = np.zeros((width, 2), dtype=np.float32)
    for i in range(width):
        seg = mono[i * per : (i + 1) * per]
        peaks[i, 0] = seg.min()
        peaks[i, 1] = seg.max()
    return peaks


def peaks_bytes(peaks: np.ndarray) -> bytes:
    # 峰值数组 → 二进制帧载荷（幻数 + f32 LE 数据；客户端按 (len-8)/8 列解析）
    data = np.ascontiguousarray(peaks, dtype="<f4").tobytes()
    return WAVE_MAGIC + data


def peaks_from_bytes(payload: bytes) -> np.ndarray:
    # 二进制帧载荷 → 峰值数组（客户端解析路径；坏帧返回空数组）
    if not payload.startswith(WAVE_MAGIC) or len(payload) < 12:
        return np.zeros((0, 2), dtype=np.float32)
    arr = np.frombuffer(payload[4:], dtype="<f4")
    if arr.size % 2 != 0:
        return np.zeros((0, 2), dtype=np.float32)
    return arr.reshape(-1, 2)


# ===== modules/waveform_data.py 模块说明 =====
# 类型：
#   无类——两个纯函数 + 一个帧幻数常量
# 函数：
#   build_peaks(audio, width)：audio (N,2)/(N,) → peaks (width,2) float32
#     （每像素列 [min,max]；n≤width 时重采样填充；零输入返回零数组）
#   peaks_bytes(peaks)：peaks → bytes（WAVE_MAGIC 4B + f32 LE min/max 交错）
#   peaks_from_bytes(payload)：bytes → (M,2) 数组（幻数/长度校验，坏帧空数组）
# 设计理由：
#   峰值算法原在 ui/waveform_widget 私有——WS 网关（modules/gateway）需要同一
#   算法输出二进制帧给 Web 前端，抽公共模块消除双实现漂移（DRY）；UI 侧改为
#   import 本模块（ui→modules 单向依赖合法）
# 异常处理：
#   零长度/非法 width 返回零数组不抛；from_bytes 坏幻数/奇数长度返回空数组
#   （宽容解析，对齐错误策略"坏数据不崩溃"）
# 关联配置：无（纯函数）；关联协议：docs/ipc_protocol.md §4.2 二进制峰值帧

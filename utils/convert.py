# 弹性类型转换模块：外部数据（分析结果/JSON）数字字段可能是字符串，宽容转换不崩溃（对齐 mrboard）

import math
from typing import Any


def to_float(value: Any, default: float = 0.0) -> float:
    # 弹性浮点转换：数字/数字字符串均可，失败/nan/inf 返回 default
    # （I2.6：不拦 nan/inf 会把坏数据当有效值污染 BPM/能量等下游计算）
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(result):
        return default
    return result


# ===== utils/convert.py 模块说明 =====
# 函数：
#   to_float(value, default=0.0)：单级 float() 兜底，None/垃圾/nan/inf 回 default
#   （G3.1：删除零调用的 to_int/to_optional_float，保留核心弹性转换；
#     I2.6 补 nan/inf 拦截——A003 P3 遗留项）
# 设计理由：分析缓存/配置的 BPM/能量等数字字段可能以字符串存储（新旧格式混合）
# 异常处理：所有转换异常内部消化，绝不外抛
# 关联配置：无（通用工具，业务模块按需复用）

# 全局缩放因子（J4 批次 4）：ui.json ui_scale 配置，启动时读取（修改后重启生效）
# 原语控件/间距的基准尺寸统一乘系数——与主题/贴图协同（贴图按分辨率键控天然适配）

from __future__ import annotations

from config.static.static_config import get_static_config

SCALE = float(get_static_config().ui.get("ui_scale", 1.0))


def s(value: int | float) -> int:
    # 基准尺寸 × 全局缩放（J4）；结果 ≥1 防零尺寸
    return max(1, int(round(value * SCALE)))


# ===== ui/scale.py 模块说明 =====
# 模块级常量：
#   SCALE：全局缩放因子（ui.json ui_scale，默认 1.0；启动读取，改配置重启生效）
# 函数：
#   s(value)：基准尺寸缩放换算（控件 setFixedSize/setMinimumSize/间距/圆角
#     统一入口；运行时读模块全局，测试可 monkeypatch SCALE）
# 设计理由：批次 0 定基准尺寸、批次 4 统一乘系数（避免返工，方案约定）；
#   缩放作为外观层基础设施与主题/贴图协同（贴图键含尺寸天然按分辨率生成）
# 异常处理：缩放结果钳 ≥1；非数值基准由调用方保证
# 关联配置：config/static/ui.json（ui_scale）

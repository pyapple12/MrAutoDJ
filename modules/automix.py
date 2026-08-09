# AI 自动编排模块：兼容性评分 / 转场计划 / Set 规划（M2 核心，占位待实现）
#
# 设计要点（参考 w.study.md B5/B6 研读结论）：
# - 兼容性评分：BPM 倍频归一化 / Camelot 档位 / 能量曲线 / 音色 / 人声冲突
# - 转场计划：退出点=最近不晚于目标的 downbeat，入场点=来曲第一 downbeat
# - Set 约束：同艺人限制、去重 key、能量弧线


def compatibility_score(track_a: dict, track_b: dict) -> dict:
    # 两曲兼容性评分（占位：M2 实现五维评分，返回 {overall, scores, warnings}）
    return {"overall": 0.5, "scores": {}, "warnings": []}


# ===== modules/automix.py 模块说明 =====
# 函数：
#   compatibility_score(track_a, track_b)：两曲兼容性评分占位（M2 实现）
# 关联配置：config/static/base.json（无直接依赖，M2 定案）

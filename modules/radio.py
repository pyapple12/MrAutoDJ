# 电台调度模块：LLM 导演 / 混合播放队列 / 点歌（M3 核心，占位待实现）
#
# 设计要点（参考 w.study.md B7/B9/B10/B11 研读结论）：
# - 混合物品队列（song|tts|silence）顺序播放（claudio 模式）
# - LLM 导演一次调用规划一组曲（radio-dj 模式）；失败确定性回退，绝不静默
# - 控制面 portmanteau 工具 + MCP/REST 双入口（mixx-dj-mcp 模式）
# - 点歌状态机 NEW→ACCEPTED→PLAYING→PLAYED（wrzdj 模式）


def plan_tanda(tracks: list) -> dict:
    # 规划一组曲目与口播（占位：M3 实现 LLM 导演）
    return {"setlist": [], "breaks": [], "warnings": []}


# ===== modules/radio.py 模块说明 =====
# 函数：
#   plan_tanda(tracks)：LLM 导演规划占位（M3 实现）
# 关联配置：M3 定案（凭据存 ~/.config/mrautodj/，不随项目走）

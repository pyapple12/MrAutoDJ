# 曲目分析模块：BPM/调性/能量/拍点检测（M1 分析管线，占位待实现）
#
# 设计要点（参考 w.study.md B4 研读结论）：
# - 分析管线模块化：tempo/key/energy/cues 各子模块独立实现
# - 分析用独立 22050Hz mono 路径，与引擎数组不共享（AGENTS.md 音频数组约定）
# - 分析结果带版本号缓存（SQLite/JSON），文件变化自动失效
# - 单曲分析失败降级 empty_record()（bpm=0/key="?"），不拖垮曲库

# 分析失败时的占位记录（bpm=0/key="?" 语义：未记录）
def empty_record() -> dict:
    # 返回默认分析记录（bpm=0/key="?"/beats 空），用于分析失败或未缓存降级
    return {"bpm": 0.0, "key": "?", "beats": [], "downbeats": []}


def analyze_file(path: str) -> dict:
    # 分析单曲：返回 {bpm, key, beats, downbeats}（占位：M1 实现 librosa 管线）
    return empty_record()


# ===== modules/analyzer.py 模块说明 =====
# 函数：
#   empty_record()：默认分析记录（bpm=0/key="?"/beats 空）——失败降级不崩溃
#   analyze_file(path)：单曲分析占位（M1 实现 librosa beat_track + KK chroma）
# 关联配置：config/static/base.json（analysis_sample_rate/analysis_hop/cache_path）

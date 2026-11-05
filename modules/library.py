# 曲库模块：条目构造与艺人解析（M2 转正——扫描与分析在 analyzer.py，本模块只做
# 曲库条目的元数据装配：文件名艺人解析 + 分析记录 → automix 可消费的条目结构）

from __future__ import annotations

from pathlib import Path


def parse_artist(path: str) -> str | None:
    # 文件名艺人解析（宽容约定："Artist - Title.ext" 首个 " - " 分割取左段；
    # 无分隔符 / 空段 / 超长（>40 字）→ None——同艺人约束对该曲自动跳过）
    stem = Path(path).stem
    if " - " not in stem:
        return None
    artist = stem.split(" - ", 1)[0].strip()
    if not artist or len(artist) > 40:
        return None
    return artist


def entry_from(path: str, record: dict | None) -> dict:
    # 分析记录 → 曲库条目（automix/UI 消费的统一结构；宽容解析——record 缺失
    # 或字段缺失走零值/占位，与 analyzer.empty_record 语义一致）
    record = record or {}
    return {
        "path": path,
        "name": Path(path).name,
        "artist": parse_artist(path),
        "bpm": float(record.get("bpm", 0.0) or 0.0),
        "key": record.get("key", "?") or "?",
        "energy": int(record.get("energy", 0) or 0),
        "timbre": record.get("timbre"),
        "record": record,
    }


# ===== modules/library.py 模块说明 =====
# 函数：
#   parse_artist(path)：文件名艺人解析（"Artist - Title" 约定，宽容降级 None）
#   entry_from(path, record)：分析记录 → 曲库条目（{path, name, artist, bpm,
#     key, energy, timbre, record}；零新依赖，不解析 ID3）
# 设计理由：扫描/分析职责留在 analyzer.py（单一来源），本模块只做 automix 可
#   消费的条目装配；艺人取文件名约定（M2 边界：ID3 解析需新依赖，不做）
# 异常处理：record None/字段缺失全兜底（宽容解析，AGENTS.md 错误策略）
# 关联配置：无

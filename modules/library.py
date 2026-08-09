# 曲库模块：扫描 + 分析缓存（M1 曲库管理，占位待实现）
#
# 设计要点（参考 w.study.md B4 研读结论）：
# - 递归扫描支持格式（mp3/flac/wav/ogg/m4a 等）
# - 分析缓存：键为绝对路径 + size + mtime + 算法版本（自动失效）
# - 缓存数据库只读连接（mode=ro），从源头杜绝误写（AGENTS.md 错误策略）


def scan_folder(root: str) -> list:
    # 递归扫描音频文件（占位：M1 实现）
    return []


# ===== modules/library.py 模块说明 =====
# 函数：
#   scan_folder(root)：递归扫描支持格式的音频文件（占位）
# 关联配置：config/static/base.json（cache_path）

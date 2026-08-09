# pathlib 封装的 JSON 读写与缓存单例模块（对齐 mrboard）

import json
import os
import tempfile
from pathlib import Path
from typing import Any

# 项目根目录（utils/ 的父目录），get_project_root 校验用
_PROJECT_ROOT = Path(__file__).resolve().parents[1]

_json_cache: dict[Path, Any] = {}


def get_project_root() -> Path:
    # 获取项目根目录并校验 main.py 存在（防止目录层级偏移）
    if not (_PROJECT_ROOT / "main.py").is_file():
        raise RuntimeError(f"项目根目录检测失败：{_PROJECT_ROOT} 下缺少 main.py")
    return _PROJECT_ROOT


def read_json(path: Path, default: Any = None, use_cache: bool = True) -> Any:
    # 读取 JSON 文件（默认带内存缓存；use_cache=False 强制读最新文件），文件不存在或解析失败时返回 default
    path = Path(path)
    if use_cache and path in _json_cache:
        return _json_cache[path]
    if not path.is_file():
        if use_cache:
            _json_cache[path] = default
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        if use_cache:
            _json_cache[path] = default
        return default
    if use_cache:
        _json_cache[path] = data
    return data


def write_json(path: Path, data: Any) -> None:
    # 写入 JSON 文件（原子写：临时文件 + os.replace），并更新缓存
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, ensure_ascii=False, indent=2)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, str(path))
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    _json_cache[path] = data


def clear_cache() -> None:
    # 清空内存缓存单例（文件被外部修改后调用以强制重读）
    _json_cache.clear()


# ===== utils/file_utils.py 模块说明 =====
# 模块级变量：
#   _json_cache：缓存单例 dict[Path, Any]，避免高频读配置重复 IO
# 函数：
#   get_project_root()：返回项目根目录（校验 main.py 存在，防止层级偏移）
#   read_json(path, default=None, use_cache=True)：
#     输入：path 文件路径（Path 或 str 均可），default 兜底值，
#       use_cache=False 时绕过缓存强制读最新文件（用户可手改的文件适用）
#     输出：解析后的数据；文件不存在/损坏/编码异常时返回 default
#     设计理由：宽容解析（AGENTS.md 错误策略）：配置文件损坏不崩溃
#   write_json(path, data)：原子写（mkstemp 临时文件 + os.replace），失败清理临时文件并重抛
#   clear_cache()：清空缓存单例
# 关联配置：无（通用工具，config/settings.py、config/static/static_config.py 复用）

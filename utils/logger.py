# 统一日志配置模块（对齐 mrboard：控制台 + 文件双通道，文件失败降级仅控制台）

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.static.static_config import get_static_config

# 静态配置解包（H2.4：日志路径/轮转参数配置驱动，base.json）
_SC = get_static_config()
_LOG_DIR_CFG = str(_SC.base.get("log_dir", "") or "")
_LOG_MAX_BYTES = int(_SC.base.get("log_max_bytes", 5 * 1024 * 1024))
_LOG_BACKUP_COUNT = int(_SC.base.get("log_backup_count", 5))

# 日志路径：显式配置优先；否则按平台默认（Windows → LOCALAPPDATA，其他 → ~/.local/share）
if _LOG_DIR_CFG:
    LOG_DIR = Path(_LOG_DIR_CFG)
elif os.name == "nt":
    LOG_DIR = (
        Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        / "MrAutoDJ"
    )
else:
    LOG_DIR = Path.home() / ".local" / "share" / "mrautodj"
LOG_FILE = LOG_DIR / "mrautodj.log"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def get_logger(name: str) -> logging.Logger:
    # 获取统一配置的日志器：首次调用时初始化控制台+文件双 handler（幂等）
    global _configured
    if not _configured:
        _setup_handlers()
        _configured = True
    return logging.getLogger(name)


def _setup_handlers() -> None:
    # 初始化根日志器：控制台 handler + UTF-8 轮转文件 handler（文件失败降级仅控制台）
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # H2.4：stderr 控制台用 errors=replace 兜底（特殊字符不再抛 UnicodeEncodeError）
    try:
        sys.stderr.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(console_handler)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        # H2.4：RotatingFileHandler 轮转（防长跑日志无限增长，参数进 base.json）
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=_LOG_MAX_BYTES,
            backupCount=_LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        root.addHandler(file_handler)
    except OSError:
        # 文件日志不可用（权限/磁盘满）时仅保留控制台输出，不阻断应用启动
        pass


# ===== utils/logger.py 模块说明 =====
# 模块级常量：
#   LOG_DIR / LOG_FILE：日志目录与文件（H2.4：base.json log_dir 优先，
#     Windows 默认 %LOCALAPPDATA%/MrAutoDJ，其他 ~/.local/share/mrautodj）
#   _LOG_MAX_BYTES / _LOG_BACKUP_COUNT：轮转大小与保留份数（base.json 配置）
#   LOG_FORMAT / DATE_FORMAT：统一日志格式（时间 | 级别 | 模块名 | 消息）
#   _configured：模块级状态标记，保证 handler 只初始化一次（幂等）
# 函数：
#   get_logger(name)：首次调用触发 _setup_handlers()，返回 logging.getLogger(name)
#   _setup_handlers()：root logger 挂控制台 handler（stderr，errors=replace）+ 轮转
#     文件 handler（utf-8 编码，中文不乱码）；文件路径不可用时降级仅控制台
# 异常处理：stderr reconfigure 失败忽略；文件 handler 创建失败捕获 OSError 后
#   仅保留控制台输出，绝不阻断启动
# 关联配置：config/static/base.json（log_dir/log_max_bytes/log_backup_count）

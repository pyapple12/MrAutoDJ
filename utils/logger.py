# 统一日志配置模块（对齐 mrboard：控制台 + 文件双通道，文件失败降级仅控制台）

import logging
import sys
from pathlib import Path

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
    # 初始化根日志器：控制台 handler + UTF-8 文件 handler（文件失败时降级仅控制台）
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(console_handler)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        root.addHandler(file_handler)
    except OSError:
        # 文件日志不可用（权限/磁盘满）时仅保留控制台输出，不阻断应用启动
        pass


# ===== utils/logger.py 模块说明 =====
# 模块级常量：
#   LOG_DIR / LOG_FILE：日志文件路径（~/.local/share/mrautodj/mrautodj.log）
#   LOG_FORMAT / DATE_FORMAT：统一日志格式（时间 | 级别 | 模块名 | 消息）
#   _configured：模块级状态标记，保证 handler 只初始化一次（幂等）
# 函数：
#   get_logger(name)：首次调用触发 _setup_handlers()，返回 logging.getLogger(name)
#   _setup_handlers()：root logger 挂控制台 handler（stderr）+ 文件 handler
#     （utf-8 编码，中文不乱码）；文件路径不可用时降级仅控制台
# 异常处理：文件 handler 创建失败捕获 OSError 后仅保留控制台输出，绝不阻断启动
# 关联配置：无（路径固定为 ~/.local/share/mrautodj）

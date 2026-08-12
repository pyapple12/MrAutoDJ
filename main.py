# MrAutoDJ 主入口：GUI 为默认模式；版本号单一来源 base.json version 字段（对齐 mrboard）

import argparse
import sys

from config.static.static_config import get_static_config

# 静态配置解包（版本号唯一来源）
_SC = get_static_config()


def _print_version() -> None:
    # 打印版本信息（来自 base.json，代码零硬编码）
    print(f"MrAutoDJ {_SC.base.get('version', 'unknown')}")


def main() -> None:
    # 主入口：--version 打印版本；默认进入 GUI（PySide6 延迟导入）
    parser = argparse.ArgumentParser(
        prog="main.py", description="MrAutoDJ - 虚拟 DJ 台与 AI 电台"
    )
    parser.add_argument("--version", "-V", action="store_true", help="显示版本信息")
    args = parser.parse_args()

    if args.version:
        _print_version()
        sys.exit(0)

    # PySide6 属重依赖，函数内导入（AGENTS.md 例外条款）
    from PySide6.QtWidgets import QApplication

    from ui.main_window import MainWindow
    from ui.themes import apply_theme

    app = QApplication(sys.argv)
    apply_theme(app)  # G0.7：主题接线（原未调用，QSS 从未生效）
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# ===== main.py 模块说明 =====
# 模块级常量：
#   _SC：静态配置单例（版本号唯一来源 config/static/base.json version 字段）
# 函数：
#   _print_version()：打印版本（代码零硬编码，对齐 AGENTS.md 参数约定）
#   main()：argparse 入口；--version 退出；默认启动 PySide6 GUI
# 设计理由：入口收编 GUI 分发（对齐 mrboard）；PySide6 延迟导入保证
#   import main 冒烟验证在未装依赖时也可通过
# 关联配置：config/static/base.json（version）

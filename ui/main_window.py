# 主窗口模块（占位：M1 实现双盘/波形/混音台布局；PySide6 延迟导入）


class MainWindow:
    # 主窗口占位（M1 实现：PySide6 QMainWindow，双 deck + 波形 + 混音台布局）
    pass


# ===== ui/main_window.py 模块说明 =====
# 类型：
#   MainWindow：主窗口占位（M1 实现）
# 设计理由：占位阶段不顶层导入 PySide6（重依赖函数内导入，AGENTS.md 例外条款），
#   保证未装依赖时 import 冒烟验证可通过

# MrAutoDJ 主入口：WS 网关 sidecar 为默认模式（PL007 迁移收口）；版本单一来源 base.json

import argparse
import sys

from config.static.static_config import get_static_config

# 静态配置解包（版本号唯一来源）
_SC = get_static_config()


def _print_version() -> None:
    # 打印版本信息（来自 base.json，代码零硬编码）
    print(f"MrAutoDJ {_SC.base.get('version', 'unknown')}")


def main() -> None:
    # 主入口：--version 打印版本；默认起 gateway sidecar（真引擎 WS 服务）；
    # 完整桌面形态 = tauri dev（shell/ 拉起 sidecar + webui 前端）
    parser = argparse.ArgumentParser(
        prog="main.py", description="MrAutoDJ - 虚拟 DJ 台与 AI 电台"
    )
    parser.add_argument("--version", "-V", action="store_true", help="显示版本信息")
    parser.add_argument(
        "--port", type=int, default=0, help="网关监听端口，0=动态分配（默认）"
    )
    parser.add_argument(
        "--fake", action="store_true", help="注入假引擎（无音频设备演示/联调）"
    )
    parser.add_argument(
        "--gui", action="store_true", help="(已退役) 旧 PySide6 GUI 已归档 .archived/，提示迁移"
    )
    args = parser.parse_args()

    if args.version:
        _print_version()
        sys.exit(0)

    if args.gui:
        # PL007 退役提示（.archived/ui/ 保留旧栈完整副本可回溯）
        print("PySide6 GUI 已退役（V0.2.9.0 起），旧栈归档于 .archived/ui/")
        print("当前形态：python main.py（WS 网关）+ webui/（npm run dev）+ shell/（tauri dev）")
        sys.exit(1)

    # 网关为默认入口（转发 modules.gateway CLI；协议见 docs/ipc_protocol.md）
    from modules.gateway import main as gateway_main

    sys.argv = ["gateway", "--port", str(args.port)] + (["--fake"] if args.fake else [])
    gateway_main()


if __name__ == "__main__":
    main()


# ===== main.py 模块说明 =====
# 模块级常量：
#   _SC：静态配置单例（版本号唯一来源 config/static/base.json version 字段）
# 函数：
#   _print_version()：打印版本（代码零硬编码，对齐 AGENTS.md 参数约定）
#   main()：argparse 入口；--version 退出；默认起 gateway sidecar（--port/--fake
#     透传）；--gui 打印退役提示（旧栈在 .archived/ui/）
# 设计理由（PL007.2）：迁移收口后桌面形态 = Tauri 壳 spawn 网关 + Web 前端，
#   main.py 从 GUI 分发改 gateway 入口（网关是唯一 Python 进程形态）；
#   gateway 延迟导入保证 import main 冒烟轻量
# 关联配置：config/static/base.json（version）；modules/gateway.py（--port/--fake）

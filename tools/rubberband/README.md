# tools/rubberband —— 项目内置变速引擎（兜底方案）

本目录存放 Rubber Band Audio Time Stretcher 的 Windows 便携构建，
作为 MrAutoDJ 变速/Keylock 功能的**兜底引擎**。

## 使用优先级（modules/stretcher.py）

1. `RUBBERBAND_BIN` 环境变量（用户显式指定，最高优先）
2. 系统 PATH 中的 `rubberband`（推荐：用户电脑安装的版本优先）
3. 本目录 `rubberband.exe`（项目内置兜底，换电脑/未安装也可用）

## 版本与来源

- 版本：**4.0.0**（2024 官方发布）
- 来源：https://breakfastquay.com/rubberband/ → "command-line utility Windows executable"
- 文件：`rubberband.exe`（主程序）+ `sndfile.dll`（libsndfile 依赖，须与 exe 同目录）

## 授权说明（重要）

- `rubberband.exe` 为 **GPL-2.0+** 许可的第三方独立程序（全文见 `COPYING.txt`），
  由 Chris Cannam / Particular Programs Ltd 发布
- MrAutoDJ（MIT）仅以**外部独立进程**方式调用它（`subprocess` 启动），
  不将其代码链接进本项目，不修改其二进制
- 分发本项目时随附 GPL 许可文本（本目录 `COPYING.txt`）以合规
- 若需闭源分发，请从 breakfastquay.com 获取商业许可

## 更新方式

从 breakfastquay.com 下载新版 Windows 构建，替换 `rubberband.exe` 与 `sndfile.dll`，
同步更新本文件的版本号与 `README.md` 中说明。

# MrAutoDJ —— 虚拟 DJ 台与 AI 电台

[![Version](https://img.shields.io/badge/Version-ver%200.01-blue.svg)](config/static/base.json)
[![Python](https://img.shields.io/badge/Python-3.14+-green.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 项目简介

Python 桌面 DJ 应用，三步路线：

1. **虚拟 DJ 台**：双打碟机、波形显示、三频 EQ、横推混音、变速与 Keylock
2. **AI 自动 DJ**：调和混音（Camelot）、节拍对齐自动转场、Set 规划
3. **Claude 电台**：LLM 自动报幕与接歌、直播间点歌互动

GUI 基于 PySide6，音频引擎基于 python-sounddevice 实时回调，分析基于 librosa。

## 目录

- [特性](#特性)
- [快速开始](#快速开始)
- [使用说明](#使用说明)
- [项目结构](#项目结构)
- [配置参数](#配置参数)
- [依赖](#依赖)
- [参考项目](#参考项目)
- [常见问题](#常见问题)
- [许可证](#许可证)

## 特性

（开发中，里程碑见 `z.plan.md`）

- **虚拟 DJ 台（M1）**：
  - 双打碟机：播放/暂停/CUE/循环/变速
  - 波形显示：离线分析 + 实时滚动
  - 三频 EQ + 横推（Crossfader）
  - Pitch 变速 + Keylock（变调不变速）
  - 自动 BPM/调性分析（librosa，缓存复用）
  - 双输出声卡（耳机监听）
- **AI 自动 DJ（M2）**：
  - 调和混音（Camelot 轮盘）选曲
  - 节拍对齐自动转场（EQ 渐变）
  - 自动 Set 规划 / 能量曲线
- **Claude 电台（M3）**：
  - 引擎控制接口（HTTP/MCP）
  - Claude 自动选歌 / 接歌 / 报幕
  - 点歌互动（直播间消息入口）
  - TTS 语音报幕

## 快速开始

### 环境要求

- Windows 10/11
- Python 3.14 或更高版本
- ffmpeg（音频解码）、rubberband（变速渲染，可选）

### 安装

```bash
# 创建虚拟环境并安装依赖
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 使用说明

### 图形界面（默认）

```bash
.\.venv\Scripts\python.exe main.py

# 查看版本
.\.venv\Scripts\python.exe main.py --version
```

### 命令行模式

（各模块提供独立 CLI，开发中）

```bash
# 曲库分析
.\.venv\Scripts\python.exe -m modules.analyzer --folder D:\Music --json
```

## 项目结构

```
MrAutoDJ/
├── main.py                    # 主入口：GUI 分发，版本号单一来源（base.json version 字段）
├── modules/                   # 业务核心层（无 GUI 依赖，可独立测试）
│   ├── engine.py              # 音频引擎：双 deck / 混音 / EQ / 横推（实时线程）
│   ├── analyzer.py            # 曲目分析：BPM / 调性 / 能量 / 拍点（librosa）
│   ├── library.py             # 曲库：扫描 / 分析缓存（SQLite 只读）
│   ├── automix.py             # AI 自动编排：兼容性评分 / 转场计划 / Set 规划
│   └── radio.py               # 电台调度：LLM 导演 / 混合播放队列 / 点歌
├── config/
│   ├── settings.py            # 用户配置读写（AppConfig，config/user_config.json）
│   └── static/                # 静态配置（只读，json 驱动）
│       ├── static_config.py   # StaticConfig 加载器 + 缓存单例
│       ├── config.json        # 引导映射表（base.json / ui.json 分类对应）
│       ├── base.json          # 应用参数（版本/采样率/块大小/缓存路径等）
│       └── ui.json            # UI 参数（颜色/阈值/表头）
├── ui/                        # GUI 层（PySide6）
│   ├── main_window.py         # 主窗口（双盘/波形/混音台布局）
│   ├── deck_widget.py         # 打碟机控件
│   ├── waveform_widget.py     # 波形绘制
│   └── themes.py              # 主题 QSS
├── data/                      # 静态数据（预留）
├── utils/                     # 通用工具（零业务依赖）
│   ├── logger.py              # 统一日志（控制台 + 文件）
│   ├── file_utils.py          # JSON 读写（原子写）+ 缓存单例
│   ├── retry.py               # 泛型重试函数（指数退避）
│   └── convert.py             # 弹性类型转换（宽容解析）
├── .reference/                # 参考仓库与硬件资料（外部 clone，不纳入版本控制）
├── tools/rubberband/          # 内置变速引擎（GPL 便携构建，兜底方案，随仓库分发）
├── requirements.txt           # Python 依赖列表
├── LICENSE                    # MIT 许可证
└── README.md                  # 本文件
```

## 变速引擎（rubberband）

Pitch 变速与 Keylock（变调不变速）依赖 Rubber Band 变速引擎。解析优先级：

1. `RUBBERBAND_BIN` 环境变量（显式指定）
2. 系统 PATH 中的 `rubberband`（**推荐**：优先使用你电脑上安装的版本）
3. 项目内置 `tools/rubberband/rubberband.exe`（兜底：换电脑/未安装也可用）

> **授权说明**：项目内置的 `tools/rubberband/` 为 **GPL-2.0+** 许可的第三方独立程序
> （Chris Cannam / Particular Programs Ltd 发布，全文见 `tools/rubberband/COPYING.txt`）。
> MrAutoDJ（MIT）仅以外部进程方式调用它，不链接、不修改其代码；
> 若需闭源分发请从 breakfastquay.com 获取商业许可。

## 配置参数

可调参数一律外置于静态配置（代码零硬编码），按分类：

| 文件                        | 参数                                      | 说明                       |
| --------------------------- | ----------------------------------------- | -------------------------- |
| `config/static/config.json` | 引导映射表                                | `base.json`/`ui.json` 对应 |
| `config/static/base.json`   | `version`                                 | 版本号唯一来源             |
|                             | `sample_rate` / `block_size` / `channels` | 音频引擎参数               |
|                             | `analysis_sample_rate` / `analysis_hop`   | 分析路径参数               |
|                             | `cache_path` / `user_config_path`         | 缓存与用户配置路径         |
| `config/static/ui.json`     | `colors.*` / 阈值 / 表头                  | UI 外观与阈值              |

修改 json 后重启应用生效（`get_static_config()` 缓存单例，进程内只读一次）。

## 依赖

| 包名               | 说明                         |
| ------------------ | ---------------------------- |
| PySide6            | GUI 框架（Qt6）              |
| python-sounddevice | 低延迟音频输出（实时回调）   |
| numpy              | 音频数组计算                 |
| scipy              | 滤波器（Butterworth biquad） |
| librosa            | BPM/调性/能量分析            |
| soundfile          | WAV 读写                     |
| pydub              | 音频解码（基于 ffmpeg）      |

## 参考项目

`.reference/` 目录存放开源 DJ 软件的浅克隆与硬件资料，研读结论见 `w.study.md`：

- **引擎**：songs-automixer_python（TUI 自动混音台）、pyCrossfade（离线混音库）
- **AI 编排**：ai-remixmate、automix、dj-track-similarity、cuekey
- **电台**：writ-fm、claudio、radio-dj、wrzdj、mixx-dj-mcp
- **架构参照**：mixxx

## 常见问题

### Q1：没有声音 / 找不到音频设备？

A：Windows 原生运行（WSL 下 sounddevice 无设备）。检查默认输出设备；多声卡场景可用 `--list-devices` 查看设备列表并指定输出。

### Q2：变速（Pitch）功能需要什么？

A：M1 采用预渲染方案，变速渲染依赖 rubberband 引擎。解析顺序：`RUBBERBAND_BIN` 环境变量 → 系统 PATH 安装的 rubberband → 项目内置 `tools/rubberband/`（已随仓库分发，换电脑零配置）。完全未找到时变速/Keylock 降级为不可用，播放不受影响。

### Q3：分析很慢？

A：首次加载会逐曲分析（librosa），结果缓存到本地（SQLite/JSON，带版本号），后续加载秒开。分析失败的单曲以占位记录（bpm=0, key="?"）降级，不影响曲库。

### Q4：M3 的 Claude 电台需要什么？

A：需要 Anthropic API key（或兼容端点）。凭据只存本机（`~/.config/mrautodj/`），不随项目走；LLM 失败时电台自动回退为普通自动混音，绝不静默。

## 维护者

- 作者：MrAutoDJ
- 项目主页：https://github.com/

## 许可证

本项目基于 [MIT 许可证](./LICENSE) 开源。

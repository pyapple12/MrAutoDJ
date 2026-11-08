# MrAutoDJ —— 虚拟 DJ 台与 AI 电台

[![Version](https://img.shields.io/badge/Version-0.3.0-blue.svg)](config/static/base.json)
[![Python](https://img.shields.io/badge/Python-3.14+-green.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 项目简介

桌面 DJ 应用（Tauri 2 + Web 前端 + Python sidecar），两大里程碑已收官：

1. **虚拟 DJ 台**：双打碟机、波形显示、三频 EQ、横推混音、变速与 Keylock
2. **AI 自动 DJ**：调和混音（Camelot）、节拍对齐自动转场、Set 规划

原规划的第三步 Claude 电台已取消（2026-11-08 定案）。

架构（V0.2.9 起）：`shell/` Tauri 2 壳（零业务）→ `webui/` Vue3+TS 拟物前端 → WebSocket（38 条指令 + 30Hz 推流 + 二进制波形帧，协议见 `docs/ipc_protocol.md`）→ `modules/gateway.py` sidecar（音频引擎 python-sounddevice 实时回调，分析 librosa）。旧 PySide6 栈已退役归档（`.archived/ui-0.2.8/`）。

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

- **虚拟 DJ 台（M1，V0.1）**：
  - 双打碟机：播放/暂停/CUE/循环/变速
  - 波形显示：离线分析 + 实时滚动
  - 三频 EQ + 横推（Crossfader）
  - Pitch 变速 + Keylock（变调不变速）
  - 自动 BPM/调性分析（librosa，缓存复用）
  - 双输出声卡（耳机监听）
- **FLX4 交互复刻（M1.5，V0.2）**：
  - 四区布局：Browse（LOAD A/B）/ 双 Deck / Mixer / Effects
  - Hot Cue 8 槽、Beat Jump、Key Shift 半音、Slip 模式
  - Pad 打击垫（Hot Cue / Beat Loop / Beat Jump / Sampler / Key Shift 五模式 + LED 灯态）
  - Jog 转盘（外圈滚轮=弯音、顶面拖动=搓碟、Vinyl 开关）
  - Beat FX 效果库（HPF/LPF/Trans/Echo/Delay + 拍数 + 深度）
  - Mixer 补全：TRIM / VU 表 / Fader Start / Tap BPM
  - 表演功能：Censor / Stutter / Instant Doubles
  - 全局 SHIFT 组合键体系
- **UI 拟物改版（M1.6，V0.22）**：
  - QPainter 自绘拟物原语库（ui/widgets/）：RotaryKnob 旋钮 / FaderSlider 推子 / GlowButton 背光按钮 / LedStrip 灯柱 / MiniDisplay 小屏 / PanelFrame 面板
  - FLX4 五列布局：LIBRARY | DECK A | MIXER | DECK B | EFFECTS，深色金属面板 + 背光体系
  - 修复轮：Echo 回绕跳读、弯音归零、搓碟语义（平滑变速刮擦）
- **虚拟控制台完善与外观层（M1.7，V0.2.6）**：
  - 批次 0 UI 优化：布局/间距/尺寸全部配置化（ui.json）、部件大小分级、死控件灰显、数值 Tooltip、FX 状态小屏、快捷键（空格播放/Ctrl+F/Ctrl+T）
  - 批次 1 功能补齐：TEMPO 实时变速（P4 闭环）、Keylock 变速不变调（rubberband 后台重渲染）、Key Shift 真实变调、Beat Sync、循环 IN/OUT/4BEAT/减半/加倍、Beat FX 拍数接线 + AUTO/TAP/CH 通道、耳机预听（CUE A/B）
  - 批次 2 Theme 化：token 运行期动态化（ui/palette.py）、dark/light 双主题、Ctrl+T 无重启切换
  - 批次 3 贴图 A 路线：程序化拉丝金属纹理 PNG 磁盘缓存（.cache/ui_textures/，按主题/分辨率键控）
  - 批次 4 大小缩放：ui_scale 全局缩放因子（控件/间距统一乘系数）
- **AI 自动 DJ（M2，V0.2.7.0）**：
  - 兼容性评分：BPM 八度折叠 + Camelot 调和轮盘打分表 + 能量曲线 + 音色谱概要（三维归一），加权聚合可解释（explanation/warnings）
  - Set 规划：贪心链 + 能量弧线（开场→峰→回落配置化）+ 同艺人间隔约束 + 去重
  - 自动转场：复用 M1.7 转场管线（skip-stretch/下拍对齐）+ 转场 EQ 渐变（low-cut 交接）+ AUTO 自动接歌模式（Mix 完成自动装填下一曲，手动操作即退出）
  - 调和混音（Camelot 轮盘）选曲 / 节拍对齐自动转场 / 自动 Set 规划与能量曲线
- **UI 架构迁移（V0.2.8.0-V0.2.9.0，当前形态）**：
  - Tauri 2 壳（Rust 零业务）+ Vue3+TS 拟物前端（skeuo 组件库/Canvas 转盘波形/双主题）+ Python sidecar（WS 网关：38 条指令 + 30Hz 状态推流 + 二进制波形帧 + 事件帧流）
  - 数据层 Web 化：虚拟滚动曲库（扫描/分析进度实时回填）、波形峰值单源管线、Automix 推荐/AUTO/MIX 全激活
  - 工程体系：真引擎端到端签收探针、vitest 基线、PySide6 旧栈退役归档

> 原规划的 Claude 电台（M3：LLM 报幕/点歌/TTS）已取消（2026-11-08 定案），研读存档见 w.study.md B7/B9/B10/B11。

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

### 桌面形态（Tauri dev，完整体验）

```bash
# 终端 1：webui 前端
cd webui && npm install && npm run dev
# 终端 2：Tauri 壳（自动 spawn Python sidecar + 端口握手）
cd shell && npm install && npm run dev
```

### 网关单跑（Python 侧开发）

```bash
.\.venv\Scripts\python.exe main.py            # = python -m modules.gateway（动态端口）
.\.venv\Scripts\python.exe main.py --fake     # 假引擎（无音频设备联调）
.\.venv\Scripts\python.exe main.py --version

# 浏览器直连前端（不装 Tauri 也能玩）：webui dev 后打开 http://localhost:5173/?gw=<端口>
```

### 界面操作

- **曲库**：选目录扫描（分析进度实时回填）、双击装载到目标盘（500ms 内再双击 = Instant Doubles）、拖拽到指定盘、搜索过滤、兼容标记
- **双 Deck**：播放/CUE/进度、Canvas 转盘（按住拖=搓碟、滚轮=弯音、Shift+拖=搜索）、TEMPO 推子+量程循环、Keylock/Key Shift/Sync、循环键行（IN/OUT/4BEAT/减半/加倍）、表演键（SLIP/CENSOR/STUTTER）、Pad×8 五模式（Hot Cue/Beat Loop/Beat Jump/Sampler/Key Shift）、Instant Doubles
- **MIXER**：TRIM/三频 EQ 旋钮（双击回中）、VU 灯柱（峰值保持）、横推、主音量、Fader Start、Tap、CUE 监听独占切换
- **BEAT FX**：HPF/LPF/Trans/Echo/Delay、通道 1/2/1+2、拍数、深度旋钮、FX ON、AUTO/TAP、状态小屏
- **推荐/AUTO**：NEXT 推荐并预备（兼容评分+理由）、MIX 立即转场、AUTO 自动接歌、已播队列
- 双主题（Ctrl+T）、Shift 键体系、空格=目标盘播放/暂停

### 命令行模式

（各模块提供独立 CLI，开发中）

```bash
# 曲库分析
.\.venv\Scripts\python.exe -m modules.analyzer --folder D:\Music --json
```

## 项目结构

```
MrAutoDJ/
├── main.py                    # 主入口：gateway sidecar 分发（--gui=退役提示），版本单一来源
├── modules/                   # 业务核心层（无 GUI 依赖，可独立测试）
│   ├── engine.py              # 音频引擎：双 deck / 混音 / EQ / 横推 / Jog / Hot Cue / Slip / Sampler / Beat FX
│   ├── gateway.py             # WS 网关 sidecar：38 条指令路由 / 30Hz 推流 / 事件帧 / 二进制波形帧
│   ├── waveform_data.py       # 波形峰值公共算法（UI 与网关单源）+ 二进制帧打包
│   ├── analyzer.py            # 曲目分析：BPM / 调性 / 能量 / 拍点（librosa）
│   ├── library.py             # 曲库：扫描 / 分析缓存（SQLite 只读）
│   ├── audio_decode.py        # 统一音频解码（pydub + 位深归一化，engine/analyzer 共用）
│   ├── transition.py          # 转场规划（八度折叠 / skip-stretch 判定）
│   ├── stretcher.py           # 变速/变调预渲染（rubberband 封装）
│   ├── transition_manager.py  # 转场编排（prepare/mix_now/Key Shift 预渲染）
│   └── automix.py             # AI 自动编排：兼容性评分 / 转场计划 / Set 规划
├── config/
│   ├── settings.py            # 用户配置读写（AppConfig，config/user_config.json）
│   └── static/                # 静态配置（只读，json 驱动）
│       ├── static_config.py   # StaticConfig 加载器 + 缓存单例
│       ├── config.json        # 引导映射表（base.json / ui.json 分类对应）
│       ├── base.json          # 应用参数（版本/采样率/块大小/缓存路径等）
│       └── ui.json            # UI 参数（颜色/阈值/表头）
├── webui/                     # 前端（Vue3+TS+Vite，拟物 UI：skeuo/ 组件库 + Canvas 波形/转盘）
│   └── src/
│       ├── composables/       # useEngine（WS 协议/状态）/ useShift / useTheme
│       ├── components/        # DeckPanel / MixerPanel / BeatFxPanel / AutomixPanel / LibraryPanel
│       └── components/skeuo/  # 拟物组件库（MetalPanel/BacklitButton/Knob/Fader/VuMeter/MiniDisplay/JogWheel）
├── shell/                     # Tauri 2 壳（Rust 零业务：spawn sidecar + 端口握手 + 退出清理）
├── docs/
│   └── ipc_protocol.md        # WS 协议 v1.2 权威定义（38 条指令/事件帧/二进制峰值帧）
├── tools/
│   ├── gen_webui_tokens.py    # ui.json → tokens.css 设计 token 生成器（双主题单源）
│   └── rubberband/            # 内置变速引擎（GPL 便携构建，兜底方案，随仓库分发）
├── data/                      # 静态数据（预留）
├── utils/                     # 通用工具（零业务依赖）
│   ├── logger.py              # 统一日志（控制台 + 文件）
│   ├── file_utils.py          # JSON 读写（原子写）+ 缓存单例
│   ├── retry.py               # 泛型重试函数（指数退避）
│   └── convert.py             # 弹性类型转换（宽容解析）
├── .archived/                 # 退役归档（ui-0.2.8 旧栈 + PySide6 探针，gitignore 不入库）
├── .reference/                # 参考仓库与硬件资料（外部 clone，不纳入版本控制）
├── z.plan.md                  # 项目规划与里程碑（含全量代码审计报告附录）
├── w.study.md                 # 参考仓库研读报告（B1-B13 外部项目 + FLX4 学习报告）
├── x.progress.md              # 任务清单（三线 PL/FIX/PATCH + 历史字母系列）
├── y.problem.md               # 已知问题记录（P1-P5 全部修复闭环，待修复区空）
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
| `config/static/ui.json`     | `colors.*` / 阈值 / 表头                  | UI 外观与阈值（webui 由 tools/gen_webui_tokens.py 生成为 CSS tokens，双主题单源） |

修改 json 后重启应用生效（`get_static_config()` 缓存单例，进程内只读一次）。

### 版本规范

**版本双轨**（对齐系列项目规范）：机器版本唯一来源 = `config/static/base.json` 的 `version`（三段式 `X.Y.Z`，README 徽章随之即时推进）；commit 标题使用四段式 `VX.Y.Z.R`（前三段与 base.json 一致，第四段 R 为修订号，只随提交历史记录、不入配置文件）。`main.py --version` 打印 base.json 原值。

## 依赖

**Python 侧**（requirements.txt，sidecar 引擎 + 网关）：

| 包名               | 说明                         |
| ------------------ | ---------------------------- |
| python-sounddevice | 低延迟音频输出（实时回调）   |
| numpy              | 音频数组计算                 |
| scipy              | 滤波器（Butterworth biquad） |
| librosa            | BPM/调性/能量分析            |
| soundfile          | WAV 读写                     |
| pydub              | 音频解码（基于 ffmpeg）      |
| websockets         | WS 网关服务（sidecar）       |

**前端/壳**（各自 npm install）：vue3 + typescript + vite（webui）；@tauri-apps/cli + Rust tauri 2（shell）

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

## 维护者

- 作者：MrAutoDJ
- 项目主页：https://github.com/

## 许可证

本项目基于 [MIT 许可证](./LICENSE) 开源。

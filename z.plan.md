# 开源 DJ 软件调研报告

> **文件职责与编号轨道**（2026-11-05 对齐 CapsulePulse）：本文件 = 调研存档 + 项目总体规划（里程碑表）+ 方案与审计归档（附录）。既有里程碑编号（M1/M1.5/M1.6/M1.7/M2/M3）与附录编号（A001/A002/A003）**原样保留、只增不删**；自此起新立方案按 AGENTS.md 任务清单纪律走三线轨道——功能里程碑入**附录 `PL{NNN}`**、小修小改入**附录 `PATCH{NNN}`**、审计报告入**附录 `A{NNN}`**（与 x.progress.md 的 `FIX{NNN}` 恒同号），立项时创建附录、收口时在对应清单节回写一行索引。

- 调研日期：2026-08-09
- 数据来源：GitHub 搜索 API（关键词：dj / djing / dj-software / dj-mixer / xwax / open-source dj app / web dj mixer 等）
- 筛选标准：近 3 年（2023-08 之后）仍有更新（push），且为真实开源项目
- 说明：已剔除搜索结果中大量"破解版 VirtualDJ / Serato"等垃圾与盗版仓库

---

## 一、核心推荐（功能完整的开源 DJ 软件）

| 项目                                                                        | 语言       | Stars | 最后更新 | 简介                                                                                                                                         |
| --------------------------------------------------------------------------- | ---------- | ----- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| [mixxxdj/mixxx](https://github.com/mixxxdj/mixxx)                           | C++        | 7010  | 2026-08  | **业界最知名的开源 DJ 软件**，GPL-2.0，四打碟机/波形/效果器/自动混音/视频混音，支持上百款硬件控制器，Win/macOS/Linux 三平台，活跃开发        |
| [xwax/xwax](https://github.com/xwax/xwax)                                   | C          | 156   | 2026-05  | 老牌开源 DVS（数字黑胶系统），用黑胶唱盘控制数字音频，被许多系统集成                                                                         |
| [gantasmo/theDAW](https://github.com/gantasmo/theDAW)                       | TypeScript | 124   | 2026-08  | 全能型 DAW + DJ + VJ 应用，可对接 Ableton/Reaper，支持 AI 生成（Stable Audio/Magenta/Suno）、Demucs 人声分离、VST3 插件、自动混音、MIDI 映射 |
| [oguzhan-yilmaz/pyCrossfade](https://github.com/oguzhan-yilmaz/pyCrossfade) | Python     | 144   | 2026-08  | 全自动混音引擎：自动 BPM 匹配、逐小节变速、EQ 平滑过渡，适合批量生成混音                                                                     |
| [mandiclab/djc-diy](https://github.com/mandiclab/djc-diy)                   | C++        | 176   | 2026-08  | 全球首款 DIY DJ 控制器（软硬件一体），固件+配套软件开源                                                                                      |
| [yugen-apps/yugen-dj](https://github.com/yugen-apps/yugen-dj)               | C#         | 24    | 2026-06  | 简单快速的免费开源 DJ 应用，特色：支持双声卡监听                                                                                             |

### 新锐/中小型完整 DJ 软件（近 1-2 年活跃）

| 项目                                                                                        | 语言                | Stars | 最后更新 | 简介                                                                                  |
| ------------------------------------------------------------------------------------------- | ------------------- | ----- | -------- | ------------------------------------------------------------------------------------- |
| [rayocta303/UNX-DJ-ENGINE](https://github.com/rayocta303/UNX-DJ-ENGINE)                     | C                   | 19    | 2026-08  | 开源 DJ 软件/媒体播放器                                                               |
| [johncrash64/radio-dj](https://github.com/johncrash64/radio-dj)                             | Go                  | 48    | 2026-08  | 24/7 AI-DJ 电台：ffmpeg+Icecast 推流，LLM 报幕，仅 ~50MB 内存                         |
| [ElMoorish/AI-DJ-Software](https://github.com/ElMoorish/AI-DJ-Software)                     | TypeScript          | 7     | 2026-03  | Electron+React+ONNX 的 AI 桌面 DJ 应用，100% 离线：自动混音、本地子流派分类、语义搜索 |
| [naveenlabs/OTO-Decks-DJ](https://github.com/naveenlabs/OTO-Decks-DJ)                       | C++ (JUCE)          | 1     | 2026-05  | 双打碟机、三频 EQ、实时波形、转盘控制、鼓垫、主录音                                   |
| [mazer666/PhraseDJ](https://github.com/mazer666/PhraseDJ)                                   | -                   | 1     | 2026-05  | Mac 开源 DJ 软件，AI 驱动，界面简洁                                                   |
| [VELYOS-AI/velyos-deck](https://github.com/VELYOS-AI/velyos-deck)                           | JavaScript          | 0     | 2026-06  | 开源 DJ 工作站：双盘、EQ、循环、热 CUE、MIDI（DDJ-SB3）、AutoMix、人声分离            |
| [JoseAlvarezDev/AmarcordDJ](https://github.com/JoseAlvarezDev/AmarcordDJ)                   | TypeScript          | 0     | 2026-02  | Tauri+React 双盘 DJ 应用，每盘独立 FX、节拍同步视觉，三平台                           |
| [iagomartins/martins-software-i-dj](https://github.com/iagomartins/martins-software-i-dj)   | TypeScript          | 1     | 2026-04  | Electron+React+C++ 音频引擎，双盘混音、效果器、EQ                                     |
| [U-DJ200/U-DJ200](https://github.com/U-DJ200/U-DJ200)                                       | -                   | 1     | 2026-06  | macOS 免费 DJ 应用，专为 Pioneer DDJ-200 控制器：AI 人声分离、节拍同步                |
| [zalmanimrecords-stack/DJliveolator](https://github.com/zalmanimrecords-stack/DJliveolator) | C# (.NET8/Avalonia) | 0     | 2026-07  | 跨平台 DJ+VJ：双盘混音 + 节拍同步 GPU 视觉引擎，GPLv3                                 |
| [sebedard-creator/MixCanvas](https://github.com/sebedard-creator/MixCanvas)                 | Rust                | 0     | 2026-08  | 时间线式无缝节拍匹配混音，免费离线                                                    |
| [clemeno/clecta](https://github.com/clemeno/clecta)                                         | Rust                | 1     | 2026-08  | 搜索、播放、排序与混音                                                                |
| [iFoundSilentHouse/scape](https://github.com/iFoundSilentHouse/scape)                       | TypeScript          | 0     | 2026-04  | Electron DJ 应用                                                                      |
| [Eveeifyeve/DJApp](https://github.com/Eveeifyeve/DJApp)                                     | Nix                 | 1     | 2025-05  | 全原生跨平台免费开源 DJ 软件                                                          |
| [kvrnl/turnstyle](https://github.com/kvrnl/turnstyle)                                       | -                   | 0     | 2026-07  | 免费桌面 DJ 应用：双唱盘、横推、三频 EQ、变速、搓盘、节拍匹配，全离线                 |
| [morphx666/Diyokee](https://github.com/morphx666/Diyokee)                                   | HTML/JS             | 10    | 2026-08  | 支持流媒体的网页 DJ 混音应用                                                          |
| [rbenzing/DJRusty](https://github.com/rbenzing/DJRusty)                                     | TypeScript          | 0     | 2026-08  | 浏览器双盘 DJ 混音器：热 CUE、节拍同步、循环、EQ                                      |
| [EnMaNueL-G/neuralmix](https://github.com/EnMaNueL-G/neuralmix)                             | JavaScript          | 3     | 2026-06  | 100% 本地 AI DJ 混音器：最多 4 盘、人声分离、Key Lock、FX、采样器 + AI 副驾           |
| [RyanDanielWalker/faderoom](https://github.com/RyanDanielWalker/faderoom)                   | TypeScript          | 1     | 2026-05  | 浏览器内真实 DJ 混音器（Next.js + Web Audio API）                                     |

---

## 二、AI 自动混音 / 电台类（近 3 年活跃）

| 项目                                                                                      | 语言   | Stars | 最后更新 | 简介                                                                                     |
| ----------------------------------------------------------------------------------------- | ------ | ----- | -------- | ---------------------------------------------------------------------------------------- |
| [Chunduri-Aditya/ai-remixmate](https://github.com/Chunduri-Aditya/ai-remixmate)           | Python | 18    | 2026-08  | 节拍锁定、调性匹配的自动转场引擎：Demucs 人声分离、动态 EQ、LUFS 母带，FastAPI+Streamlit |
| [clawd139/automix](https://github.com/clawd139/automix)                                   | Python | 1     | 2026-02  | 开源 AI DJ 引擎：人声感知转场、智能曲目规划、节拍匹配混音                                |
| [ozzaii/vibemix](https://github.com/ozzaii/vibemix)                                       | Python | 7     | 2026-07  | 开源 AI DJ 搭档：听、看、回话                                                            |
| [VeltriaAI/dj-treta-being](https://github.com/VeltriaAI/dj-treta-being)                   | Python | 4     | 2026-07  | 自建 AI DJ：自动搜索、下载、聆听、混音、生成音乐                                         |
| [Sonic-Forage/forage-dj](https://github.com/Sonic-Forage/forage-dj)                       | Python | 1     | 2026-05  | AI 自主 DJ 界面：Stable Audio 3 文本生成音乐、Numark NS7II MIDI 映射、语音指令           |
| [Phlank/low-pressure-zone](https://github.com/Phlank/low-pressure-zone)                   | C#     | 7     | 2026-08  | 在线 DJ 电台站                                                                           |
| [stanangular/autodj-mixer](https://github.com/stanangular/autodj-mixer)                   | Python | 0     | 2026-07  | AI 混音：A1F 结构分析、Camelot 调性匹配、逐小节变速                                      |
| [LaRambla20/songs-automixer_python](https://github.com/LaRambla20/songs-automixer_python) | Python | 1     | 2026-06  | 终端 TUI 自动混音器：节拍匹配渐变、变速同步、主 FX、搓碟回旋                             |
| [Emruur/SetBuilder](https://github.com/Emruur/SetBuilder)                                 | Python | 1     | 2026-06  | 编排 DJ Set：逐曲 DSP（EQ/压缩/限幅）、响度归一化、导出混音                              |

---

## 三、DJ 曲库 / 分析 / 迁移工具（近 3 年活跃）

| 项目                                                                                                        | 语言       | Stars | 最后更新 | 简介                                                                                      |
| ----------------------------------------------------------------------------------------------------------- | ---------- | ----- | -------- | ----------------------------------------------------------------------------------------- |
| [slipmatio](https://github.com/slipmatio)                                                                   | -          | -     | 2026-08  | DJ 曲库管理器（v3 开发中）                                                                |
| [surco-app/surco](https://github.com/surco-app/surco)                                                       | TypeScript | 4     | 2026-08  | 免费开源 DJ 曲目整理：Discogs/Bandcamp 自动打标、BPM/调性检测、转码导出                   |
| [M-Igashi/baken](https://github.com/M-Igashi/baken)                                                         | Rust       | 42    | 2026-08  | Rekordbox/CDJ 准备工具：响度增益、调性+BPM 播放列表排序、CDJ 安全 MP3 转码                |
| [coderDJing/FRKB](https://github.com/coderDJing/FRKB_Rapid-Audio-Organization-Tool)                         | TypeScript | 32    | 2026-08  | 快速音频整理工具（Win/Mac）                                                               |
| [FrankwaP/mixxx-utils](https://github.com/FrankwaP/mixxx-utils)                                             | Python     | 42    | 2026-07  | Mixxx 数据库工具集                                                                        |
| [vynulldev/vynull](https://github.com/vynulldev/vynull)                                                     | Go         | 3     | 2026-07  | Linux 虚拟 CDJ：通过 Pro DJ Link 把音乐库推给 CDJ，彩色波形/节拍网格/CUE                  |
| [sparkly-quasar/openboxxx](https://github.com/sparkly-quasar/openboxxx)                                     | C++        | 1     | 2026-08  | 独立 export.pdb+ANLZ 写入器：Mixxx 曲库一键导出到 rekordbox/CDJ U 盘                      |
| [scanmydata/Dj-Library-migration-tool](https://github.com/scanmydata/Dj-Library-migration-tool)             | Python     | 0     | 2026-07  | 通用 DJ 曲库转换器：Rekordbox/Serato/Traktor/VirtualDJ 互转（CUE/循环/节拍网格/播放列表） |
| [tmahanjana/dj-sync](https://github.com/tmahanjana/dj-sync)                                                 | Python     | 0     | 2026-08  | 跨 rekordbox/Serato/Engine DJ 曲库迁移（热 CUE、循环、节拍网格、评分）                    |
| [MeteorBurn/dj-track-similarity](https://github.com/MeteorBurn/dj-track-similarity)                         | Python     | 3     | 2026-08  | 音频嵌入+AI 分类的音乐相似度引擎（DJ 选曲）                                               |
| [webmaxru/bpm-counter](https://github.com/webmaxru/bpm-counter)                                             | JavaScript | 49    | 2026-08  | 免费在线实时 BPM 计数器                                                                   |
| [Tatsh/bpmdetect](https://github.com/Tatsh/bpmdetect)                                                       | C++        | 14    | 2026-08  | 自动 BPM 检测工具                                                                         |
| [fobiat/openBPM](https://github.com/fobiat/openBPM)                                                         | C++        | 1     | 2026-08  | ESP32 黑胶 DJ 辅助：拍速计数器、节拍匹配助手                                              |
| [Supercarlillos/cuekey](https://github.com/Supercarlillos/cuekey)                                           | Python     | 2     | 2026-08  | 免费调和混音分析：调性(Camelot)/BPM/能量/CUE，支持 rekordbox 集成（macOS）                |
| [zapperment/better-traktor-stream-deck-tool](https://github.com/zapperment/better-traktor-stream-deck-tool) | JavaScript | 0     | 2025-02  | Traktor→Stream Deck 联动                                                                  |

---

## 四、周边 / 硬件控制

| 项目                                                                                                                      | 语言       | Stars | 最后更新 | 简介                                             |
| ------------------------------------------------------------------------------------------------------------------------- | ---------- | ----- | -------- | ------------------------------------------------ |
| [sandraschi/mixx-dj-mcp](https://github.com/sandraschi/mixx-dj-mcp)                                                       | Python     | 2     | 2026-07  | 用 LLM 通过 FastMCP 控制 Mixxx（40+ 工具）       |
| [mxmilkiib/deere-redo](https://github.com/mxmilkiib/deere-redo)                                                           | -          | 4     | 2026-08  | Mixxx 皮肤（紧凑 24 热 CUE）                     |
| [mxmilkiib/mixxx-novation-launchpad-pro-mk3-milkii](https://github.com/mxmilkiib/mixxx-novation-launchpad-pro-mk3-milkii) | JavaScript | 4     | 2025-10  | Mixxx 控制器脚本（Launchpad Pro MK3）            |
| [wrzonance/WrzDJ](https://github.com/wrzonance/WrzDJ)                                                                     | Python     | 9     | 2026-08  | 点歌应用：Web 仪表盘 + 访客点歌台 + 自动曲目识别 |
| [vigosan/oh-my-dj](https://github.com/vigosan/oh-my-dj)                                                                   | C++        | 0     | 2026-08  | OBS 插件：多机位轮换 + 多平台直播（DJ 直播用）   |
| [mrepol742/dj-mixer-console](https://github.com/mrepol742/dj-mixer-console)                                               | TypeScript | 0     | 2026-04  | 离线网页混音控制台（Web Audio API）              |

---

## 五、已停止维护/过期（不推荐，仅参考）

| 项目                         | 最后更新 | 说明                                 |
| ---------------------------- | -------- | ------------------------------------ |
| idjc（Internet DJ Console）  | 2022-10  | 经典开源网络电台 DJ 软件，已停止维护 |
| TheAudioProgrammer/juceDjApp | 2023-06  | JUCE 教学向 DJ 应用，已超 3 年未更新 |
| TuckerBurke/WebAudioMixer    | 2020-06  | Web 混音台，停更                     |
| WebMixer (alexus2033)        | 2024-10  | 接近 3 年边界，基本停更              |

---

## 六、结论与建议

1. **主流选择**：**Mixxx** 是唯一处于"完全开源 + 长期活跃 + 三平台 + 硬件支持完善"级别的完整 DJ 软件（7k+ stars，GPL-2.0），适合直接使用、二次开发或作为架构参考。
2. **技术栈参考**：
   - 传统桌面端：C++/Qt（Mixxx）、C++/JUCE（OTO-Decks-DJ）、.NET/Avalonia（DJliveolator）
   - 新浪潮：Electron/Tauri + React/TypeScript（AI-DJ-Software、AmarcordDJ、velyos-deck）
   - 网页端：Web Audio API（DJRusty、faderoom、Diyokee）
   - AI 混音引擎：Python（pyCrossfade、ai-remixmate、automix）
3. **生态机会**：近 3 年活跃方向集中在 **AI 混音/自动 Set 规划、曲库迁移工具（rekordbox↔Serato↔Mixxx）、DVS（xwax）、控制器脚本**——这些是 Mixxx 之外最活跃的细分赛道。
4. 若要做新产品，建议优先研究 Mixxx 的架构（Engine 与 GUI 分离、MIDI 映射体系、皮肤系统），再结合 pyCrossfade/ai-remixmate 的 AI 混音能力。

> 注：Stars 数仅反映热度；许多 0-10 star 的新项目仍在快速迭代（如 2026 年内持续更新），筛选时已按"更新日期"而非 Stars 为准。

---

## 聚焦清单（Python 优先）

### M1 引擎（核心参考）

| 项目                   | Stars | 价值                               |
| ---------------------- | ----- | ---------------------------------- |
| songs-automixer_python | 1★    | TUI DJ 台，与 M1 几乎同构          |
| pyCrossfade            | 144★  | 全自动混音引擎：渐变变速 + EQ 过渡 |

### M2 AI 自动 DJ

| 项目                | Stars | 价值                     |
| ------------------- | ----- | ------------------------ |
| ai-remixmate        | 18★   | 人声分离转场 + LUFS 母带 |
| automix             | 1★    | 人声感知转场、Set 规划   |
| dj-track-similarity | 3★    | embedding 相似度选曲     |
| cuekey              | 2★    | Camelot/BPM/能量分析     |

### M3 Claude 电台

| 项目        | Stars | 价值                               |
| ----------- | ----- | ---------------------------------- |
| writ-fm     | 379★  | Python 电台蓝图：Claude 报幕 + TTS |
| Claudio     | 46★   | 歌单 + 口播 + TTS，交互设计参考    |
| radio-dj    | 48★   | LLM 导演架构可移植                 |
| WrzDJ       | 9★    | Python 点歌台                      |
| mixx-dj-mcp | 2★    | MCP 控制 DJ（40+ 工具）            |

### 取舍

1. M1 深读 songs-automixer_python
2. M2 看 pyCrossfade 渐变 + ai-remixmate 转场
3. M3 看 radio-dj 架构 + mixx-dj-mcp 控制层

---

# MrAutoDJ 开发计划

## 项目定位

MrAutoDJ：从虚拟 DJ 台起步，逐步演进为 AI 自动 DJ 与 LLM 电台。三步共用一套架构：**引擎（Engine）← 调度（Automation）← 大脑（LLM）**。

## 技术决策（已确认）

- 语言/框架：Python + PySide6 桌面应用
- MIDI：第一步不做硬件控制器，但架构预留 MIDI 映射接口
- 电台形态：LLM 自动报幕 + 接歌（无人值守），并支持直播间点歌互动（两者都要）

## 技术栈选型（草案）

| 模块          | 方案                         | 说明                               |
| ------------- | ---------------------------- | ---------------------------------- |
| GUI           | PySide6                      | 波形绘制 / 跨线程信号槽 / 成熟稳定 |
| 音频播放      | python-sounddevice 回调      | 低延迟，双设备输出（主+监听）      |
| 解码          | ffmpeg (pydub/ffmpeg-python) | 全格式支持                         |
| 变速变调      | pyrubberband 或 soundtouch   | keylock（变调不变速）              |
| BPM/调性      | librosa / aubio              | 离线分析 + 在线 Tap                |
| 音频处理      | Pedalboard                   | EQ/滤波/效果器                     |
| TTS（第三步） | edge-tts 等                  | 电台报幕                           |

## 架构（三步共用）

1. **Engine 层**：纯音频实时线程，零 UI 依赖（deck、mixer、效果器、主输出）
2. **Controller 层**：指令总线/控制接口（第一步=UI 调用；第二步=自动调度器；第三步=LLM 工具调用/MCP/HTTP）
3. **UI 层**：PySide6 界面，只发指令、订阅状态

## 里程碑

- [x] **M1 第一步：虚拟 DJ 台**（V0.1，2026-08 完成，任务明细见 x.progress.md D0-D5）
  - [x] 曲库与分析：扫描、BPM/调性/能量/CUE 检测、SQLite 版本化缓存、进程池批处理、CLI
  - [x] 双打碟机：状态机、样本级定时切歌、循环、CUE、三频 EQ、常量功率横推、音量
  - [x] Pitch 变速（rubberband 预渲染）+ Keylock 变调不变速；双输出耳机监听
  - [x] 变速转场编排：SKIP/STRETCH 判定、epoch 防陈旧、参数失效重渲染
  - [x] 波形显示（离线峰值缓存 + 播放头滚动）、深色主题（ui.json 驱动）
  - [x] UI 集成：曲库表格/双盘控件/混音台/Prepare/Mix、跨线程信号回填
  - [x] 集成验证：无头引擎探针、端到端脚本、GUI 无头初始化、冒烟
- [x] **M1.5 FLX4 交互复刻**（V0.2，2026-08 完成，依据 w.study.md B13 报告，任务明细见 x.progress.md E 系列）
  > 定位：在 M1 基础上按 FLX4 面板一比一补全交互与功能（保留 M1 的曲库/分析/变速转场能力，叠加 FLX4 操作体系）
  - [x] **引擎支撑层**：Hot Cue 8 槽、Beatgrid 跳转与 Skip、Key Shift 半音预渲染、Jog 接口（搓碟/弯音/触摸/搜索）、VU 采集（预分配环形）、Slip 模式、Sampler 8 槽、Echo/Delay 效果库、Fader Start/Tap BPM/Censor/Stutter、TRIM 预增益、Beat FX 链
  - [x] **UI 交互层**：全局 SHIFT 组合键、Pad 打击垫（5 模式 + LED 灯态）、Jog 转盘（滚轮弯音/拖动搓碟）、Beat FX 面板、Mixer 补全（TRIM/VU/Fader Start/Tap）、Instant Doubles、LED 灯态联动、表演功能键
  - [x] **UI 四区布局重排**：Browse 顶栏（LOAD A/B + 搜索）+ 双 Deck + Mixer/Effects，保留 M1 曲库与 Prepare/Mix
  - [x] 集成验证：无头探针 probe_m15 + 端到端 verify_m15 + 冒烟
  - [x] Beat FX 修复：效果/深度/开关统一状态应用；延迟线环形缓冲回绕分段读取
- [x] 待修复问题（y.problem.md，修复轮排在 M1.6 之前）：
  - [x] P1 Echo 回绕跳读（2026-08-12 已修：删 start 判断恒从块头读；无头验证 + GUI 听测确认）
  - [x] P2 弯音不归零（2026-08-12 已修：单发 QTimer 累积归零 + 减速插值防卡顿；GUI 实测确认）
  - [x] P3 搓碟语义（2026-08-12 已修：触摸锁定 + 平滑变速刮擦 + Slip 落回；GUI 实测确认）
  - P4 Pitch 滑块无效果（M1 遗留占位）——📌 **V0.21 之后修复**，见 y.problem.md
- [x] **M1.6 UI 拟物改版**（V0.22，方案 2026-08-10 与用户讨论定稿；2026-08-12 完成，任务明细见 x.progress.md F 系列；V0.21 已被 P1-P3 修复占用故版本顺延）
  > 定位：把 M1.5 的四区布局从"标准 Qt 控件 + QSS"升级为 **QPainter 自绘拟物原语体系**（Mixxx 皮肤同路线），视觉对标 FLX4/Rekordbox 现代硬件面板；只改视觉层，引擎与交互逻辑零改动
  - [x] **方案决策**（已定稿）：
    - 路线 B：自绘控件原语库——QSS 堆质感做不出旋钮/推子，治标不治本；不做 SVG 贴图（素材重活）与 QML 重构（现有代码作废）
    - 风格：现代 DJ 台质感——深灰蓝黑金属面板 + 内凹槽 + 丝印标题 + 橙/蓝/绿/白背光（Pioneer 色系）
    - 原则：原语控件零业务依赖（不 import modules/），只做外观与交互、只发信号；业务逻辑留在现有 deck_widget/beat_fx_widget/pad_widget 组合层
    - 性能：静态层（面板纹理/刻度环/凹槽）一次渲染到 QPixmap 缓存，paintEvent 只 blit + 重绘动态部件；灯态沿用定时器低频刷新，不碰实时音频线程
  - [x] **配色体系**（token 进 ui.json）：panel_base/panel_edge/panel_inset/silk_text、glow_orange/blue/green/white、pad_color[5]（五模式色）
  - [x] **控件原语库** `ui/widgets/`（全 paintEvent 自绘）：
    - RotaryKnob 旋钮（刻度环+指针+中心帽；垂直拖拽/滚轮/双击复位）→ TRIM/EQ×3/MASTER/LEVEL/DEPTH
    - FaderSlider 推子（内凹槽+中央刻度线+拉丝金属帽）→ 通道推子×2/横推/Tempo（Tempo 带量程标签 ±6/10/16/WIDE）
    - GlowButton 背光按钮（内凹座+按压辉光+LED 灯态+模式色）→ 全按钮/LOAD/Pad/模式键
    - LedStrip LED 灯柱（分段亮起 绿→黄→红）→ VU 表替换/Beat FX 拍数指示
    - MiniDisplay 小屏（黑底+绿字 7 段数字感）→ BPM/拍数/曲名
    - PanelFrame 面板容器（渐变底+圆角+顶部高光+丝印标题）→ 四区容器
  - [x] **组合替换映射**：Mixer 区（PanelFrame + RotaryKnob×6 + FaderSlider×3 + LedStrip×2 + GlowButton）／Deck 区（PanelFrame + GlowButton + Jog 升级为金属圈+指示环+中心屏 + Pad 背光化）／Beat FX（PanelFrame + RotaryKnob + MiniDisplay + LedStrip）／Browse（PanelFrame + GlowButton）
  - [x] **布局核对机制**（与用户双向可核对，2026-08-11 更新为多模态主模型路线）：
    - 布局规格单 `docs/ui_layout.md`：ASCII 布局图 + 部件表格（位置/尺寸/间距/对齐），每次改动先更新，双方核对单一真相源，防口口相传走样
    - 无头渲染截图：`QT_QPA_PLATFORM=offscreen` + `widget.grab()` → `.temp/ui_preview/layout_vN.png`（不进 git），每轮布局改动自动出图；**主模型换为多模态后 AI 可直接读图核对**（与用户可见效果一致），仍需用户确认最终视觉
    - 用户反馈方式：ASCII 布局图／文字描述／截图标注 → 1px 级迭代
    - 布局意图来源：参照 FLX4 面板实物/官方图（用户提供参考图到 `.temp/design_ref/`，或 FLX4 官方面板图）+ B13 部件清单 + 用户口述偏好，均先转成布局规格单再实现
  - [x] **实施顺序**（每步独立可验证、可回退）：
    - Step 1：ui.json 配色 token + PanelFrame + RotaryKnob + GlowButton 三个原语
    - Step 2：替换 Mixer 区（旋钮密集区，效果立竿见影）+ 无头截图核对
    - Step 3：FaderSlider + 替换推子/Tempo
    - Step 4：Jog 转盘视觉升级 + Pad/Beat FX 背光化
    - Step 5：全量替换 + 无头初始化验证 + 截图定稿；提交（Git 拆分由用户决定）
  - [x] 集成验证：无头初始化 + 无头截图 + 冒烟；GUI 实测核对背光/灯态交互
- [x] **M1.7 虚拟控制台完善与外观层**（V0.2.6，方案 2026-08-13 定稿；任务清单 J 系列见 x.progress.md——**批次 0-4 全部完成（2026-11-05）**：UI 优化配置化 → 功能补齐（实时变速/Keylock/Key Shift 重渲染/Sync/循环键/FX 拍数/监听）→ Theme 化（dark/light 运行期切换 Ctrl+T）→ 贴图 A 路线（程序化 PNG 缓存）→ 全局缩放 ui_scale；21/21 探针 PASS + 双主题截图读图核对；目测项按用户授权闭环，提交由用户执行）
  > 定位：在 M1.6 基础上完善虚拟 DJ 控制台——先优化现有 UI（位置/大小/功能显性化），再补齐 FLX4 缺件与未实现按键行为，随后做外观层（Theme/贴图/缩放）；置于 M2 之前（虚拟台完善后再推进 AI 自动 DJ）
  - [ ] **批次 0：UI 优化（前置）**——四区布局/比例进配置、响应式重排、间距网格统一；部件位置按 FLX4 语义（TEMPO 竖置位、耳机区预留、Pad 布局核对）；部件大小分级（按钮 ≥32/旋钮分级/Jog 120-180/Pad 42）；死控件灰显、占位功能提示、操作反馈与状态显性化；Tooltip/Tab 顺序/快捷键
  - [ ] **批次 1：功能补齐**——补缺件（Beat Sync/主盘、TEMPO 推子+量程、Loop IN/OUT/4BEAT/CALL◀▶、耳机监听区、Key Shift 真实变调、Pad 剩余模式远期）；补未实现行为（Pitch 实时变速 P4、Keylock 变速不变调、Key Shift 变调、Beat FX beats 接线）；与 I 系列（A003 22 项）合并执行；全量测试
  - [ ] **批次 2：Theme 化**——token 动态化（原语控件可刷新 palette）+ 主题注册表（dark/light）+ 运行期切换入口 + 统一刷新机制；功能与 UI 数据层切割
  - [ ] **批次 3：贴图拟物化**——A 路线起步（`_skins.py` 程序化渲染 PNG 贴图），B SVG 皮肤 / C 手工设计后续
  - [ ] **批次 4：大小缩放**——ui.json 加 `ui_scale`，控件尺寸/字号/间距参数化乘系数（与 Theme 协同，贴图按分辨率生成）
  - [ ] 集成验证：无头截图 + 全量回归 + GUI 实测（FLX4 交互清单逐项）
- [x] **M2 第二步：AI 自动 DJ**（V0.2.7.0，2026-11-05 完成，方案与任务见附录 PL002 / x.progress.md PL002；人声冲突维度因依赖缺位明确不做——偏差记录于附录 PL002 决策 1）
  - [x] 兼容性评分：BPM 倍频归一化 / Camelot 档位 / 能量曲线 / 音色（人声冲突不做）
  - [x] 调和混音（Camelot 轮盘）选曲与 Set 规划（同艺人约束/去重/能量弧线）
  - [x] 节拍对齐自动转场：prepare/mix 管线接入 AI 调度（EQ 渐变 + 下拍触发）
  - [x] 自动 Set 规划：贪心编排 + 能量曲线 + 可解释评分（explanation/warnings）
- [ ] **M3 第三步：Claude 电台**
  - [ ] 引擎暴露控制接口（HTTP/MCP，portmanteau 工具模式）
  - [ ] 混合播放队列（song/tts/silence 顺序播放）
  - [ ] Claude API 工具调用（选歌/接歌/报幕，确定性回退绝不静默）
  - [ ] 点歌互动（状态机 NEW→ACCEPTED→PLAYING→PLAYED）
  - [ ] TTS 语音报幕（多引擎可插拔 + 去 emoji）

## 参考项目（来自上文调研）

Mixxx（架构参照）、pyCrossfade、ai-remixmate、radio-dj、WrzDJ（点歌台）、mixx-dj-mcp（LLM 控制 Mixxx 思路）

---

## 附录：虚拟控制台完善与外观层工作计划（2026-08-13，V2）

> 定位：M1.7（V0.25+）方案——虚拟 DJ 台完善与外观层改造，置于 M2 之前。
> 状态：📌 方案已定稿，待落盘为 M1.7 里程碑 + 拆任务清单。

### 一、目标总览（五批次）

| #   | 批次                | 目标                                           | 一句话                             |
| --- | ------------------- | ---------------------------------------------- | ---------------------------------- |
| 0   | **UI 优化（前置）** | 当前界面部件的位置/大小/功能布局全面优化       | 先让现有界面"可用可看"，再谈补东西 |
| 1   | 功能补齐            | 补缺的部件与按钮 → 补未实现按键行为 → 全量测试 | 对齐 FLX4 面板                     |
| 2   | Theme 化            | 功能与 UI 切割，运行期多主题切换               | 外观数据源动态化                   |
| 3   | 贴图拟物化          | 矢量绘制升级为贴图皮肤                         | 更接近硬件质感                     |
| 4   | 大小缩放            | 界面整体缩放（窗口/DPI）                       | 适配不同屏幕                       |

### 二、批次 0：UI 优化（功能补齐的前置）

> 定位：不动功能与引擎，只改现有部件的位置、大小、布局、可用性——为后续补部件/补行为打好界面地基。

#### 0a. 布局优化

| 项          | 现状                                               | 目标                                                      |
| ----------- | -------------------------------------------------- | --------------------------------------------------------- |
| 四区比例    | QSplitter 硬编码（0.24/0.76、0.24/0.22/0.24/0.19） | 比例进 ui.json；按内容自适应（Mixer 按控件数、Deck 均分） |
| 响应式      | 窗口 resize 后控件固定不变、空间浪费/挤压          | 布局随窗口缩放合理重排（splitter 比例 + 部件可伸缩性）    |
| 间距/边距   | 各处 6/8/10 不一致                                 | 统一间距网格（如 4/8/12 三级）进配置                      |
| Browse 顶栏 | 按钮松散                                           | 分组布局（LOAD 组/搜索组/状态组），对齐 FLX4 Browse 条    |

#### 0b. 部件位置优化（按 FLX4 面板语义）

| 现状                             | 问题                                     | 目标                                                          |
| -------------------------------- | ---------------------------------------- | ------------------------------------------------------------- |
| TEMPO/Pitch 在 Deck 底部横向滑块 | 位置不醒目、语义弱（Pitch 无效更显突兀） | 预留 TEMPO 推子竖置位（对齐 FLX4 右侧），Pitch 保留作量程指示 |
| Beat FX 面板在 EFFECTS 列        | 拍数/AUTO/TAP/CH 死控件占位              | 隐藏或标注死控件（见 0d），为真实部件腾位                     |
| 耳机区缺失                       | 无 CUE 键/监听平衡位置                   | 预留 Mixer 下方耳机控制位（批次 1 补部件）                    |
| Pad 与模式键                     | 相对位置/间距未严格对齐 FLX4             | 按 B13-3.12 布局核对                                          |

#### 0c. 部件大小优化

| 项           | 现状             | 目标                             |
| ------------ | ---------------- | -------------------------------- |
| 按钮最小尺寸 | GlowButton 28×24 | 可点性提升（≥32 高），文字不裁切 |
| 旋钮直径     | 28 固定          | 按区域分级（Mixer 32、FX 28）    |
| Jog 尺寸     | 140 固定         | 可伸缩区间 120-180               |
| Pad 键       | 35×35 固定       | 42×42 左右，间距统一             |
| 一致性       | 同类控件大小不一 | 同语义控件同尺寸                 |

#### 0d. 功能层面的 UI 优化（"假功能"显性化）

| 项                                     | 处理                                     |
| -------------------------------------- | ---------------------------------------- |
| beat_fx 死控件（AUTO/TAP/CH1/CH2/1+2） | 标注"预留"灰显，或批次 1 补功能后启用    |
| Pitch/Keylock 占位（P4）               | 状态栏明确提示"未实现"，按钮灰显避免误导 |
| 操作反馈                               | 补旋钮/推子数值显示（如 EQ 增益 dB）     |
| 状态显示                               | 目标盘、当前效果、FX ON 状态显性化       |

#### 0e. 可用性细节

Tooltip（关键控件 hover 说明）、Tab 顺序合理、键盘快捷键补全（空格=播放等，对齐 B13）、窗口标题/状态栏信息完善。

#### 可行性

纯 UI 层改动，无引擎风险，工作量中等偏小；可独立验证（截图对比 + GUI 实测）。**注意**：尺寸先按固定分级做，缩放因子留给批次 4 统一参数化（避免返工）。

### 三、批次 1：功能补齐

#### 1a. 缺的部件/按钮（B13 差距）

Beat Sync/主盘、TEMPO 推子+量程（±6/10/16/WIDE）、Loop IN/OUT/4BEAT 独立键 + CUE/LOOP CALL◀▶（减半/加倍）、耳机监听区（CUE/平衡/音量）、Key Shift 真实变调接入、Pad 剩余 3 模式（KEYBOARD/PAD FX1/PAD FX2，远期）、Beat FX 死控件启用（AUTO/TAP/CH）、Censor 曲头行为（A003 I0.3）。

#### 1b. 未实现的按键行为

Pitch 实时变速（P4）、Keylock 变速不变调、Key Shift 实时变调、Beat FX beats 拍数接线。弯音/搓碟已实现（V0.21 修复）无需动。

#### 1c. 测试

全量回归（现有 13 probe + 新专项探针）+ GUI 逐项实测（FLX4 交互清单）。

#### 可行性

引擎实时变速/变调是硬骨头（实时 vs 预渲染两条路线需定边界）；建议与 I 系列（A003 22 项，含 Pitch/死控件）合并执行。

### 四、批次 2：Theme 化

#### 现状

配色 token 已进 ui.json（V0.22-V0.23）✓、QSS 已 token 化（H2.3）✓；**缺陷**：原语控件模块加载时固化 token（改配置需重启），`apply_theme` 仅 dark，无切换入口。

#### 要做什么

1. token 动态化：原语控件持可刷新 palette 引用（全局主题通知 → 控件 refresh_palette() 重绘）——"功能与 UI 切割"在数据层落地
2. 主题注册表：themes.py 扩展多主题（dark/light），每主题一份 token 集
3. 切换入口：运行时切换（菜单/快捷键），切换后全控件刷新（无重启）

#### 可行性

中等。Qt 无内置主题机制，需自建"token provider + 刷新通知"（信号或全局对象）；13 个自绘控件需把类级常量改实例持有 + 统一刷新入口（防漏刷新花屏）。工作量中。

### 五、批次 3：贴图拟物化

#### 现状

全部 QPainter 矢量绘制（金属渐变/辉光/刻度环），已有 `_skins.py` 公共绘制层。

#### 三路线（可行性递增）

| 路线                      | 做法                                                                       | 拟物度 | 工作量             |
| ------------------------- | -------------------------------------------------------------------------- | ------ | ------------------ |
| A. 程序化贴图（推荐起步） | 把 `_skins.py` 绘制离线渲染成 PNG，运行时 QPixmap 加载——复用现有代码零素材 | ★★☆    | 小                 |
| B. SVG 皮肤               | 控件支持 SVG 素材（QSvgRenderer），皮肤目录化可主题化                      | ★★★    | 中（素材重活）     |
| C. 手工设计贴图           | 外部设计（PS/Figma 导出）                                                  | ★★★★   | 大（依赖设计资源） |

#### 可行性

高（A 路线）。静态层 QPixmap 缓存已有基础，贴图化天然契合。建议 A 起步（与批次 2 主题、批次 4 缩放协同），B/C 后续。

### 六、批次 4：大小缩放

#### 现状

窗口 resize(1280, 800)；原语控件 setFixedSize 固定（Jog 140、Pad 35、旋钮 28）；QSplitter 布局。

#### 方案对比

| 方案                    | 做法                                                | 优点                            | 缺点                   |
| ----------------------- | --------------------------------------------------- | ------------------------------- | ---------------------- |
| A. Qt 高 DPI            | Qt6 默认 per-screen DPI                             | 零成本                          | 自绘控件不缩放只缩文字 |
| B. 全局缩放因子（推荐） | ui.json 加 ui_scale；控件尺寸/字号/间距参数化乘系数 | 完整缩放、可配、与主题/贴图协同 | 需改全部原语控件       |
| C. QGraphicsView 缩放   | 场景层变换                                          | 整体变换                        | 重构布局体系，过重     |

#### 可行性

B 中等（原语控件"固定尺寸"改"scale×基准"）；与批次 2（主题）、批次 3（贴图按分辨率生成）天然协同。建议缩放作为"外观层基础设施"与主题一起做，贴图在其上做。

### 七、建议执行顺序与依赖

```
批次 0：UI 优化（位置/大小/功能显性化）——独立先行，快速见效
批次 1：功能补齐（I 系列 + 补部件 → 补行为 → 全量测试）
批次 2：外观层基础（Theme + 缩放参数化）——批次 0 的间距/尺寸在此统一乘因子
批次 3：贴图拟物（A 起步，基于主题与缩放）
```

### 八、风险提示

1. 引擎实时变速/变调（Pitch/Keylock/Key Shift）是技术硬骨头——弯音插值可扩展，但"持续变速+变调"与转场预渲染管线需协调（实时 vs 预渲染边界）
2. 批次 0 的"尺寸分级"与批次 4"缩放因子"重叠——批次 0 只定基准尺寸，缩放留给批次 4
3. Theme 切换花屏/漏刷新——统一刷新机制设计期定死
4. 缩放参数化影响面广（13 个原语控件全改），回归风险（probe_p5 覆盖交互不覆盖尺寸）
5. 贴图 B/C 路线依赖设计资源，工作量不可控——以 A 路线为验收基线
6. 批次 0 布局重排可能影响 probe_p6 布局断言（四列结构不变则无碍）

---

## 附录：布局核对方案演进记录（2026-08-11 更新：多模态主模型路线替代 Figma MCP）

> 演进历程：
>
> 1. 2026-08-10 初稿：Figma MCP 接入方案（下述原文保留备查）——当时主模型 deepseek-v4-flash 无视觉能力，MCP 的结构化数据（JSON 坐标/颜色）是无视觉下精确核对的唯一路径
> 2. 2026-08-11 决策：**用户选择更换多模态主模型（方案 A）**，AI 可直接读图——Figma MCP 降级为备选；布局意图来源改为"FLX4 面板参考图（`.temp/design_ref/`）+ B13 部件清单 + 用户描述"；无头截图由 AI 直接读图核对，与用户可见效果一致
> 3. 2026-08-11 实测补充：**默认模型（deepseek-v4-flash）实测仍无法读图**（read 工具报错 Cannot read）；多模态能力需用户手动切换模型（如 Qwen3.8 max）获得——约定见 AGENTS.md"多模态模型约定"；后续所有读图类任务（F4.3 参考图分析、F5.7/F6.6 截图核对）启动前须通知用户切换模型
> 4. 若日后用户使用 Figma，可恢复 MCP 路线（下述配置原文），两条路线可并存（MCP 拿精确数值、读图看整体效果）

---

### （原文备查）Figma MCP 接入方案（2026-08-10 定稿）

> 目的：让 AI 直接读取 Figma 设计稿的精确布局数据（布局树/绝对坐标/像素尺寸/样式），替代"截图猜位置"，实现 1px 级布局核对

### 1. 解决的问题

- 截图核对只能"看大概效果"，拿不到精确坐标/尺寸/层级
- 布局规格单（docs/ui_layout.md）若手工誊写易走样，直接从设计稿抽取则零误差
- 视觉 token（颜色/字距）直接从设计稿提取，对齐 ui.json 配色体系

### 2. 配置（写入 `.opencode/opencode.json` 的 mcp 段）

```json
{
  "mcp": {
    "figma": {
      "type": "local",
      "command": ["npx", "-y", "figma-developer-mcp", "--stdio"],
      "environment": { "FIGMA_API_KEY": "..." }
    }
  }
}
```

- 需要：Figma API token（个人访问令牌，Figma 账号设置 → Security → Personal access tokens）
- 注意：配置修改后需重启 opencode 生效；token 属凭据，不得写入 git（.opencode/ 已在 .gitignore 中）
- 备选：figma-developer-mcp 支持 `--scope=personal` 或 `--scope=team`，如组织受限用 team scope + 添加文件 key

### 3. 工作流（设计 → 代码 → 核对闭环）

```
用户在 Figma 画布局稿 → 分享给 AI（file key）
  → AI 通过 MCP 读取：文件列表/帧层级/节点绝对坐标与尺寸/fill 颜色/文本内容（全部为文本数据，无需视觉）
  → 生成布局规格单 docs/ui_layout.md（部件表格：位置/尺寸/间距/对齐/配色）
  → 按规格单实现 Qt 原语与布局（M1.6）
  → 无头渲染截图 .temp/ui_preview/ → 对照设计稿 → 偏差反馈 → 迭代
```

### 4. 具体核对项（MCP 可提供的精确数据）

| 数据                                | MCP 接口                      | 用途                    |
| ----------------------------------- | ----------------------------- | ----------------------- |
| 文件与页面列表                      | `get_file` / `get_file_nodes` | 定位设计稿              |
| 节点布局树（frame/组/实例）         | `get_file_nodes`（节点递归）  | 翻译成 Qt 布局层级      |
| 绝对坐标 + 尺寸（x/y/width/height） | 节点 `absoluteBoundingBox`    | 布局规格单的精确数值    |
| 填充色/描边/效果                    | 节点 `fills/strokes/effects`  | 生成 ui.json 配色 token |
| 文本内容/字体                       | 节点 `characters/style`       | 丝印标题/标签文案       |
| 渲染图                              | `get_image`                   | 对照预览（含导出参数）  |

### 5. 落地条件与前置

- [ ] 用户提供 Figma API token（或确认使用 figma-developer-mcp 的 OAuth 方式）
- [ ] 用户创建/导入 FLX4 布局设计稿（或自定义布局稿），分享文件权限给 token 所属账号
- [ ] 在 M1.6 Step 1（配色 + 原语）之前完成配置，使 Step 2（Mixer 区替换）直接按设计稿坐标实现
- 备注：非 Figma 设计工具（Sketch/XD/PS）无成熟 MCP，届时退回"导出 PNG + 读图核对"方式

---

## 附录 A001：全量代码审计报告（第一轮，2026-08-12）

> 范围：全部 25 个 .py + 3 个 JSON；三路并行只读审计（utils/config、modules、ui），信号接线全量核对无类型失配
> 状态：✅ **P0-P3 已全部修复**（2026-08-12 G 系列完成，见 x.progress.md；probe_g0-g3 + 全量回归 9/9 PASS + GUI 实测确认）

### 一、重复造轮子（14 处，审计重点）

1. 解码归一化重复：engine.load_audio vs analyzer._decode_mono（数值不一致，应抽 utils 共用）
2. utils.convert 弹性转换零使用（analyzer 导入未调用）
3. utils.retry / config.settings 整模块无调用
4. 金属渐变绘制三处重复（jog_wheel/fader_slider/rotary_knob → 抽 _skins.py）
5. 滚轮步进"全程/20"两处；6. 拍长计算两处（→ _beat_len）；7. 候选打分循环两处；8. Key Shift 钳制两处
6. 回调内插值结构重复（弯音 vs scratch）；10. scan_folder 同名重复风险（library 占位）
7. set_channel_fader 复制 deck.stop 逻辑；12. 表头硬编码 vs ui.json table_headers 不一致
8. clear_cache 死代码 + read_json 对不存在文件写缓存

### 二、严重问题（功能/正确性/稳定性）

1. themes 未接线（QSS 从未生效）；2. analyzer engine_sr=44100 硬编码（采样率变更索引错位）
2. start_mix fade 除零；4. 正向搜索形状错误；5. stretcher 无 rubberband 前置检查
3. CuePlayer 二次失败外抛；7. rotary 指针 QRectF 误用绘制错位
4. panel set_title 无标题崩溃；9. pad 灯态 isChecked 残留冲突
5. main_window 直写 deck._position（绕过锁）；11. deck_widget 44100 显示硬编码

### 三、硬编码 / 防御性 / 死代码 / 规范违反（摘要）

- **硬编码**：modules 参数群（增益/EQ/槽位/钳制/转场/分析参数）未走 base.json；ui 配色 20+ 处与 ui.json 重复；定时器 100ms/splitter 比例/16777248/0.5s/5000ms 等；配置承诺未兑现（led 阈值键不存在、SEARCH_WHEEL_STEP 未进配置、table_headers 死配置）
- **防御性缺口**：convert 不拦 nan/inf；waveform 无 1D 防护；fader/rotary min==max 除零；长文本溢出；static_config 无校验；EQ/FX setter 无锁；浮点精确比较
- **死代码**：vu_meter 整模块、shift_state 死方法、_TRAVEL、QMessageBox 导入、_last_out_pos、_next_bpm/_next_downbeats、convert 两函数、retry/settings 整模块、clear_cache
- **规范违反**：函数内延迟导入 8+ 处；Optional[] 6+ 处；说明区失实 5 处；参考标注 5 处

### 四、亮点

回调 fail-soft 静音降级到位；预分配缓冲设计正确；进程池 spawn + numba 隔离；信号接线无类型失配；占位模块 M2/M3 边界清晰

### 五、建议优先级

| 优先级    | 事项                                                                                |
| --------- | ----------------------------------------------------------------------------------- |
| P0 正确性 | 采样率硬编码 / 搜索形状 / fade 除零 / 指针绘制 / pad 灯态 / set_title / themes 接线 |
| P1 去重   | 解码统一（数值不一致）/ 金属渐变抽 _skins.py / 拍长·钳制·步进公共化 / 表头配置化    |
| P2 配置化 | modules 参数群 + ui 配色进 config，兑现 led 阈值/搜索步进/表头承诺                  |
| P3 清理   | 死代码归档或接线 / 说明区同步 / Optional→\|None / 延迟导入上移 / 参考标注移除       |

---

## 附录 A002：全量代码审计报告（第二轮，2026-08-12）

> 范围：全部 33 个 .py + 3 个 JSON（三路并行：utils/config、modules、ui），与第一轮逐项比对区分"遗留/新增"
> 方式：只读审计，未修改任何代码；audit-project skill 执行
> 状态：✅ **P0-P3 已全部修复**（2026-08-13 H 系列完成，见 x.progress.md；probe_h0-h3 + 全量回归 13/13 PASS + GUI 实测确认；待提交 V0.24）

### 一、高（正确性/崩溃/数据竞争）

| 文件:行号                              | 问题                                                                        | 性质              |
| -------------------------------------- | --------------------------------------------------------------------------- | ----------------- |
| analyzer.py:437                        | hop = 512 与配置 ANALYSIS_HOP 重复定义——配置变更时 CUE 检测静默脱钩         | 新增确认          |
| engine.py:197-234                      | DeckEQ setter 无锁，_b/_a 非成对替换，回调可能读到系数中间态                | 上轮标注未修      |
| waveform_widget.py:23                  | _build_peaks 无 1D 防护（IndexError），set_audio 在 try 外调用 → 加载链崩溃 | 上轮标注未修      |
| main_window.py:537                     | other_deck._position = ... 直写私有字段且无锁（与回调线程竞争）             | 上轮标注未修      |
| rotary_knob.py:74 / fader_slider.py:67 | min==max 除零（RotaryKnob(0,0) 构造即崩）                                   | 新增确认          |
| static_config.py:24-31                 | mapping 非 dict/键缺失/data 非 dict 校验缺失                                | 上轮 P1 标注未修  |
| deck_widget.py:100-101                 | 44100 显示换算硬编码——G0.1 采样率配置化后 UI 显示层脱钩                     | 新增（G0.1 遗漏） |

### 二、中（纪律/一致性/配置化未闭环）

1. def 内 import / def 内 def：transition_manager.py:125 _work 嵌套 + :142 函数内 import（G3.5 遗漏）；engine.py:1123、analyzer.py:490/553/664 函数内 import（新增 2 + 遗留 2）；main_window.py:441 函数内 import（顶层 L28 死导入并存）；rotary_knob.py:114,127 import math×2
2. stretcher：rubberband_available() 零调用；渲染入口无前置检查；双渲染函数样板重复
3. engine：L13 死 import；Censor 分支缺 _mix_sample；L1147 float 精确比较；set_pregain 2.0 字面量；0.01 阈值×6；Trans/Echo/Delay/HPF 曲线硬编码
4. main_window：deck._bpm or 120.0 私有直读（与 _on_beatloop 的 _deck_meta 路径不一致）；_beat_fx._onoff.isChecked() 跨控件私有访问；fade_seconds=16.0 字面量；16777248 魔法数字；range(8) 未引用 SLOT_COUNT
5. 重复实现：拍数阶梯 [1,2,4,8,16,32] 双处定义；path→entry 查找×2；_KEY_SHIFT_MAX 双处读键
6. themes.py QSS 硬编码 6 色 + 说明区"颜色零硬编码"矛盾
7. logger.py：路径硬编码（Windows 非标准）、无轮转、控制台 handler 无 errors 兜底（特殊字符致日志崩溃）
8. convert.py：to_float 零调用；不拦截 nan/inf

### 三、低（规范/风格）

- import 顺序违规 3 处；_detect_cues 类型注解错误（list[int] 实返 list[dict]）
- glow_button _GLOW_WHITE 死变量：辉光文字纯白 vs glow_white(#e8ecf0) 不一致
- _skins.py 后仍散落重复（jog_wheel metal_pen / rotary_knob top_highlight_pen）
- 长文本溢出无 elide（glow_button/mini_display）；pad_colors 空列表除零；beat_fx 尺寸 44<48 冲突；Key Shift 灯阵 idx0/idx7 双灯同亮（需确认语义）
- 说明区偏差 3 处（beat_fx 关联配置/ main_window jog_bend_reset_ms / deck_widget 44100 注释）
- 死代码：settings.CONFIG_DIR、ui.json quota_warn_percent 死键、engine L13

### 四、修复优先级建议

| 优先级    | 内容                                                                                                                                            |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| P0 正确性 | analyzer hop 脱钩 / DeckEQ 无锁 / waveform 1D 防护 / main_window 无锁写 _position / min==max 除零 / deck_widget 44100 显示 / static_config 校验 |
| P1 去重   | 拍数阶梯单源 / path→entry 提取 / _KEY_SHIFT_MAX 单源 / stretcher 渲染样板 / engine 死 import / 双 BPM 路径统一                                  |
| P2 配置化 | analyzer 能量权重+CUE 参数 / engine 0.01×6+FX 曲线 / themes QSS token 化 / logger 路径+轮转 / convert nan/inf+接线                              |
| P3 清理   | def 内 import 全清（5 文件）/ def 内 def 提升 / glow_white 修正 / skins 收敛 / 死代码 / 说明区同步 / import 顺序                                |

> 亮点：G0-G3 修复全部生效；配置键 45 个与代码读取完全一致；transition.py 无问题

---

## 附录 A003：全量代码审计报告（第三轮，2026-08-13）

> 范围：全部 .py + JSON（三路并行：utils/config、modules、ui），V2.1 规则（13 类维度 + 回归复核）
> 方式：audit-project skill V2.1 执行；只读未改代码
> 状态：✅ **P0-P3 已全部修复**（2026-11-05 I 系列完成，见 x.progress.md；probe_i0-i3 新增 + 全量回归 17/17 PASS + 冒烟 OK。补录 2 项：I0.5 空 cue 切片 timemap 防御——本报告 P2 表"transition_manager.py:208"系笔误，实际位置 stretcher.py:208；I2.6 convert nan/inf 拦截。参考级观察项 24 项按回落理由保留不动。GUI 实测与提交待用户）
> 二轮复核：H0.1 漏改（analyzer.py:464 hop NameError 回归）已在 I0.1 修复

### 零、上轮修复复核清单（A002/H 系列）

| 结果         | 项                                                                                              |
| ------------ | ----------------------------------------------------------------------------------------------- |
| ✅ 在位      | H0.2-H0.7、H1.1-H1.4、H2.1-H2.4、H3.x（主会话 19 项 grep + ui 组复核）                          |
| ❌ 回归 1 处 | H0.1 漏改：analyzer.py:464 hop_length=hop 引用已删局部变量 → NameError（git diff 确认只改两处） |

### 一、P0-P3 修复清单

#### P1（必修，可复现崩溃）

| 文件:行号       | 类型   | 描述                                                                             | 建议                    | 性质              | 影响面       |
| --------------- | ------ | -------------------------------------------------------------------------------- | ----------------------- | ----------------- | ------------ |
| analyzer.py:464 | 正确性 | hop NameError：CLI 批量分析（默认 with_cues=True）100% 崩溃，BPM/Key/Energy 全丢 | hop_length=ANALYSIS_HOP | 回归（H0.1 引入） | 分析管线/CLI |

#### P2（应修）

| 文件:行号                               | 类型   | 描述                                                                      | 性质 |
| --------------------------------------- | ------ | ------------------------------------------------------------------------- | ---- |
| engine.py:807-813                       | 正确性 | _fill_resample step==0 → IndexError 静音卡死（                            | rate | <0.000244，API 级） | 遗留 |
| engine.py:774-780                       | 正确性 | Censor 越过曲头后反向被永久清除（行为与注释不符）                         | 遗留 |
| stretcher.py:183                        | 防御   | rubberband 缺失 → 晦涩 TypeError；                                        |
| ubberband_available() 零调用            | 遗留   |
| transition_manager.py:208               | 防御   | 空 cue 切片 → timemap[-1] IndexError                                      | 遗留 |
| led_strip.py:17-18 / mini_display.py:16 | 配置化 | warning/danger/accent 在 colors 内，顶层读取恒回落默认——改配置不生效      | 新增 |
| beat_fx_widget.py:29-34                 | 死代码 | channel/beats/bpm_auto/bpm_tap 四信号只发不接，AUTO/TAP/CH 用户可见死控件 | 新增 |
| main_window.py:746                      | 正确性 | MIXING 不计入"播放中"：Mix 后 16s 播放键文案/灯态失实且点击行为错位       | 新增 |

#### P3/P4（摘要）

- 配置防御：settings.py:13 直接索引（全库唯一非 .get）；:39 主题白名单双处漂移；CUE_PARAMS/ECHO_PRESET 缺键 KeyError；convert to_float 不拦 nan/inf（遗留）
- H 残留：analyzer.py:681 函数内 import tempfile；tm numpy 死 import；main_window 双 BPM 路径/_beat_fx._onoff 私有访问（A002 遗留）
- 注释/文档失实 10+ 处（等功率换算、H0.2 原子性注释过强、deck_widget 关联配置、README 结构树缺 audio_decode、四区/五列标题过时）
- 性能：glow_button set_led 无去重（180 次/秒无效重绘）；set_fx 重建 Biquad 丢 zi 咔嗒
- 细节：mini_display elide 字体度量不一致（H3.5 引入）；pad 硬编码 8 未随 SLOT_COUNT；分析 worker 关窗 emit/换文件夹混库；waveform _SC.ui 残留；pad_light 死代码

### 二、参考级观察项（24 项回落，摘要）

外观几何/有注释依据的算法参数/不可达防御/预留参数等，含回落理由。代表性：Biquad 纯 Python 循环（块预算内）、分析 STFT 32MB 瞬时、_build_peaks float64 拷贝、keyRelease 焦点丢失 SHIFT 滞留、Instant Doubles 误触窗口、vu_meter pyc 残留、LedStrip 顶段 -2px。

### 三、亮点

H 系列 19 项修复在位（除 H0.1 漏改）；配置键 40 个与读取方对齐无死键；文档一致性全过（README 徽章==base.json==git V0.24、x.progress 编号连续、y.problem 状态真实）；锁语义/import 循环无风险；transition.py 无问题。

---

## 附录 PL001：UI 评审修复（截断与列宽 / 面板补丁 / 激活态层级）

> 立项：2026-11-05。来源 = taste-skill（app-screens 模式）UI 评审报告（评审素材 `.temp/ui_preview/review/`，before 截图已存档）；评审结论 overall 6.0（design 5.5 / usability 5.5 / creativity 7.5 / content 7），Top3 问题：①文字大面积截断+曲库列塌缩 ②QSS 全局背景在拟物面板上打黑/白补丁+无内容色块+VU 空态不可见 ③激活态层级失衡（FX ON 白光抢主操作/效果键选中色不一致/Pitch 原生滑块）。
> 定位：纯 UI 层修复（themes/widgets/main_window/deck_widget/beat_fx_widget/pad_widget），引擎与业务逻辑零改动；评审"硬件拟物"设计意图保留（金属/辉光/渐变不属违规项），只修可用性硬伤与一致性。
> 状态：✅ **已实施**（2026-11-05，任务组 PL001 见 x.progress.md——16/16 条勾结；probe_pl001 全 PASS + 22/22 探针回归 + 冒烟 OK；after 截图 dark/light×3 特写目检全过（截断清零/色块消失/VU 框架可见/Jog 无叠字/FX ON 描边激活/空态引导）；执行中升级两处根因——GlowButton 无 sizeHint 覆写（截断源头）与五列最小宽超主区（Pad 全宽化 + mins+shares 机制解决）；遗留 PanelFrame 标题重叠记 y.problem#P5。已随 V0.2.6.1 提交推送 98ae909）

---

## 附录 PL002：M2 AI 自动 DJ（兼容性评分 / Camelot 选曲 / Set 规划 / 自动转场）

> 立项：2026-11-05（对应里程碑表 M2 四条：兼容性评分 / 调和混音选曲与 Set 规划 / 节拍对齐自动转场 / 自动 Set 规划）。
> 定位：`modules/automix.py` 从占位转正为 M2 核心——**确定性编排算法**（贪心 + 打分表，非 LLM；LLM 报幕属 M3 radio.py）；纯逻辑零 GUI 依赖（分层红线），UI 只做接入。
> 代码基础盘点（2026-11-05 实读）：`analyzer.Key` 已有 Camelot/wheel 记谱、`transition.fold_ratio/tempo_compatible/plan_transition` 已有八度折叠与 skip-stretch 判定、`TransitionManager.prepare/mix_now` 已有 downbeat 对齐与 epoch、`main_window._library` 已有 [{path, bpm, key, energy, record}] 曲库结构；缺口 = 打分表/贪心规划/音色维度/艺人元数据/自动循环。
> 状态：✅ **已实施**（2026-11-05，任务组 PL002 见 x.progress.md——15/15 条勾结；probe_pl002_score/set/bridge 全 PASS + 25/25 全量回归 + 冒烟 + Effects 推荐区截图读图；执行中修正两处设计落地细节——key_score 需双记谱解析（Camelot "8A"/标准 "A minor"）、贪心同分 max 稳定取首防 dict 比较 TypeError；人声冲突维度按决策 1 不做已记录。live 听感验收与提交 V0.2.7.0 由用户执行）

### 一、设计决策（含取舍）

1. **评分五维 → M2 实现四维 + 人声冲突明确不做**：BPM / Key(Camelot) / Energy / Timbre 四维有数据基础（timbre 需新增分析字段，PL002.4）；**人声冲突不做**——需 Demucs/人声分离依赖（重、GPL 生态风险、分析耗时翻倍），且 M1 分析器无此字段；记入里程碑偏差，待 M3 或独立 PL 再议（诚实原则：不虚构能力）。
2. **Camelot 打分表**（DJ 惯例，常量进 automix.py）：
   - 同键 1.0 / 同号异字母（关系大小调）0.85 / 同字母相邻号（能量步进 ±1）0.9 / 对角相邻（异字母 ±1 号）0.6 / 其余 0.2；任一 key 缺失（"?"）→ 0.5 中性
3. **BPM 分**：复用 `transition.fold_ratio` 八度折叠——r_eff==1 → 1.0；half/double-time → 0.75；否则 `max(0, 1 - |r_eff-1|/(tolerance*2))`（tolerance 用 TEMPO_MATCH_TOLERANCE）；bpm≤0 → 0.4
4. **Energy/Timbre 分**：能量差 `exp(-(Δe/2)²)`（σ=2 拍级）；timbre 为谱概要（0-1 归一三维）欧氏距离高斯衰减（σ 进配置）；缺失一律 0.5 中性
5. **总分配置**：`base.json automix_weights = {"bpm": 0.3, "key": 0.3, "energy": 0.2, "timbre": 0.2}`——`compatibility_score(a, b) -> {overall, scores{四维}, warnings[]}`
6. **音色字段**：`analyzer._detect_timbre`（谱质心/谱带宽/谱滚降 85% 的全程均值，各自 min-max 归一到 0-1）→ `record["timbre"] = [c, b, r]`；**ANALYSIS_VERSION 1→2**（旧缓存自动失效重分析，已有机制）
7. **艺人元数据**：无 ID3 解析依赖（避免 mutagen 新依赖）——文件名约定宽容解析 `"Artist - Title.ext"`（首个 " - " 分割；无分隔符 → artist=None，同艺人约束对该曲自动跳过）
8. **Set 规划**：贪心链（非全局最优，可解释够用——KISS）：每步从候选取 `compatibility_score × 能量弧线贴合度` 最高者；能量弧线 = 目标曲线 `[开场 0.5 → 峰 1.0 → 回落 0.6]` 按曲数归一（形状配置 `base.json automix_energy_arc`）；约束 = 已播去重 + 同艺人间隔 ≥ `automix_same_artist_gap`（默认 3 首）；每步输出 `explanation`（如 "Key 8A→8B 关系调 + BPM 倍频 + 能量 +1"）与 `warnings`（"候选不足跳过艺人约束"）
9. **自动转场**：复用 `TransitionManager.prepare/mix_now` 全部机制（downbeat 对齐/epoch/skip-stretch），automix 只负责"选曲与推荐"；新增**转场 EQ 渐变**——mix 启动后由 TransitionManager 渐变线程分步调 `now_deck.eq.set_low`（-1 → 0，8 步斜坡，非回调线程——回调零 IO 纪律不破），经典 low-cut 交接手法
10. **自动模式**：UI 开关 + mix 完成自动 prepare 下一曲的循环（AutomixController 持有队列指针）；停止条件 = 无候选 / 用户关闭 / 手动暂停（手动 Load/Prepare 时自动模式退出，防双源打架）

### 二、措施（五组，文件/函数级）

#### 组 A 评分核心（automix.py 纯逻辑，TDD 先行）

- **A1 Camelot 打分**——`automix.py` 新增 `key_score(key_a: str, key_b: str) -> float`：复用 `analyzer.parse_key` 解析（异常 → 0.5 中性）；按决策 2 打分表实现（Camelot 号/字母经 `Key.camelot` 性质换算，不重复造轮）
- **A2 维度分与聚合**——`automix.py` 新增 `bpm_score/energy_score/timbre_score`（模块级常量读 `base.json automix_weights/automix_timbre_sigma`）+ 重写占位 `compatibility_score(track_a: dict, track_b: dict) -> dict`（四维聚合 + warnings：维度缺失清单）
- **A3 探针**——`.temp/probe_pl002_score.py`：合成用例表（同键 1.0/关系调 0.85/倍速 0.75/未知中性 0.5/权重和=1 等 ~15 断言；**先 FAIL（占位恒 0.5）后 PASS**）

#### 组 B 分析扩展与曲库接入

- **B1 音色概要**——`analyzer.py` 新增 `_detect_timbre(y, sr) -> list[float]`（`librosa.feature.spectral_centroid/bandwidth/rolloff(roll_percent=0.85)` 全程均值，按固定参考范围 min-max 归一：质心 [200,6000]Hz、带宽 [200,4000]Hz、滚降 [1000,10000]Hz）+ `analyze_file` 组装 `record["timbre"]` + `ANALYSIS_VERSION = 2`；验证：probe 断言合成正弦/白噪 timbre 向量区分度 + 缓存版本失效重分析
- **B2 艺人解析与曲库条目**——`library.py` 占位转正：新增 `parse_artist(path) -> str | None`（Path.stem 按首个 " - " 分割取左段，空/过长(>40 字) → None）与 `build_entries(paths: list[str], records: dict) -> list[dict]`（输出 `{path, name, artist, bpm, key, energy, timbre, record}`——**main_window._library 迁移到此结构**：`_append_row` 改用 build_entries 单条构造，曲库表刷新逻辑不变）；验证：probe 文件名用例（标准/无分隔/超长）
- **B3 UI 曲库迁移**——`main_window.py`：`_library` 条目构造改调 `library.build_entries` 单条版本（`library.entry_from(path, record)`），`_entry_by_path`/`_append_row`/兼容标记逻辑保持；验证：冒烟 + probe_g1（表头/兼容标记断言）不回归

#### 组 C Set 规划（automix.py 纯逻辑）

- **C1 弧线与贪心链**——`automix.py` 新增 `plan_set(entries: list[dict], start: dict | None, length: int) -> dict`：输出 `{sequence: [entry...], explanations: [str], warnings: [str], arc: [float]}`；能量弧线目标 `automix_energy_arc = [0.5, 0.8, 1.0, 1.0, 0.7]`（按 length 归一插值）；每步评分 = `overall × exp(-|e_now - arc_i|/0.3)` 取最高；约束：已播去重、同艺人间隔（`automix_same_artist_gap=3`，候选不足时降级并在 warnings 声明）；`explanation` 由四维 scores 组装（只列贡献前二的维度）
- **C2 探针**——`.temp/probe_pl002_set.py`：合成曲库（8 曲可控 BPM/Key/energy/artist）断言：序列长度/去重/同艺人间隔/弧线贴合顺序/explanation 非空（先 FAIL 后 PASS）

#### 组 D 自动转场调度与 UI 接入

- **D1 推荐桥**——`automix.py` 新增 `class AutomixController`：`__init__(tm: TransitionManager, entries_getter)`、`recommend(now_meta: dict) -> dict | None`（返回 `{entry, explanation}`；无候选/无 BPM → None）、`auto_mode: bool` 开关、`on_mix_started()`（自动模式：记录已播 + 立即推荐并 prepare 下一曲——经 `tm.prepare`，cue_seconds=下一曲首 downbeat 或 0）
- **D2 转场 EQ 渐变**——`transition_manager.py mix_now()`：SKIP/STRETCH 启动后起守护线程（daemon），8 步 × fade/10 间隔调 `now_deck.eq.set_low(-1 → 0)`（末步恢复 0；被 mark_stale/新 mix 抢占时线程检测 epoch/代次退出）；**回调线程零改动**（纪律不破）；验证：probe 断言渐变序列首末值与线程退出
- **D3 自动循环**——`main_window.py`：`_on_mix` 成功后若 `self._automix.auto_mode` 调 `on_mix_started()` 链式 prepare；手动 Prepare/Load 时置 `auto_mode=False` 并状态栏提示（防双源）；`closeEvent` 停控制器
- **D4 UI 推荐区**——`main_window._build_effects_panel()`：Prepare/Mix 按钮上方加推荐行（MiniDisplay 显示推荐曲名 + QLabel 显示 explanation 摘要 + `Auto Next` GlowButton（单次推荐并装填）+ `AUTO` GlowButton（勾选 = 自动模式，蓝色 LED））；接线 `_on_recommend/_toggle_automix`
- **D5 探针**——`.temp/probe_pl002_bridge.py`：假引擎 + 假 tm 断言 recommend 选择/自动链 prepare 调用序列/手动操作退出自动模式/EQ 渐变首末值

#### 组 E 检验与收尾

- **E1 全量回归**——probe_pl002_score/set/bridge 全 PASS + 既有 22 探针 + 冒烟（analyzer 缓存 V2 首次重分析耗时段落明）+ 截图（Effects 推荐区）
- **E2 文档与提交**——README 特性（M2 段落）、z.plan 里程碑 M2 勾选与本附录状态回写、x.progress 勾选、提交（四段式 V0.2.7.0，用户执行）

### 三、验证方案（总）

1. **纯逻辑 TDD**：评分表/贪心链/艺人解析全为纯函数（合成用例，零音频依赖）——先 FAIL 后 PASS
2. **分析管线**：`_detect_timbre` 用合成信号断言（440Hz 正弦 vs 白噪的谱质心显著分离）；V2 缓存失效重分析
3. **桥接**：假引擎/假 tm 断言调用序列（不真渲染 rubberband）
4. **回归**：全量探针（重点 g1/i2 缓存相关断言——ANALYSIS_VERSION 变更后 `probe` 中写缓存的用例自愈，观察即可）+ 截图读图
5. **live（用户）**：真曲库跑 Auto Next 单步 + AUTO 模式一小段 Set，听感验收

### 四、不做的事（边界）

- 人声冲突维度（决策 1）与 LLM 参与（M3）；不引入 mutagen/Demucs 新依赖；不做全局最优 Set（贪心够用）；不改 M1.7 已有转场机制（对齐/epoch/skip-stretch 全复用）；UI 不做 Set 时间线可视化（远期）

---

## 附录 PATCH001：UI 小修与对拍可视化（面板标题占位 / 曲库列宽 / 波形下拍网格）

> 立项：2026-11-06（用户：M2 听感验收通过、小问题修复、继续优化）。三件小修：① P5 面板标题重叠（y.problem#P5 转实施）② 曲库表"调性/能量"列被裁（PL001 评审遗留——库列 320px 放不下 5 列默认宽）③ 波形下拍网格（对拍可视化，M2 后续项——M2 闭环后解锁）。
> 状态：✅ **已实施**（2026-11-06，PATCH001 4/4 勾结；probe_patch001 PASS（并抓出 waveform paintEvent 变量顺序 NameError 真 GUI 崩溃）+ 25/25 回归 + 截图读图；已知权衡：密集包络段下拍网格被波形淹没（alpha 40 包络主导），安静段可见。提交 V0.2.7.2 由用户执行）

### 措施（文件/函数级）

1. **P5 面板标题占位**——`ui/widgets/panel_frame.py`：新增模块常量 `CONTENT_TOP_MARGIN = 26`（标题行 6..24 + 2px 空隙）；`ui/main_window.py` 五处面板内容布局顶边距 8/`_SP_MD` → `CONTENT_TOP_MARGIN`（browse/lib/deck/mixer/effects——`setContentsMargins` 第二参）；PanelFrame 标题 QLabel 保持（占位后无重叠）
2. **曲库列宽**——`ui/main_window.py _build_ui()`：表格建列后设固定宽（状态 40 / BPM 60 / 调性 64 / 能量 48），曲名列走既有 stretchLastSection 弹性吸收剩余——五列在 280px 最小库列下全部可见；验证：probe 断言四列宽之和 ≤ 库面板内容宽
3. **波形下拍网格**——`ui/waveform_widget.py`：新增 `set_grid(downbeats: list[int])`（样本位置列表，转 x 时按 `_duration` 比例映射）；`paintEvent` 在波形包络**之前**绘制淡网格竖线（accent 色 alpha 40——下拍 1px 线，包络主导视觉）；`ui/main_window.py _load_track_to/Instant Doubles` 传入 `entry["record"].get("downbeats")`；验证：probe 断言网格存储/映射在宽内/双击换曲更新

### 验证

- `.temp/probe_patch001.py`：标题占位（面板子控件 y ≥ CONTENT_TOP_MARGIN）/ 列宽和 ≤ 内容宽 / 网格存储与映射断言 + 双主题 grab 不崩；全量回归 + 截图


### 一、目标

1. **可读性**：1650×800 默认窗宽下全部按钮文本完整可读，曲库列保持 ≥260px 不塌缩
2. **面板一致性**：拟物纹理面板无黑/白补丁色块；VU 未亮段在暗面板上可见（空态保留框架）
3. **激活态纪律**：主操作唯一（Mix Now 唯一橙色实心）；效果键选中恒橙光；Pitch 滑块归入拟物体系
4. **空态引导**：空曲库有一句引导（empty keeps frame + 一句话，app-screens §11 first run 规则）

### 二、措施（四组，文件/函数级）

#### 组 A：截断与列宽（对应评审 Top3-1）

- **A1 splitter 列宽下限与比例重申**——`ui/main_window.py _build_ui()`：四处面板 `setMinimumWidth`（曲库 260 / deck 420 / mixer 230 / effects 250）；`show()` 后比例被子控件 sizeHint 重算覆盖是曲库塌缩根因，补 `QTimer.singleShot(0, self._apply_splitter_sizes)`（新方法，集中 body/main 两级 `setSizes` 调用，构造与 show 后各执行一次）
- **A2 GlowButton 文本自适应**——`ui/widgets/glow_button.py paintEvent()`：elide 前先按 `QFontMetrics.horizontalAdvance(text)` 与可用宽（rect.width()-6）比较，超宽则字号降一档（painter 字体 pointSize -1，最低到 8）再 elide——文本优先可读，tooltip 已有全名兜底
- **A3 BeatFxWidget 两行布局**——`ui/beat_fx_widget.py __init__()`：row1 拆为 `fx_row`（FX 标签+效果 5 键）与 `ch_row`（CH1/CH2/1+2 独立一行）；`AUTO` 按钮文本不再被挤（row2 的 AUTO/TAP 保持右置）
- **A4 Pad 模式键短名**——`ui/pad_widget.py`：`PAD_MODES` 拆为业务值与显示文本两层（`PAD_MODES` 信号值不变，新增 `PAD_MODE_LABELS = {"Beat Loop": "LOOP", "Beat Jump": "JUMP", "Key Shift": "KEY", ...}`），模式键构造用 LABELS，`_select_mode`/`_apply_mode_color` 按 PAD_MODES 逻辑不变
- **A5 Mixer/PHONES 按钮短名**——`ui/main_window.py _build_mixer_panel()`：FaderStart 键文本 `{label} FS`、Tap 键 `TAP`（label 前缀 A/B 保留）；PHONES 两键 `CUE A`→`CA`、`CUE B`→`CB`（tooltip 全名已存在不改）

#### 组 B：拟物面板补丁与状态诚实（对应评审 Top3-2）

- **B1 QSS 背景作用域改造**——`ui/themes.py _build_qss()`：删除 `QMainWindow, QWidget { background: {bg}; ... }` 全局实底规则，改为全局 `QWidget { background: transparent; color: {fg}; }` + 定点实底（`QTableWidget`/`QLineEdit`/`QStatusBar`/`QMainWindow` 保留 bg）；QLabel/QContainer 随全局透明——PanelFrame 拉丝纹理在全部标签后透出，黑/白补丁消失。回归点：QTableWidget/QLineEdit 实底必须在（浅色主题下表格可读）
- **B2 Mixer 残留色块定位与清除**——B1 落地后重截 zoom_mixer：若 EQ 标签下 90×70 / 横推旁 120×200 色块仍残留，写 `.temp/probe_block.py` 给可疑容器 setStyleSheet 临时描边逐个排除（候选：row2 列 QVBoxLayout 拉伸的 QLabel、xf_col 的横推标签被 row4 stretch 拉高）；定位后修复（横推标签改 `xf_col.addWidget(QLabel, 0, Qt.AlignHCenter)` + 固定行高， QLabel 拉伸属 QSS 透明后自愈项）
- **B3 LedStrip 未亮段可见**——`ui/widgets/led_strip.py _segment_color()`：未亮分支从 `panel_inset` 改 `panel_edge` 并在段顶加 1px 6% 白描边（paintEvent 段矩形上缘 drawLine）——暗面板上灯柱框架可见（"空态保留框架"）
- **B4 Jog 中心屏重叠修复**——`ui/jog_wheel.py __init__()/paintEvent()`：Vinyl checkbox 从覆盖式布局改独立行——圆盘绘制区域下移（paintEvent 圆心 y += checkbox 高/2，半径同步收缩）或 checkbox 移到 Jog 底部（圆上方留 18px 头部行）；消除 "✓ Vinyl" 压 "---- BPM" 的叠字

#### 组 C：激活态层级（对应评审 Top3-3）

- **C1 效果键初始橙光**——`ui/beat_fx_widget.py __init__()` 末尾：构造 `setChecked(True)` 后补调 `self._select_fx("HPF")`（统一走现有选中路径，初始即橙光，与点击后一致）
- **C2 激活辉光分档**——`ui/widgets/glow_button.py paintEvent()`：`isChecked()`（非按压）态辉光半径 ×0.85、外圈 alpha 220→150（按压/LED 常亮态维持现强度）；`ui/beat_fx_widget.py` 的 FX ON 改"描边激活"——新参数或 set_led 语义扩展：checked 时画 1.5px led 色圆角描边 + 文字亮色，不整面辉光——主操作唯一性还给 Mix Now（橙色实心）
- **C3 Pitch 滑块拟物化**——`ui/deck_widget.py __init__()/set_pitch_display()`：`QSlider` → 复用 `ui/widgets/fader_slider.py` 的 `FaderSlider(-8, 8, 0, Qt.Horizontal, length=200)`；`set_pitch_display` 改 `set_value` + blockSignals（防 pitch_changed 回环）；`_on_pitch_changed` 保留（手动拖动仍发信号，main_window `_on_pitch` 提示语义不变）；QSS 的 QSlider 规则随之可删（themes.py 清理）

#### 组 D：空态与 light 微调

- **D1 空曲库引导**——`ui/main_window.py _build_ui()`：曲库 PanelFrame 内表格上加一句 QLabel（`Qt.AlignCenter`，silk 色 12px）"打开文件夹加载曲库 · 双击曲目加载到目标盘"，`load_library()` 有行后 `setVisible(False)`；"empty keeps frame + 一句话"（app-screens §11）
- **D2 light 辉光降档**——`ui/widgets/glow_button.py paintEvent()`：辉光 alpha 系数按 `palette.current()` 分档（dark 220 / light 150，中心 110/70）——浅底光晕不发脏；读 palette 而非硬编码（palette 已有 current() 接口）

### 三、验证方案

1. **探针** `.temp/probe_pl001.py`（TDD：先 FAIL 后 PASS）：
   - 截断断言：对 LOAD A/B、FX 5 键、CH 3 键、模式 5 键、FaderStart/Tap、PHONES 2 键逐个断言 `btn.fontMetrics().horizontalAdvance(text) <= btn.width()-6`（文本完整放下，无省略号）——修复前 FAIL
   - 列宽断言：1650×800 show 后 `library_panel.width() >= 260`
   - 一致性断言：效果键初始 `_led_color == QColor(glow_orange)`；QSS 无 `QWidget { background: {bg}` 全局规则；LedStrip 未亮段色 == panel_edge；deck_widget Pitch 是 FaderSlider 实例
   - 渲染断言：dark/light 双主题全窗 grab 不崩
2. **截图对比**：重跑 `.temp/review_shots.py` 输出 after 组（dark 空载/加载、light 加载、三特写），与 before（同目录现存）逐项目检——截断清零、无色块、VU 框架可见、Jog 中心屏无叠字、FX ON 描边态
3. **全量回归**：既有 21 探针全 PASS（重点 p5/p6 布局与交互断言、j0 尺寸断言——A2-A5 改按钮文本/宽度可能触碰 p6 文本断言，同步更新）+ 冒烟 import
4. **验收**：GUI 实测（用户）——可读性/层级/空态引导逐项复核

### 四、范围与不做的事

- 不动引擎/modules 层；不改配色 token 值本身（light/dark token 表不动，只改透明度分档）；不改交互逻辑与信号（A4 显示文本与业务值分离）；Splitter 响应式重排、Tooltip 体系等 M1.7 批次 0 已做项不重做
- 评审报告中"波形无拍标线（BPM grid）"等属 M2 对拍功能范畴，不入本 PATCH（记录到 y.problem 备忘，未来 [problems#N]）


---

## 附录 A004：全量代码审计报告（第四轮，2026-11-06）

> 范围：modules/ ui/ utils/ config/ main.py + 静态 JSON（三路并行只读：modules 核心组 / ui 组 / config+utils 组，逐文件全文阅读）；主审计面 = A003 之后的三个功能提交 **98ae909（M1.7）/ 736029c（M2）/ ebd16b5（PATCH001）**；Mimosa 独立深扫 0 发现（seal 892f…，静态面与人工审计互补）。
> 方式：audit-project skill（MR 2026-11-05 版）执行；只读未改代码。
> 状态：✅ **已修复**（2026-11-06，FIX004 26/26 勾结，见 x.progress.md；probe_fix004 33 断言 + 26/26 探针回归 + 冒烟 + 截图读图。P1 两族（Mix 完成一致性/解码位深）+ P2 全部 12 项 + P3 批清（含两项规范裁决落定：A5 缓存库口径改消费侧只读、M5 缺失 energy 中性拟合）。ANALYSIS_VERSION→3 旧缓存自动失效。提交 V0.2.7.3 由用户执行）

### 零、上轮修复复核清单

| 结果 | 项 |
| --- | --- |
| ✅ 在位 | I 系列 20 项全部在位（三路代理 `git show 19ef44d` 逐文件比对 + probe_i0-i3 行为断言双重确认）；H 系列抽查、PATCH001 三件在位；98ae909 新代码正确继承修复模式（factor 分支钳制 / HPF/LPF 未回退重建 Biquad） |
| 结论 | 三组一致无漏改无回归；但发现 2 处**方案落地缺口**（PL001.11 辉光降档死开关 → 一节 #8；PL002.11 AUTO 链真实引擎失效 → 一节 #1）——属新代码集成缺陷而非修复丢失 |

### 一、P0-P3 修复清单（合并去重：P1×2 / P2×12 / P3×~20）

#### P1（必修——确定性错值/数据破坏）

| # | 文件:行号 | 描述 | 建议 | 性质 | 影响面 |
| --- | --- | --- | --- | --- | --- |
| 1 | **Mix 完成状态一致性族**（engine.py:1114-1119 + main_window.py:1014-1023/820-825 + automix.py:305-314） | ① `_fill_mixing` 换缓冲不重置烘焙域/循环/scratch——Keylock 下来曲按旧曲速度播、rebias 以旧 `_orig_audio` 渲染把上一曲换回、旧循环套新曲；② `_deck_meta` Mix 后从不更新→第二次转场起 BPM/downbeats/推荐基准全错位；③ AUTO 链在 mix_now 置 MIXING 之后才 prepare→PLAYING 守卫恒拒且静默——AUTO 真实引擎下永不自动装填（probe FakeTM 无守卫=勾验盲区）；④ Instant Doubles meta 缺 energy/timbre | mix 完成钩子统一：play() 同款重置 + `_make_deck_meta(entry)` 三入口共用 + 链式 prepare 等回 PLAYING + 失败上状态栏；补真实守卫探针 | 新增（M1.7/M2） | 转场编排/主窗口/跨模块 |
| 2 | utils/audio_decode.py:16-21 | 8/24-bit WAV 归一化失真 256 倍（pydub 源码核实：24-bit 数值 ±2^23 却除 2^31；8-bit 偏置后仍除 32768）→ native wav 播放/VU/波形/能量分析近静音级失真，静默 | 按位深正确归一（24→2^23、8 补分支）+ 合成三档 wav 探针 + 修注释 | 遗留（G1.1 起） | 解码管线全链路 |

#### P2（应修）

| # | 文件:行号 | 描述 | 性质 |
| --- | --- | --- | --- |
| 3 | analyzer.py:555 | downbeat 帧换算 `beat_times / ANALYSIS_HOP` 缺采样率因子（应 ×sr/hop）→ 相位探测自 V0.1 从未生效（恒 phase 0，每曲白算全曲 STFT） | 遗留 |
| 4 | engine.py:1098-1119 | MIXING 段无变速因子：Keylock 关+TEMPO≠1 时混音瞬间速度跳变、弯音/搜索失效 | 新增 |
| 5 | engine.py:448-458/1352-1361 | stop()/fader 停止不清 `_orig_audio` 不取消 `_rebias_timer`→去抖窗后复活已停盘；整曲内存双份滞留 | 新增 |
| 6 | engine.py:633-649 | `_swap_buffer` 漏映射 `_pending_mix_at`→定时切歌错位或静默丢失 | 新增 |
| 7 | transition_manager.py:32 + base.json | `eq_ramp_steps` 读取方在、配置键从未登记（"该进配置未进"） | 新增 |
| 8 | ui/glow_button.py:29/42-45 | checked 辉光降档死开关——`set_checked_tier` 生产零调用，PL001.11 勾验与实际行为不符（探针自证盲区） | 新增 |
| 9 | ui/led_strip.py:74 | 垂直灯柱方向/色带整体镜像（顶部绿底部红、低电平顶部先亮，与 docstring/VU 惯例相反）；水平分支正确 | 遗留（M1.6 起） |
| 10 | ui/widgets/_textures.py:46-66 | 纹理缓存无上限 + paintEvent 路径同步写 PNG（splitter 拖动逐像素 miss→卡顿+千级文件） | 新增 |
| 11 | ui/main_window.py:1006-1012 | `_on_prepared_done` 无 `_closing` 防护（渲染窗关窗后 emit 已删对象，I3.6 同型漏改） | 新增 |
| 12 | main_window.py:61-62/349/448 + beat_fx:87 | s() 双重缩放（调用点已 s() 构造内再 s()）——ui_scale≠1 时指数偏差 | 新增 |
| 13 | panel_frame.py:33-41 + main_window:216-219 | 主题切换后丝印标题/空库引导句内联样式不刷新（浅底残留深色） | 新增 |
| 14 | main_window.py:872/933 + deck_widget:157 | Pitch 反显 ±8 钳制 vs TEMPO 量程 ±16/WIDE——指示饱和失真 | 新增 |

#### P3（摘要，~20 项）

E5 FX_TRANS_LADDER 死常量+注释失实｜E6 play() 不重置 _key_shift（Pad 灯失真）｜E7 tap() 不联动 FX 延迟｜E8 Echo/Delay 默认值三处重复+1.9 钳制分叉｜E9 engine 说明区缺漏｜E10 close() 不关 CuePlayer｜A2 analyzer 说明区两处失实｜A3 _detect_timbre 不传 hop_length｜A4 numba 临时目录堆积｜**A5 缓存库可写 vs AGENTS"只读连接"口径冲突（规范裁决→FIX004.19）**｜M3 GAP=1 切片边界（`sequence[-0:]` 全序列）｜M4 缓存数值不走宽容转换（两处）｜**M5 弧线对缺失 energy 惩罚与"缺失中性"声明不符（裁决→FIX004.19）**｜T2 mix_now 曲终竞态返回 True 无混音｜T3 守卫死条件+pending 重入未声明｜T4 _now_downbeats 锁外读｜T5 渐变间隔 fade/16 与设计 fade/10 不符｜S1 sample_rate 默认 44100 三处｜S2 _safe_progress 吞错未登记｜R1 transition.py 说明区失实｜ui：Sampler 死路径（sample_load 零入口）/弯音钳双源/函数内 import ×2/beat_fx Qt 死导入+注释停在"预留未接线"/主题白名单三处漂移（palette 硬编码第三处）/贴图缓存键无配色版本/ui.json quota_warn_percent 死键/settings 写异常说明失实/scipy 死依赖

### 二、参考级观察项（~30 项，代表性）

打分表/σ/弧线 0.3 为 PL002 设计定值；plan_set 预留零调用；set_tempo_rate 保护性钳制；Biquad 硬编码 2ch（项目契约）；回调内 numpy 分配（说明区已声明）；_maybe_rebias 锁外原子读（理论，需验证）；Censor 不遵守 loop（黑胶语义）；mix_now 不恢复原 EQ（设计选择）；**静音 timbre 可能 NaN 进缓存（需验证）**；README 徽章==base.json ✓；base.json 其余 50+ 键全对齐 ✓；ThemeBus 无泄漏 ✓；waveform set_grid 越界处理正确 ✓；兼容标记不随切盘刷新；峰值缓存不随 resize；SHIFT 焦点滞留（A003 已登记）；AGENTS.md GUI 无头验证命令误写 PyQt6（应 PySide6）

### 三、亮点

I 系列 20 项修复零回归；探针体系暴露一处方法论盲区并已转化为修复项（**FakeTM 假件绕过真实 State 守卫→PL002 勾验假阳性**，FIX004.3/.5 补真实守卫探针）；M2 纯逻辑层（评分/规划/解析）质量良好，问题集中在跨模块时序契约（mix 完成/prepare 守卫/线程回调）——恰是假件探针覆盖不到的接缝；配置键 50+ 核对仅 1 缺 1 死。

---

## 附录 A005：全量代码审计报告（第五轮，2026-11-06）

> 范围：modules/ ui/ utils/ config/ main.py + AGENTS/requirements（三路并行只读）；审计对象 = **A004 修复批次（FIX004，工作区未提交改动，HEAD ebd16b5 之后）**。
> 方式：audit-project skill 执行；只读未改代码。
> 状态：✅ **已修复**（2026-11-06，FIX005 18/18 勾结，见 x.progress.md；probe_fix005 全 PASS + 27/27 探针回归 + 冒烟 + 截图。P1×3 + P2×7 + P3 批全部落地；两项 A004 记录勘误落定。提交 V0.2.7.4 由用户执行）

### 零、上轮修复复核清单

| 结果 | 项 |
| --- | --- |
| ✅ 在位 | FIX004 修复主体 12/12（diff 逐块防漏改）：mix 完成重置、_swap_buffer pending 映射、stop/_cancel_rebias、MIXING 因子（_mix_source_chunk）、tap 联动、configure 钳容量、FX_TRANS_LADDER 删、audio_decode 位深分母表（pydub 源码+五档实测复核）、downbeat ×sr/hop（V3）、automix GAP 短路/缺失中性/timbre 定长/to_float、eq_ramp_steps、键增删全仓零残留 |
| ❌ **FIX004 勾验不实 4 处** | ① FIX004.3 引入 `_tick` AUTO 消费段 **NameError**（P1-1，探针假件盲区再现）② FIX004.23"analyzer 两处说明区"未落地 ③"engine 说明区补全"未落地 ④ 头部"P3 批全部落地"不实（A004 P3 有 8 项未立条目未改）；FIX004.26"probe_fix004a/b/c/d"与实际单文件不符 |

### 一、P0-P3 修复清单（P1×3 / P2×7 / P3×~20）

#### P1（必修）

| # | 文件:行号 | 描述 | 建议 | 性质 | 影响面 |
| --- | --- | --- | --- | --- | --- |
| 1 | ui/main_window.py:1361 | `_tick` AUTO 消费段引用 `now_deck`——该名仅存在于其他三个方法局部，`_tick` 内未定义 → AUTO 开启时每次 mix 完成**确定性 NameError**，链式装填永不执行、当次 tick 刷新中断（非 AUTO 不触发；被标记已清故不重复抛） | 改循环变量 `deck`；**补 `_tick` 级真引擎 AUTO 探针**（QTimer 驱动——直调消费块的探针抓不到接线错，A004"探针盲区在接缝"教训重现） | 新增（FIX004.3 引入） | 主窗口/AUTO 链 |
| 2 | automix.py:312-321 + main_window.py:1354-1361 | `on_mix_started(incoming)` 形参收而不用，内部仍读 `_now_meta_getter()`——UI 已先滚 meta 为来曲 → `_played` 记入**来曲**而非播完曲（播完曲永不进防重复名单，A→B→A 回环可能）。修 P1-1 后立即确定性复现 | `on_mix_started` 改用 `incoming["path"]` 记已播（形参已备） | 新增（FIX004.3 引入，跨 ui+modules） | AUTO 防重复 |
| 3 | requirements.txt | **缺 `audioop-lts`**：py3.13+ 移除标准库 audioop；pydub 0.25.1 回退 `import pyaudioop` 为 py2 绝对导入（py3 必然失败）→ 按 AGENTS 流程重建 venv 后 `import pydub` 硬崩、解码全链路死；**冒烟门禁盲区**（pydub 延迟导入，import 全过测不出） | 加 `audioop-lts>=0.2.0; python_version >= "3.13"`；冒烟增真实解码调用（合成 wav → decode_audio） | 新增（环境可复现性；本机 venv 已手工装不受影响） | 解码全链路 |

#### P2（应修）

| # | 文件:行号 | 描述 | 性质 |
| --- | --- | --- | --- |
| 4 | _textures.py:50-51 + panel_frame.py:83 | 量化**向下取整**且绘制不拉伸——面板宽高非 32 倍数（几乎恒真）右/下缘露透明空带（FIX004.14 注释"按需拉伸"无实现） | 新增（FIX004.14 引入回归） |
| 5 | main_window.py:903-905 | 量程切换调 set_pitch_range 后**不回写 Pitch 反显**——乐速非零点量程键：帽跳中位、标签滞留旧值 | 新增（FIX004.18 引入） |
| 6 | main_window.py:135/786/1014 | `_pending_entry` 单槽无盘归属：双盘先后 mix 错配滚动、另一盘装填误清在途、prepare 守卫拒后滞留（与 T2 竞态叠加） | 新增（FIX004.2 设计缺口） |
| 7 | main_window.py:517 + beat_fx:80（对照 :525） | MiniDisplay 两处去 s() 为**误伤**（构造内仅 setMinimumSize，setFixedSize 本无双重）——ui_scale≠1 不缩放；第三处 _rec_display 仍 s() 同类三态 | 新增（FIX004.16 扩面误伤） |
| 8 | automix.py on_mix_started + engine.py:1169-1178 | mix 完成重置清单缺 `_tempo_rate`/`_key_shift`——来曲继承出曲盘乐速偏移与移调（×1.06/+2 半音）；"按 play() 同款重置"未完全兑现（需裁决：延续舞池速度 or 换曲归零） | 新增（FIX004.1 残余） |
| 9 | engine.py:1121-1141 | `_mix_source_chunk` 丢循环回绕——loop 中转场出曲淡化期穿 loop 直冲曲尾静音（原 `_get_chunk` 有回绕） | **新增（FIX004.8 引入回归）** |
| 10 | main_window.py:1351-1366 | mix 完成只滚 meta 不更新 `deck._bpm`/波形网格——混后 Beat FX 延迟/Trans/beat_jump 按旧曲 BPM，Jog 屏与 FX 时基不一致 | 新增（FIX004.1/.2 缺口） |

#### P3（摘要，~20 项）

engine：`_apply_rebias` 终装无二次守卫（E3 停盘复活换入口复现）｜stop 不清 `_mix_finished`（100ms stale 消费）｜完成重置缺 slip/key_shift/_reverse｜`_get_next_chunk` 死代码（FIX004.8 后零调用）｜fader 停止与 stop() 8 行重复（两轮同步改漂移风险）｜close 不关 CuePlayer（E10 未修）｜"弯音可用"注释失实｜analyzer：说明区两处失实（勾验不实本体）｜_detect_timbre 不传 hop（A3 未修）｜numba 目录堆积（A4 未修）｜tm：T2 曲终竞态/T3 死条件/T4 锁外读（三项未修）｜stretcher：S2 吞错未登记｜automix：AUTO 链不感知目标盘切换（late-bind 接缝）｜ui：bus lambda 强持有主窗（多窗 RuntimeError，需验证——生产单窗不可达）｜`deck._mix_finished` 私有直读直写｜silk 样式串 4 份重复｜手动 `_on_prepare` 忽略返回值（AUTO 路径有提示、手动静默同族不一致）｜波形播放头恒 deck_a 色｜贴图键无配色版本（遗留）｜弯音/deck_widget/jog 注释失实 3 处｜三处说明区缺新方法（_glow_params 重复条目）

**A004 记录勘误**：P1#2"24-bit 数值保持 ±2^23 却除 2^31"定性不成立——pydub 构造器无条件 24→32 转换且数值 ×256 升满幅 ±2^31（实测逐值吻合）；真实 256 倍失真仅 8-bit 一档（÷32768 vs 实际 ±128）。当前修复后五档全部正确。

### 二、参考级观察项（~25 项，含回落理由）

_mix_source_chunk 推进-消费恒等零漂移（同式同 frames）；beat_frames clip 上界松而无害；32-bit float wav 经 ffmpeg int32 满幅正确（建议探针补第四档）；plan_set 弧线量纲 0-1 vs energy 1-10 不自洽（零调用预留，PL002 文档补量纲说明）；`_maybe_rebias` 锁外 timer 交错被 orig 守卫兜住（理论）；Censor/负向搜索不遵守 loop（黑胶语义）；AUTO 链 on_done=None 无反馈；`_cycle_theme` 二元 toggle 泛化空间；圆角不随 scale；量化后首次写盘 ≤31 次（达标）；`bind_theme` 自动断开（lambda 形态除外已列）；搓碟 dt 兜底（理论）等——豁免清单非空。

### 三、亮点

三路回归复核确认 FIX004 主体修复真实有效（引擎级断言扎实）；base.json/ui.json 全键矩阵核对终态**零死键零缺键**；audio_decode 五档实测行为全对；ui 组"业务 LED+checked 全按钮无降档漏网"、letter 闭包全对、ThemeBus 无泄漏；config 组发现 requirements 缺 audioop-lts 的**环境可复现性 P1**（冒烟门禁盲区的实证）。

---

## 附录 PATCH002：UI 打磨收口（曲库空态构图 / B 盘空态 / Mixer 密度 / 波形网格可见度）

> 立项：2026-11-06（第三轮 UI 评审验证轮——上轮 Top3 全部闭环、overall 6.0→7.4，剩余四项打磨级一次收口）。
> 状态：✅ **已实施**（2026-11-07，PATCH002 5/5 勾结，见 x.progress.md；probe_patch002 全 PASS + 27/27 回归 + 冒烟 + 截图读图。执行中一处方案回退：QStackedWidget 改互斥可见（库面板布局行为回归）；一处二分发现：waveform paint 内 drawText 中文触发 Qt AV 已改 QLabel 路径。提交 V0.2.7.5 由用户执行）

### 措施（文件/函数级）

1. **曲库空态构图**——`main_window.py _build_ui()`：曲库改 QStackedWidget 两页（页 0=表格 / 页 1=居中引导句 14px）；`_update_lib_hint` 改切页（原引导句沉底且字号 12）
2. **B 盘空态提示**——`waveform_widget.py`：新增 `set_empty_hint(text)` + `paintEvent` 空数据分支（n_peaks<2）在中央绘制 silk 12px 提示（保留边框——"empty keeps frame + 一句话"）；`deck_widget.py set_track` 有曲时清提示；B 盘未加载默认显示"从曲库双击载入曲目"
3. **Mixer 密度**——`main_window._build_mixer_panel()`：横推标签改与横推条同行（原独立一行致 panel-void 边缘）
4. **波形网格可见度**——`waveform_widget.paintEvent()`：下拍线全程 alpha 40→55 + 顶部 6px 实色刻度（密集包络段靠顶部刻度辨认——回应已声明权衡）

### 验证

- `.temp/probe_patch002.py`：空库切页断言 / B 盘提示存储断言 / 横推同行几何断言 / 网格绘制断言 + 双主题 grab 不崩；全量回归 + 截图

---

## 附录 PL003-007 总纲：Tauri 2 + Web 前端 + Python Sidecar 架构迁移（2026-11-07 立项）

> 背景：PySide6 拟物化受限于前端表现力（三轮 UI 评审 7.4 封顶），用户定案迁移至 Tauri 2 + Web（Vue3+TS+Vite）+ Python sidecar；**引擎资产（modules/ 五轮审计代码）100% 保留**，仅替换 UI 层与进程壳。
> 边界（用户定案）：5 个 PL 完成即**迁移完成**（Web 全功能 + 旧栈退役 + 工程门禁切换）；性能优化/深度测试/韧性/打包发布全部后置为迁移后阶段，不占本五案。
> 状态：PL003 实施中（2026-11-08：gateway/协议文档/webui 骨架完成，probe_gateway 19 项 PASS；Tauri 壳编译验证中）；PL004-007 依次排期（004/005 可并行）。

### 〇、总体架构与贯穿决策

```
Tauri 2 壳（Rust 零业务：窗口/文件对话框/sidecar 进程管理）
 └─ WebView2 → webui/（Vue3+TS+Vite：拟物 UI、Canvas 波形/转盘、60fps 动效）
      ↕ WebSocket（127.0.0.1 动态端口：RPC 指令帧 + 事件推流帧 + 二进制峰值帧）
 └─ spawn → Python sidecar（开发态 = .venv 解释器；打包态后续阶段）
      └─ modules/gateway.py（唯一新增模块：asyncio WS 服务）
         ├─ 指令路由（→ 现有引擎方法，modules/* 零改动）
         ├─ 30Hz 状态推流（asyncio 轮询，绝不进音频回调线程）
         └─ 数据端点（波形峰值/曲库/分析进度/推荐）
```

贯穿决策：
1. **引擎零改动**——现有"UI 只发指令"纪律兑现：MainWindow 换 WS 网关，modules/ 不动
2. **协议双通道**——RPC 帧 `{id, cmd, args}→{id, ok/error}` + 事件帧（tick/波形/分析）；大数组二进制帧（f32 LE）
3. **假引擎注入复用**——探针已验证的 FakeEngine 模式用于网关无头测试（UI 层首次获得稳定回归手段）
4. **版本单一来源不变**——base.json `version` 仍是唯一源
5. **双栈并存渐进**——PL003-006 期间 PySide6 旧版保留可对照，PL007 才退役

### 一、PL003 — Sidecar 骨架与 WS 协议 v1（架构闸门）

> 目标：最小端到端链路——浏览器按钮 → 真引擎真声音 → 状态回显。可行性验证，后续一切基座。

- `modules/gateway.py`（新）：asyncio + websockets 轻量服务；引擎注入（构造传 engine / 测试传 FakeEngine）；指令路由首批 8 条（load/play/pause/cue/seek/volume/xfader/mix）；30Hz tick 推流任务（asyncio 轮询 deck.position/state/vu_levels，不进音频回调）；`--fake` 参数无音频设备可跑
- `docs/ipc_protocol.md`：帧 schema（RPC/事件/二进制峰值）+ 协议版本 + 错误码
- `shell/`（Tauri 2 + shell 插件）：dev 模式 spawn `.venv python -m modules.gateway`；动态端口 + 就绪握手 + 前端注入
- `webui/`（Vite+Vue3+TS 骨架）：连接状态屏 + hello-DJ 一屏（加载/播放/CUE/BPM/位置条）
- 验证：`probe_gateway.py`（FakeEngine+WS 客户端：路由/频率≥25Hz/错误帧/断线重连）+ tauri dev 全链冒烟真机出声
- 退出标准：真机出声、30Hz 流稳定、杀 sidecar 前端可重连

### 二、PL004 — 双盘控制面全量对齐

> 目标：控制面平价——以 main_window 现有信号接线清单为唯一对照表逐条迁移，漏一条不算完成。

- Deck 区：Jog 转盘（Canvas 滚轮弯音/拖动搓碟/Vinyl/播放指示）、Pad 8 键五模式+灯态、TEMPO+量程、Keylock/Key Shift/Sync、循环键行、Slip/Censor/Stutter
- Mixer 区：TRIM/EQ×3 旋钮（拖拽+双击回中）、VU 灯柱、通道推子/横推、FaderStart/Tap、PHONES 预听
- Beat FX：效果组/通道/拍数/深度/ON + FX 状态小屏；Effects 推荐区（NEXT/AUTO）
- 指令路由表扩至全集；Shift 语义、快捷键（空格/Ctrl+F/Ctrl+T）、Tab 序
- `webui/src/composables/useEngine.ts`：状态→组件响应式绑定层（对应现 _tick 职责）
- 验证：协议一致性探针（每指令→引擎状态断言，复用现有断言库改写）+ taste-skill app-screens 评审首轮
- 退出标准：功能对照清单 100%；操作延迟主观 <50ms

### 三、PL005 — 曲库/分析/Automix 数据层

> 目标：数据面平价——曲库、分析管线、M2 自动编排全量上 Web。

- 曲库表：虚拟滚动/搜索/兼容标记/双击装载/拖拽到盘、Instant Doubles
- 分析进度流（事件帧推送替代 QueuedConnection 回填）、失败降级展示
- 波形数据管线：服务端峰值计算（复用 _build_peaks 逻辑）→ 二进制帧一次传输+播放头增量；下拍网格/BPM 标线 Canvas 分层
- Automix：推荐区（NEXT/AUTO/explanation）、Prepare/Mix 转场状态可视化
- Tauri dialog 插件接文件夹选择
- 验证：数据一致性探针（曲库状态==引擎装载状态双向核对）+ 波形渲染断言
- 退出标准：M1+M2 全功能 Web 面可用，PySide6 仅剩可对照旧版

### 四、PL006 — 拟物视觉与动效体系

> 目标：迁移初衷兑现——视觉质变（唯一"新能力"PL）。

- Design tokens：ui.json → CSS variables（含 theme_light 覆盖），运行时双主题切换（对应 palette/ThemeBus 语义）
- 拟物组件库 `webui/src/components/skeuo/`：旋钮/推子/背光钮/灯柱/金属面板（程序化纹理超越 QPainter：真辉光 blur、金属各向异性）
- 60fps 动效：转盘随播放旋转、推子跟手、VU 峰值保持衰减、转场 EQ 渐变/波形交叉可视化、加载态
- 布局配置化迁移（splitter 比例/间距网格/尺寸分级 → CSS grid + tokens）
- 验证：taste-skill 评审 ≥2 轮 + 与 PySide6 版 before/after 并排对比
- 退出标准：评审 overall ≥8.0（现 7.4）；动效无掉帧

### 五、PL007 — 迁移收口：PySide6 退役与工程体系切换（不含打包）

> 目标：Web 面成为唯一前端，工程门禁切换到新栈。开发形态即终态（gateway + tauri dev 能跑即验收）。

- 双栈对照验收：PL004 功能清单 + PL005 数据清单 + live 听感（AUTO 接歌/转场 EQ/Keylock）逐项签收——退役前置闸门
- PySide6 退役：ui/ 移 archived/；requirements 剥离 PySide6；main.py GUI 分发改 gateway 入口
- 探针体系切换：引擎/协议探针为门禁主力；PySide6 UI 探针随旧栈归档（行为断言已由协议探针在 PL004/005 承接）
- webui 测试基线：vitest 单测（composables 逻辑层）+ 组件冒烟——只建基线
- AGENTS.md 工作流更新：Node 工具链进环境陷阱；门禁重排（引擎探针+协议探针+vitest+tauri dev 冒烟）；冒烟清单去 PySide6 加 gateway
- 验证：退役后全量回归 + `git grep PySide6` 仅剩 archived//文档历史 + tauri dev 冷启动全流程
- 退出标准：对照清单签收；PySide6 出 requirements；AGENTS/README/z.plan 反映新栈

### 六、迁移后阶段池（不占本五案，届时按需立项）

性能调优（指令往返/波形压缩/60Hz 流）｜深度测试（组件/协议矩阵/故障注入）｜韧性（心跳/自动重启/重连 UI 完整化）｜打包发布（PyInstaller sidecar + Tauri bundler + 安装包）｜视觉精修迭代

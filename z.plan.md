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
- [ ] **M2 第二步：AI 自动 DJ**
  - [ ] 兼容性评分：BPM 倍频归一化 / Camelot 档位 / 能量曲线 / 音色 / 人声冲突
  - [ ] 调和混音（Camelot 轮盘）选曲与 Set 规划（同艺人约束/去重/能量弧线）
  - [ ] 节拍对齐自动转场：prepare/mix 管线接入 AI 调度（EQ 渐变 + 下拍触发）
  - [ ] 自动 Set 规划：贪心编排 + 能量曲线 + 可解释评分（explanation/warnings）
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
> 状态：✅ **已实施**（2026-11-05，任务组 PL001 见 x.progress.md——16/16 条勾结；probe_pl001 全 PASS + 22/22 探针回归 + 冒烟 OK；after 截图 dark/light×3 特写目检全过（截断清零/色块消失/VU 框架可见/Jog 无叠字/FX ON 描边激活/空态引导）；执行中升级两处根因——GlowButton 无 sizeHint 覆写（截断源头）与五列最小宽超主区（Pad 全宽化 + mins+shares 机制解决）；遗留 PanelFrame 标题重叠记 y.problem#P5。提交 V0.2.6.1 由用户执行）

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


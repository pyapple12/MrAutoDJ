# 开源 DJ 软件调研报告

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

## 附录：全量代码审计报告（2026-08-12）

> 范围：全部 25 个 .py + 3 个 JSON 配置（main.py / utils×5 / config×3 / modules×8 / ui×10 / ui/widgets×6）
> 方式：三路并行只读审计（utils/config、modules、ui），信号接线全量核对无类型失配；未修改任何代码
> 状态：✅ **P0-P3 已全部修复**（2026-08-12 G 系列完成，见 x.progress.md；probe_g0-g3 + 全量回归 9/9 PASS + GUI 实测确认；后续多轮审计迭代中）

### 一、重复造轮子专项（14 处，本次审计重点）

| #   | 重复点                                                         | 位置                                                                         | 后果                                                                              |
| --- | -------------------------------------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| 1   | pydub 解码+归一化                                              | engine.load_audio vs analyzer._decode_mono                                   | 归一化策略不一致（按位深 vs 固定 32768），24/32-bit 两处数值不同；应抽 utils 共用 |
| 2   | utils.convert 弹性转换零使用                                   | analyzer.py:20 导入 to_float 未调用；to_int/to_optional_float 无调用方       | 弹性转换防线形同虚设                                                              |
| 3   | utils.retry 整模块无调用                                       | radio/analyzer 均未用                                                        | 与"缓存兜底/重试"策略脱节                                                         |
| 4   | config.settings 整模块无调用                                   | AppConfig/load/save_config 零引用                                            | 用户配置持久化未接线 UI                                                           |
| 5   | 金属渐变绘制三处重复                                           | jog_wheel/fader_slider/rotary_knob（同色值系）                               | 应抽 ui/widgets/_skins.py 公共皮肤工具                                            |
| 6   | 滚轮步进"全程/20"两处                                          | rotary_knob/fader_slider                                                     | 抽公共常量                                                                        |
| 7   | 拍长计算两处                                                   | engine beat_jump vs set_beatloop                                             | 提取 _beat_len(bpm)                                                               |
| 8   | 候选打分循环两处                                               | analyzer._estimate_bpm vs _pick_metrical_level                               | 提取 _score_candidate()                                                           |
| 9   | Key Shift 钳制两处                                             | engine.py:456 vs transition_manager.py:124                                   | 统一进 config                                                                     |
| 10  | 回调内插值结构重复                                             | engine 弯音 vs scratch（idx/i0/i1/frac 加权）                                | 抽公共插值方法                                                                    |
| 11  | scan_folder 重复风险                                           | analyzer.py:530 已实现 vs library.py 占位同名                                | M1 实现时直接复用勿重写                                                           |
| 12  | set_channel_fader 复制 deck.stop 逻辑                          | engine 锁内直改 7 个私有字段                                                 | Deck 提供原子 fader_stop/start()                                                  |
| 13  | 表头配置未用                                                   | main_window 硬编码 ["Mix",…] vs ui.json table_headers ["状态",…]（值不一致） | 用配置驱动                                                                        |
| 14  | file_utils.clear_cache 死代码 + read_json 对不存在文件也写缓存 | —                                                                            | 缓存永久陈旧风险                                                                  |

### 二、严重问题（功能/正确性/稳定性）

1. themes.py 未接线：apply_theme() 全项目无调用，QSS 从未生效（自绘控件不受影响，原生控件/表格无样式）
2. analyzer.py:501 engine_sr=44100 硬编码：base.json 采样率变更即 beats/downbeats 索引错位（正确性 bug）
3. engine.py:818 除零：start_mix 不校验 fade_seconds>0 → _fill_mixing 除零整段静音
4. engine.py:740 正向搜索形状错误：|search_rate|<1 时 out[:]=chunk[:frames] 形状不匹配（与已修弯音 bug 同源未修）
5. stretcher.py 无 rubberband 前置检查：缺失时 TypeError 而非可读错误
6. CuePlayer 二次失败外抛：与"故障静默 is_dead"承诺相悖
7. rotary_knob.py:115-123 指针绘制可疑：QRectF 当"点"用 + 取 center，线段起点/长度异常，应直接 drawLine(cx,cy,…)
8. panel_frame.py:37 set_title AttributeError：无标题构造后调用必崩
9. pad 灯态冲突：pad 点击 isChecked 残留 + GlowButton 辉光判定混用交互态/业务灯态 → pad 灯阵失真
10. main_window.py:535 直接写 deck._position：绕过锁与 API（Instant Doubles）
11. deck_widget.py:95 44100 硬编码：M:SS 换算与 base.json 脱钩（说明区自认）

### 三、硬编码与配置化（AGENTS.md 参数约定违反）

- modules 层：MAX_GAIN/VU_BUFFER/EQ 频率(100/1k/10k Hz)与增益斜率/Hot Cue 槽位 8×6 处/弯音±0.5/搜索±16/Key Shift±12/转场参数(16s/30s/0.1s)/分析参数群（MIN/MAX_BPM、能量权重、CUE 参数）
- ui 层：#ff7a2f 等配色 20+ 处与 ui.json 同名键重复、定时器 100ms、splitter 比例、16777248（应 Qt.Key_Shift）、Instant Doubles 0.5s、状态栏 5000ms、Pitch 范围、Beat Loop/Jump 拍数表
- 配置承诺未兑现：led_strip 读 ui.json 不存在的键（led_green_threshold/led_yellow_threshold）；jog_wheel SEARCH_WHEEL_STEP=4.0 未进配置；table_headers 键死配置

### 四、防御性编程缺口

- convert.to_float 不拦截 "nan"/"inf"（污染分析数据）
- waveform._build_peaks 无 1D 音频防护（IndexError）
- fader_slider/rotary_knob 在 min==max 时除零
- glow_button/mini_display 长文本溢出无省略
- static_config 对 mapping 非 dict、键缺失无校验（与"抛错暴露"注释矛盾）
- engine EQ/FX setter 无锁（系数错配一帧）；浮点精确比较（==1.0）脆弱

### 五、死代码

vu_meter.py 整模块（被 LedStrip 替代）、shift_state.toggle/active/changed（零调用零订阅）、fader_slider._TRAVEL、main_window QMessageBox 导入/_UI_COLORS/_on_search_release 占位接线、engine._last_out_pos（只写不读）、transition_manager._next_bpm/_next_downbeats（只写不读）、utils.convert 两函数、utils.retry 整模块、config.settings 整模块、file_utils.clear_cache

### 六、规范违反

- 函数内延迟导入 8+ 处（main_window×5、engine import time、analyzer tempfile/get_project_root、deck_widget Path）——librosa 豁免条款不适用
- Optional[...] 6+ 处未用 | None；tuple/list/dict 泛注解多处
- 说明区失实 5 处：engine（缺类/常量/分配取舍注释）、jog_wheel（0.02/×256 全面过时）、analyzer（缺 6 函数）、stretcher、convert（声称 analyzer 复用失实）
- 参考标注注释：jog_wheel/pad_widget/beat_fx/vu_meter/shift_state 第 2 行"参考：w.study.md…"——与"正式程序文件禁止参考标注"字面冲突

### 七、亮点（合规良好）

回调 fail-soft 双 try/except 静音降级落实到位；预分配缓冲（_buf_a/_buf_b/VU 环形）设计正确；analyzer 进程池 spawn + numba 缓存隔离（Windows 安全）；信号接线全量核对无类型失配；占位模块 M2/M3 边界清晰；文件尾说明区体系基本完整

### 八、建议优先级

| 优先级    | 事项                                                                                                                         |
| --------- | ---------------------------------------------------------------------------------------------------------------------------- |
| P0 正确性 | ① analyzer 采样率硬编码 ② 搜索分支形状错误 ③ fade 除零 ④ rotary 指针绘制 ⑤ pad 灯态冲突 ⑥ panel set_title 崩溃 ⑦ themes 接线 |
| P1 去重   | ① 解码归一化统一（严重，数值不一致）② 金属渐变抽 _skins.py ③ 拍长/钳制/步进公共化 ④ 表头配置化                               |
| P2 配置化 | modules 参数群 + ui 配色 20 处进 config，兑现 led 阈值/搜索步进/表头承诺                                                     |
| P3 清理   | 死代码（vu_meter/settings/retry/convert 未用部分）→ 归档或接线；说明区同步；Optional→\|None；延迟导入上移；参考标注移除      |

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

- [ ] M1 第一步：虚拟 DJ 台
  - [ ] 双打碟机（播放/暂停/CUE/循环）
  - [ ] 波形显示（离线分析+实时滚动）
  - [ ] 三频 EQ + 横推（Crossfader）
  - [ ] Pitch 变速 + Keylock 变调不变速
  - [ ] 自动 BPM 检测
  - [ ] 双输出声卡（监听）
- [ ] M2 第二步：AI 自动 DJ
  - [ ] 调和混音（Camelot 轮盘）选曲
  - [ ] 节拍对齐自动转场（EQ 渐变）
  - [ ] 自动 Set 规划/能量曲线
- [ ] M3 第三步：Claude 电台
  - [ ] 引擎暴露控制接口（HTTP/MCP）
  - [ ] Claude API 工具调用（选歌/接歌/报幕）
  - [ ] 点歌互动（直播间消息入口）
  - [ ] TTS 语音报幕

## 参考项目（来自上文调研）

Mixxx（架构参照）、pyCrossfade、ai-remixmate、radio-dj、WrzDJ（点歌台）、mixx-dj-mcp（LLM 控制 Mixxx 思路）

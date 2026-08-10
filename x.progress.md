# MrAutoDJ 源码研读任务清单（x.progress.md）

> 目标：通读 12 个参考仓库，提炼本项目（Python 虚拟 DJ 台 → AI 自动 DJ → Claude 电台）可借鉴的
> 代码结构、文件分类规范、代码规范、错误处理规范，逐步产出报告至 `w.study.md`。

## A. 前期准备

- [x] A1 扫描仓库结构
- [x] A2 建立 w.study.md 报告骨架

## B. 逐个阅读参考仓库

- [x] B1 songs-automixer_python：引擎结构、TUI 交互、节拍匹配/变速/渐变、错误处理与测试
- [x] B2 pyCrossfade：混音引擎/节拍对齐/EQ 过渡算法、库结构、测试与 CI
- [x] B3 automix：AI 选曲/转场逻辑、配置与数据组织、规范化写法
- [x] B4 cuekey：BPM/调性分析管线、打包与发布、文档规范
- [x] B5 ai-remixmate：总体设计、引擎核心（转场/人声分离/LUFS）、配置系统、工程化规范
- [x] B6 dj-track-similarity：embedding 相似度方案、核心代码、前端/API 组织、工具集与测试
- [x] B7 radio-dj：LLM 报幕 + 推流架构、调度/技能体系、Go 结构映射启示
- [x] B8 writ-fm：报幕稿生成 + TTS 链路、配置/调度/运维、工程组织与测试
- [x] B9 mixx-dj-mcp：MCP 控制 DJ 设计、工具注册与 bridge、工具分类与错误处理
- [x] B10 claudio：产品设计、前后端结构、歌单/口播/TTS 调用链、可视化交互
- [x] B11 wrzdj：点歌台架构、server 与 bridge、kiosk/dashboard、部署与安全
- [x] B12 mixxx：架构总览、引擎核心、波形/效果/曲库、规范提炼

## C. 汇总产出（写入 w.study.md）

- [x] C1 12 个项目"可借鉴点"分项目汇总
- [x] C2 归纳文件分类规范 / 目录结构规范（跨项目共性）
- [x] C3 归纳代码规范（命名、类型、依赖管理、配置管理）
- [x] C4 归纳错误处理与日志规范（跨项目对比）
- [x] C5 归纳测试与 CI 规范
- [x] C6 输出对 MrAutoDJ 的分阶段落地建议（M1/M2/M3 各参考哪些）

## D. M1 虚拟 DJ 台任务清单（细粒度，带参考）

> 参考标注格式：`.reference/<分类>/<仓库>/<文件>`，建议按路径先读对应文件再实现。
> 音频数组约定：引擎 `(N,2) float32 [-1,1] @44100Hz`；分析 22050Hz mono（AGENTS.md）。

### D0 前置环境（一次性）

- [x] D0.1 安装依赖：`.venv\Scripts\python.exe -m pip install -r requirements.txt`（PySide6/sounddevice/numpy/scipy/soundfile/pydub/librosa）+ 系统级 ffmpeg（pydub 解码依赖）
- [x] D0.2 检查 `config/static/base.json` 已含音频参数（sample_rate=44100/block_size=2048/channels=2/analysis_sample_rate=22050/analysis_hop=512/cache_path）
- [x] D0.3 冒烟验证基线：AGENTS.md 中的 import 命令必须通过（现有占位代码已满足）

### D1 曲库与分析（modules/library.py + modules/analyzer.py）

- [x] D1.1 `library.scan_folder(root)`：递归收集支持格式（mp3/flac/wav/ogg/m4a/aac/opus/wma/aiff/mp4/webm），排序返回绝对路径列表
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/analyzer.py` 的 `SUPPORTED_EXTENSIONS` 与 `scan_folder`
- [x] D1.2 `analyzer.analyze_file(path)` 骨架：解码（pydub 转 22050Hz mono /32768）→ 依次调 tempo/key/energy/cues 子函数 → 返回记录 dict
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/analyzer.py` 的 `analyze_file`（整体管线结构）
- [x] D1.3 BPM 检测：librosa `onset_strength` + 自相关候选打分；实现 `fold_bpm`（折进 70-180）、`refine_bpm`（间隔中值剔除离群）、`snap_bpm`（吸附整数/半整数）
  - 参考：`.reference/ai-autodj/cuekey/src/cuekey/analysis/tempo.py`（estimate_bpm/pick_metrical_level/fold_bpm/refine_bpm/snap_bpm）
- [x] D1.4 拍点追踪：纯 numpy Ellis DP 追踪器（`track_beats`），返回帧索引转秒
  - 参考：`.reference/ai-autodj/cuekey/src/cuekey/analysis/tempo.py` 的 `track_beats`/`local_maxima`
- [x] D1.5 downbeat 检测：从拍点中选相位（4 拍一强拍，40-150Hz 低频能量最大化）
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/analyzer.py` 的 `_pick_downbeat_phase`
- [x] D1.6 调性检测：`librosa.effects.harmonic` 分离 → chroma_cqt(tuning=0.0) → 时间中位数 → 24 键 KK 相关，返回 "Am"/"F#m" 记谱 + 置信度
  - 参考：`.reference/ai-autodj/cuekey/src/cuekey/analysis/key.py`（detect_key/\_pearson/detect_key_from_chroma）
- [x] D1.7 Camelot 轮盘：`Key(pitch_class, mode)` frozen dataclass + `camelot`/`openkey` 记谱 + `parse_key`
  - 参考：`.reference/ai-autodj/cuekey/src/cuekey/camelot.py`（完整照抄思路）
- [x] D1.8 能量 1-10：响度(90%分位 RMS)40% + onset 密度 25% + 低频占比 20% + 拍速 15%
  - 参考：`.reference/ai-autodj/cuekey/src/cuekey/analysis/energy.py`
- [x] D1.9 自动 CUE 点：MFCC+chroma 聚合聚类分段 → 边界吸附 downbeat → 8s 最小间距去重 → 最多 8 个
  - 参考：`.reference/ai-autodj/cuekey/src/cuekey/analysis/cues.py`
- [x] D1.10 分析缓存：SQLite（表：path PK/size/mtime_ns/version/has_cues/payload），校验 size+mtime+版本号，坏条目返回 None 重分析
  - 参考：`.reference/ai-autodj/cuekey/src/cuekey/cache.py`（含 ANALYSIS_VERSION 常量与 CUEKEY_CACHE_DIR 环境变量思想）
- [x] D1.11 `analyze_many(paths, on_result, should_stop)` 批处理：缓存命中先回 → 剩余走进程池（spawn + numba 缓存隔离 + max_tasks_per_child=16 防内存爬升 + BrokenProcessPool 重建）
  - 参考：`.reference/ai-autodj/cuekey/src/cuekey/analyzer.py`（analyze_many/\_warm_worker/default_workers）
- [x] D1.12 失败降级：单曲分析异常 → `empty_record()`（bpm=0/key="?"）记日志继续；坏文件绝不中断整批
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/analyzer.py` 的 `empty_record`
- [x] D1.13 CLI：`python -m modules.analyzer --folder <路径> [--json]`，打印进度条（ASCII `#`，Windows cp1252 兼容）
  - 参考：`.reference/dj-engine/songs-automixer_python/main.py`（argparse + 进度回调模式）

### D2 音频引擎（modules/engine.py）

- [x] D2.1 `AudioEngine` 骨架：常驻 `sd.OutputStream(44100, 2, float32, blocksize=2048)` + `threading.Lock` + `State(IDLE/PLAYING/MIXING)` 枚举；回调内零 IO、锁内操作短
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/audio_engine.py`（**init**/\_callback/State）
- [x] D2.2 `load_audio(path)`：pydub 解码 → set_channels(2)/set_frame_rate(44100) → `/32768.0` 归一化 → (N,2) float32
  - 参考：同上的 `load_audio`
- [x] D2.3 `play(audio)`/`pause()`/`stop()`：状态迁移 + 清播放头 + FX 状态 reset
  - 参考：同上的 `play`/`pause`/`stop`
- [x] D2.4 `_fill_playing`：取块、写 outdata、自然结尾置 IDLE（越界补零）
  - 参考：同上的 `_fill_playing`/`_get_chunk`
- [x] D2.5 `start_mix(next_audio, fade_seconds, scheduled_start_sample=None)`：**样本级定时切歌**（到达指定 sample 同帧内切 MIXING，无静音缝隙）；`_fill_mixing` 线性/等功率交叉淡化；结束 `_position=_mix_pos` 接续
  - 参考：同上的 `start_mix`/`_fill_mixing`（scheduled_start_sample 机制是 M2 对拍的基础）
- [x] D2.6 等功率曲线：`fade_in=sin(πt/2)`、`fade_out=cos(πt/2)`（与线性并存，settings 可选）
  - 参考：`.reference/ai-autodj/automix/automix/effects/mixer.py` 的 `SimpleCrossfader`（fade_type 库）
- [x] D2.7 三频 EQ（每 deck）：4 阶 Butterworth（24dB/oct），**系数在 setter 线程算、回调只跑 lfilter**，`zi` 状态跨块持久（换效果/开关时重置防咔嗒），float64 递归
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/fx.py` 的 `MasterFx`（完整照抄）
- [x] D2.8 横推（Crossfader）：位置 [-1,1]，常量功率曲线（CONSTPWR）+ 可选 ADDITIVE，输出限幅 ±1.0
  - 参考：`.reference/arch-soft/mixxx/src/engine/enginexfader.h`（getXfadeGains 曲线思想）+ `.reference/ai-autodj/automix/automix/effects/mixer.py`（equal_power 数学）
- [x] D2.9 音量：master `[0, 2.0]`（boost 输出硬限幅 ±1.0）+ cue `[0, 1]` 无 boost（护耳），回调内应用
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/audio_engine.py`（MAX_GAIN 与回调限幅）
- [x] D2.10 CUE 功能：`cue_set`（当前位置设 CUE）、`cue_play`（回到 CUE 播放）；CUE 值吸附到最近 downbeat（B1 的 cue_snapped 机制）
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/app.py` 的 `NextTrackPanel.set_cue`（吸附逻辑）+ `.reference/claude-radio/mixx-dj-mcp/src/mixx_dj_mcp/tools/deck_control.py`（操作命名）
- [x] D2.11 循环：`loop_activate`（开关，量化为整小节边界）+ `beatloop_N`（1/2/4/8/16/32/64 拍）
  - 参考：`.reference/claude-radio/mixx-dj-mcp/src/mixx_dj_mcp/tools/deck_control.py`（loop_beat/beatloop 操作）
- [x] D2.12 变速预渲染：`plan_transition(now_bpm, next_bpm, fade)`（八度折叠 + 漂移阈值 0.25 拍判定 skip/stretch）→ `make_transition_buffer`（rubberband CLI `-3 --centre-focus -M timemap -D dur`，64 锚点，smootherstep 渐变回 1.0）
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/transition.py` + `automix/stretcher.py`（完整照抄，含 timemap 坑位注释）
- [x] D2.13 Keylock（变调不变速）：变速渲染后做变调（rubberband pitch 参数或 pyrubberband），与变速管线共用预渲染框架
  - 参考：`.reference/dj-engine/pyCrossfade/pycrossfade/utils.py` 的 `time_stretch`（pyrubberband 通道感知用法）
- [x] D2.14 双输出监听：`CuePlayer` 独立 `sd.OutputStream`（第二设备），**与主引擎完全解耦**（独立锁/缓冲/播放头），PortAudioError 回退设备采样率 + np.interp 重采样，失败置 `is_dead` 静默
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/cue_player.py`（完整照抄）
- [x] D2.15 引擎错误纪律：回调 `try/except` fail-soft（静音降级置 dead），绝不抛到 UI 线程；`load_audio` 失败抛分类异常由上层降级
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/cue_player.py` 的 `_callback` 异常处理

### D3 变速转场集成（引擎 ↔ 预渲染）

- [x] D3.1 `prepare_mix()`：加载来曲 → `plan_transition` 判定 → SKIP 直接缓存原始 CUE 音频 / STRETCH 后台线程渲染（`_prep_epoch` 计数器防陈旧结果，完成比对不一致即丢弃）
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/app.py` 的 `action_prepare_mix`/`_prep_epoch`（关键机制）
- [x] D3.2 `mix_now()`：调用 `engine.start_mix`（对拍时用 `scheduled_start_sample` 对齐来曲 downbeat）；转场中禁止再次混音（状态守卫）
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/app.py` 的 `action_mix_now`/`_commit_mix` 守卫
- [x] D3.3 参数改动失效机制：CUE/Fade 变更后旧预渲染缓冲标记 stale 重渲染（`_mark_stale`）
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/app.py`（Key invariants 中对应条目）

### D4 UI 层（ui/）

- [x] D4.1 `MainWindow`：PySide6 主窗口，布局 = 顶部曲库（搜索/表格）+ 中部双 DeckWidget + 底部混音台（EQ 旋钮 × 2 组 + 横推滑块 + 主音量）；深色主题（ui.json 颜色）
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/app.py` 的 compose/CSS（布局分区思想）+ `.reference/arch-soft/mixxx/res/skins`（布局层级参考，无需读码）
- [x] D4.2 `DeckWidget`：曲名/BPM/调性显示 + 播放/暂停/CUE/循环按钮 + Pitch 滑块 + Keylock 开关；全部操作走引擎锁内方法，UI 只发指令
  - 参考：`.reference/claude-radio/mixx-dj-mcp/src/mixx_dj_mcp/tools/deck_control.py`（操作集合定义）+ `.reference/dj-engine/songs-automixer_python/automix/app.py`（按键绑定思想）
- [x] D4.3 `WaveformWidget`：离线峰值数组（载入时降采样缓存）+ 播放头按 `engine.position` 滚动（100ms 定时器刷新，跨线程经 Qt 信号）
  - 参考：`.reference/arch-soft/mixxx/src/waveform`（目录结构参考，GPU 渲染不需要）+ 音频约定
- [x] D4.4 曲库表格：双击加载到 Deck A/B（拖拽可选）、显示 BPM/调性/能量、`:)` 标记兼容曲目（octave-folded）
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/app.py` 的 `_match_marker`/`tempo_compatible`
- [x] D4.5 状态栏与日志：状态提示走 `utils.logger`；UI 事件回调异常捕获（不崩溃）
  - 参考：`.reference/dj-engine/songs-automixer_python/automix/app.py` 的 `_status` 模式

### D5 集成与验证

- [x] D5.1 无头引擎测试：`AudioEngine.__new__(...)` 跳过开流 + 合成 numpy 音频直驱 `_callback`，验证状态机/混音/EQ/循环（`.temp/probe_engine.py`）
  - 参考：`.reference/dj-engine/songs-automixer_python/tests/probe_*.py`（**new** harness 模式）
- [x] D5.2 GUI 无头初始化：`$env:QT_QPA_PLATFORM="offscreen"` 下 MainWindow 构建不报错
  - 参考：AGENTS.md 验证命令
- [x] D5.3 端到端验证脚本：`.temp/verify_m1.py`——扫描测试曲库 → 分析（缓存二次秒开）→ 双盘加载 → 播放 → EQ/横推操作 → 变速切换 → 无异常退出
- [x] D5.4 冒烟验证：AGENTS.md import 命令 + `main.py --version` 通过
- [x] D5.5 提交：`feat: V0.1，完成虚拟 DJ 台（双盘/EQ/横推/变速/波形/分析缓存）`（中文 conventional + 版本号）

## E. M1.5 FLX4 交互复刻任务清单（带参考标注）

> 依据：w.study.md B13 报告（FLX4 功能清单）；参考标注：
>
> - B13-<节>：w.study.md B13 报告章节
> - MIDI：.reference/dj-controller/DDJ-FLX4/Pioneer-DDJ-FLX4.midi.xml（281 控件映射）
> - MZH：.reference/dj-controller/DDJ-FLX4/Mixxx_zh_controller_pioneer_ddj_flx4.html（Mixxx 中文映射）

### E1 引擎支撑层（modules/engine.py 扩展）

- [x] E1.1 Hot Cue 槽位：Deck 加 `_hot_cues`（8 槽），`hot_cue_set(idx)/hot_cue_play(idx)/hot_cue_clear(idx)/hot_cue_state(idx)`；暂停时按住预听（Cue Point Sampler 语义）
  - 参考：B13-3.14（CUE 三态语义）、B13-3.12（Pad Hot Cue 模式）、MZH-Hot Cue Mode
- [x] E1.2 Beatgrid 跳转：`beat_jump(±beats)`（按 BPM 间隔跳转，对齐最近拍）；Vinyl 关时的 Skip 模式（跳转不脱拍）
  - 参考：B13-3.4/3.5（CUE/LOOP CALL）、B13-3.10（Beat Jump 模式）、MZH-Beat Jump Mode
- [x] E1.3 Key Shift 半音：Deck 加 `_key_shift`（±12 半音）；基于 stretcher.make_keylock_buffer 预渲染管线（切换时渲染，state 变化失效旧缓冲）
  - 参考：B13-3.11（Key Shift 模式）、MZH-Pitch Shift Mode（灯阵表）、既有 modules/stretcher.py
- [x] E1.4 Jog 引擎接口：`jog_touch(on)`（触摸态）、`jog_scratch(delta_samples)`（搓碟位置偏移）、`jog_bend(rate)`（临时弯音，持续至释放）、`jog_search(rate)`（SHIFT 高速搜索）
  - 参考：B13-3.16（Jog 转盘：Vinyl 开=搓碟、外圈/顶面=弯音、SHIFT=高速搜索）、MIDI（Jog 映射：0xB0/0x22、0xB0/0x21、触摸 0x90/0x36）
- [x] E1.5 VU 电平采集（方案 C）：引擎预分配峰值数组（每盘 1×N 环形），回调内无分配算峰值（max/min 组合，不新建数组）写入；UI 定时器读取
  - 参考：B13-4.5（通道电平指示）、决策记录（方案 C：预分配 + 定时器）
- [x] E1.6 Slip 模式：Deck 加 `_slip_active/_slip_actual`（隐藏真实位置暗中推进），`slip_toggle()`；结束后落回真实位置
  - 参考：B13-8（Slip 模式）、MIDI（reverseroll 0x90/0x0E 关联）
- [x] E1.7 Sampler 槽位：每盘 8 槽，`sample_load/play/stop/unload(slot)`；采样混入对应盘输出
  - 参考：B13-3.11（Sampler 模式）、MZH-Sampler Mode
- [x] E1.8 效果库扩展：`Echo`（延迟线：环形缓冲 + feedback）、`Delay`（多 tap）加入效果库，与既有 HPF/LPF/Trans 组合链
  - 参考：B13-5（Beat FX）、既有 modules/engine.py Biquad/DeckEQ 模式
- [x] E1.9 传输辅助：`fader_start(enabled)`（推子联动：0→播放、到底→停止）、`tap()`（Tap BPM：时间戳队列算 BPM）、`censor()`（按住反向播放）、`stutter()`（回临时 CUE 播放）
  - 参考：B13-4.10（Tap 功能）、B13-4.14/4.15（Fader Start）、B13-8（Censor/Stutter）、MIDI（reverseroll）

### E2 UI 交互层（ui/ 新增组件）

- [x] E2.1 全局 SHIFT 组合键体系：SHIFT 修饰状态（键盘/按钮），各控件第二功能分发
  - 参考：B13-3.15（SHIFT）、B13 各部件 SHIFT 列
- [x] E2.2 Pad 打击垫组件（ui/pad_widget.py）：1×8 网格 + 模式切换（Hot Cue / Beat Loop / Beat Jump / Sampler / Key Shift）
  - 参考：B13-3.12（Pad）、B13-3.8-3.11（模式键）、MZH-Pad Modes
- [x] E2.3 Jog 转盘控件（ui/jog_wheel.py）：圆盘绘制 + **外圈滚轮=弯音、顶面按住拖动=搓碟**、触摸态、SHIFT+滚=高速搜索、Vinyl 模式开关
  - 参考：B13-3.16（Jog 交互）、决策记录（双交互结合）
- [x] E2.4 Beat FX 面板：效果类型选择（HPF/LPF/Echo/Delay/Trans）、通道选择（CH1/CH2/双）、拍数 ±、BPM Auto/Tap、LEVEL/DEPTH
  - 参考：B13-5（Effects 区 6 部件）、MIDI（0x94 通道 FX 映射）
- [x] E2.5 Mixer 补全：TRIM 旋钮（→deck pregain）、VU 表组件（定时器读 E1.5 数组）、Fader Start 联动、Tap BPM 按钮
  - 参考：B13-4.1/4.5/4.10/4.14、MIDI（TRIM=0xB0/0x24、Fader=0xB0/0x33）
- [x] E2.6 Instant Doubles：LOAD 双按 = 把另一盘曲目复制到本盘同位置播放（含元数据/波形）
  - 参考：B13-2.1（LOAD 双按）
- [x] E2.7 LED 灯态体系：按钮 setChecked/样式表反映引擎状态（Hot Cue 亮灭、Pad 灯阵、Key Shift 灯阵、模式指示）
  - 参考：MZH-Pitch Shift Mode 灯阵表、B13-7（LED 反馈）
- [x] E2.8 表演功能键：Slip / Censor / Stutter 按钮 + 灯态（接 E1.6/E1.9）
  - 参考：B13-8（表演功能）、MIDI（reverseroll）

### E3 UI 四区布局重排

- [x] E3.1 布局重构：Browse（顶栏：LOAD/旋转选择/曲库搜索）+ 双 Deck（含 Jog/Pad）+ Mixer + Effects 四区；保留 M1 曲库表格与 Prepare/Mix 入口
  - 参考：B13-1（布局总览）、既有 ui/main_window.py

### E4 集成验证

- [x] E4.1 无头引擎探针 `.temp/probe_m15.py`：Hot Cue/Beat Jump/Key Shift/Slip/Sampler/VU/Jog/Censor/Stutter 断言
- [x] E4.2 端到端 `.temp/verify_m15.py`：全功能操作链路 + 无异常退出
- [x] E4.3 冒烟（AGENTS.md import + --version）+ GUI 无头初始化
- [ ] E4.4 提交 `feat: V0.2，完成 M1.5 FLX4 交互复刻（...）`（由用户执行）

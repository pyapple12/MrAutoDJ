# MrAutoDJ 参考仓库研读报告（w.study.md）

> 本报告逐个记录 12 个参考仓库的阅读结论：可借鉴的功能实现、文件分类规范、
> 代码规范、错误处理规范。任务清单见 `x.progress.md`。

## 报告结构

1. 每个项目一节（B1~B12），含：项目简介 / 架构 / 可借鉴点 / 规范提炼
2. 汇总章节（C1~C6）：跨项目规范归纳 + MrAutoDJ 落地建议

---

# B1 songs-automixer_python（LaRambla20 · Python/Textual TUI DJ 台）

> 与 MrAutoDJ M1 目标几乎同构：节拍匹配渐变、变速同步、主 FX、backspin、耳机预听。
> 技术栈：Python + Textual(TUI) + sounddevice + librosa + scipy + pydub + rubberband CLI。

## 架构（强烈推荐本项目照搬的分层）

```
main.py → automix/analyzer → automix/app → automix/audio_engine（单向依赖）
```

- 入口唯一（main.py），全部源码在 `automix/` 包内
- **纯逻辑与 I/O/引擎分离**：`transition.py` 是纯函数（无副作用、可单测）；`analyzer.py` 纯分析不碰播放；`stretcher.py` 是唯一调用 rubberband 的模块
- 音频约定统一：引擎 `(N,2) float32 [-1,1] @44100Hz`；分析路径单独 22050Hz mono，与引擎数组不共享

## 引擎核心（audio_engine.py）

- 一个常驻 `sd.OutputStream` + `threading.Lock`；状态机 `State(Enum): IDLE/PLAYING/MIXING`
- 回调 `_callback` 实时线程纪律：**不做任何 I/O，只读预加载 numpy，锁内操作保持短**
- `start_mix(buf, fade, scheduled_start_sample=None)`：支持**样本级精确的定时切歌**（等到指定 sample 再在同一个音频帧内切到 MIXING，无静音缝隙）——这是对拍混音的关键
- 交叉淡化用逐帧线性 `np.linspace`；MIXING 结束 `_position = _mix_pos`（而非 0）保证接续正确
- 软件音量在音频层：master `[0, 2.0]`（可 boost，输出硬限幅 ±1.0 保护音箱）；cue 音量 `[0,1]` 无 boost（护耳）
- `load_audio`：pydub 解码 → `/32768.0` 归一化

## 变速变调（stretcher.py）—— 预渲染方案的完整范本

- **证实了"离线预渲染"路线可行**：所有变速都通过 `make_transition_buffer()` 调 rubberband CLI（R3 引擎 `-3 --centre-focus`）
- 输出缓冲结构：`fade_s` 恒速 start_rate → `restore_s` 沿 smootherstep 回到 1.0 → 之后 1.0 到结尾（一次调用渲染整首余量）
- 64 锚点 timemap；坑记录：`-M` 才是 timemap 标志（`-T` 是恒速）、必须配 `-D`、首锚点不能是 (0,0)（NaN bug）
- 进度解析：rubberband 用 CR 覆盖输出，需逐字符读 stderr 按 `\r` 分块；Pass1/Pass2 权重 5/95
- 启动时 `rubberband_available()` 探测，缺失即硬失败退出（fail-fast）

## 转场规划（transition.py）—— 纯函数范式

- `plan_transition(now_bpm, next_bpm, fade) → TransitionPlan(skip, start_rate, matched_bpm, drift_beats, relation)`
- **八度折叠** `fold_ratio`：64↔128 BPM 折叠到 ~1.0，避免半速/双速误判
- 漂移模型：`drift_beats = (next_bpm/60)·|r_eff−1|·fade`；`skip = drift_beats ≤ 0.25`（一个常量 `MAX_DRIFT_BEATS` 就是整个 skip/stretch 调参点）
- `tempo_compatible()` 驱动 UI 的 `:)` 匹配标记

## 分析管线（analyzer.py）

- librosa `beat_track` + Krumhansl-Kessler chroma 调性；downbeat 启发式：4 拍相位里选 40–150Hz STFT 能量最大者（假设 4/4）
- beats/downbeats 直接以引擎采样率(44100)的样本索引存储，UI 无需换算
- **缓存版本化**：`~/.automix_cache.json` `{"version": 2, "entries": {md5(path:mtime:size): record}}`，版本不符静默重分析；坏条目用 `empty_record()` 降级而非 KeyError
- 分析失败 → `empty_record()`（bpm=0, key="?", beats=[]）静默降级，单曲失败不拖垮库

## FX（fx.py）—— 实时 DSP 纪律范本

- **系数计算与处理分离**：`butter()` 只在 setter（UI 线程、锁内）算 `_b/_a`；回调只跑 `lfilter`
- 滤波状态 `zi` 的连续性管理：小幅调节保留、切换效果/开关/重开曲目时重置（防咔嗒声）
- 4 阶 Butterworth + float64 递归（float32 biquad 在低截止有可闻底噪）；切效果自动清零旧效果
- Trans 门控：BPM 同步 50% 占空比，~2ms declick ramp，相位跨块持久化

## 双输出监听（cue_player.py）

- 第二个独立 `sd.OutputStream`，与主引擎**完全解耦**（独立锁/缓冲/播放头，无 MIXING 状态）
- PortAudioError → 回退设备采样率 + np.interp 重采样；**所有故障吞掉置 `is_dead`**（蓝牙/USB 掉线绝不能卡死主播放）

## 并发与陈旧任务防护（app.py）—— 本项目最值得学的工程点

- `_prep_epoch` 计数器：每次使 prep 失效的操作（N/P/Stop/换曲/参数改动）都 `+=1`，后台 worker 捕获启动时值，完成时比对，不一致即丢弃缓冲——**用单调 epoch 解决"过期异步结果"问题**
- `_cue_epoch`/`_loading` 同模式用于监听解码
- `call_from_thread` 是 worker 线程更新 Textual 控件的唯一安全通道
- UI 100ms `set_interval` 驱动 `_tick()`（进度/BPM 动画/延迟切换/自动混音检测）
- `_commit_mix()` 是唯一混音提交核心：手动 M 与自动混音共用，保证行为一致
- 自动/紧急混音（A 键）：纯分类器 `_emergency_decision()`（无副作用可直测）+ 每曲一次性 `_emergency_fired` 复位

## 错误处理规范（小结）

- **fail-fast**（启动期）：rubberband 缺失、采样音缺失、设备名无法解析、主监听同设备 → 打印明确错误 exit(2)
- **fail-soft**（运行期）：cue 设备丢失 is_dead、分析失败 empty_record、UI 回调异常被 `_safe_progress` 吞掉
- 错误消息全部到 `sys.stderr` 并带 `ERROR:` 前缀 + 修复指引（不只说"失败"）

## 代码/文件规范

- 包结构极简：一个包 + 一个入口 + tests + scripts（生成器）+ assets + samples
- 常量集中在模块顶部并带理由注释（如 HPF_MIN_HZ=300 解释"太低听不见"）
- 全程类型注解；内部状态 `_` 前缀；只读状态用 `@property`
- `CLAUDE.md` 堪称范本：Quick start / Keybindings / Architecture / **Key invariants（不变量清单）** / Gotchas（含 Windows cp1252 ASCII 输出、Textual 版本上限等真实坑）/ Testing 表

## 测试规范

- 不用 pytest：`tests/probe_*.py` 独立脚本，直接运行打印 `PASS`
- **无头测试模式**：`AudioEngine.__new__(...)` 跳过开流，手工设状态字段 + 合成 numpy 音频直驱 `_callback`/`_tick`——无音频设备的 CI 也能测引擎逻辑（本项目可借鉴）
- 纯函数（transition/analyzer 判定逻辑）直接断言

## 可借鉴性评分：★★★★★（M1 最高价值参考）

---

# B2 pyCrossfade（oguzhan-yilmaz · Python 离线混音引擎库）

> 144★。与 B1 不同：这是**离线批量混音库**（不是实时台），输入两首歌、输出拼接好的 WAV。
> 技术栈：numpy/scipy + madmom + essentia + pyrubberband + yodel + typer。SDK + CLI 双入口。

## 总体设计

- 库式分层：`Song`（音频+拍子数据对象）→ `transition.crossfade()`（核心算法）→ `utils`（DSP 工具）→ `config`（全部可调参数）
- `__init__.py` 公开 `__all__` 与 `__version__`；`[project.scripts] pycrossfade = "pycrossfade.cli:main"`
- 过渡输出为 4 段拼接：`master_initial → time_stretch_audio → crossfade_part → slave_remaining`，所有分段切片与索引都保留在结果里

## 对 M2（自动混音）最有价值的算法

### 1. 逐小节渐变变速（time_stretch_gradually_in_downbeats）

- 把 master 最后 N 个小节**逐 downbeat 片段**变速，因子沿 `np.linspace(1.0, final_factor, n)` 渐变
- 明确记录了 `np.linspace` 而非 `np.arange` 的原因：**arange 的浮点步进可能静默错过终点**，linspace 保证最后一片精确到达 final_factor——B1 的 smootherstep 是连续版，这是离散版

### 2. 节拍匹配对齐（beatmatch_to_slave）

- 将 master 的每个小节变速到与 slave 对应小节**等长**（ts_factor = 两小节长度比）
- 变速结果长度可能差几帧：**截断或补零到精确长度**，保证 concat 无缝

### 3. 三频 DJ EQ 交叉淡化（crossfade_eq）—— 经典 DJ 技巧

- master 低/高 shelf 渐降、slave 渐升；**双方中频在重叠中心做 dip（默认 -6dB）防浑浊**（EQ 而非音量十字交叉）
- 分步滤波（默认 20 步）逐段换系数，**滤波器状态 zi 在步间传递防 zipper noise**（与 B1 fx.py 的 zi 连续性思想一致）
- 增益曲线：`master_level = master_start*(1-t)`、`slave_level = slave_start+(1-slave_start)*t`、`mid_dip = -dip_db*sin(πt)`

### 4. 其他 DSP 细节

- `click_protect()`：拼接边界前后 3ms cosine 渐入渐出防咔嗒（离线版防 click）
- `linear_fade_volume` 支持 linear/cosine/**equal_power** 三种感知响度曲线（equal_power = 平方和恒定）
- `replay_gain_offset()`：dB→线性因子 `10^(dB/20)` 应用到整轨
- 立体声处理全部 `gains[:, None]` 广播；**绝不原地修改输入数组（返回 copy）**

## 拍点检测（song.py）

- madmom 神经网络双处理器：`RNNDownBeatProcessor`（激活）+ `DBNDownBeatTrackingProcessor`（beats_per_bar=4, fps=100）——比 B1 的 librosa 启发式更准
- downbeats 直接从 beat_num==1 过滤，`dbeats * sample_rate → 音频样本索引`（与 B1 同约定：以引擎采样率存索引）
- **注释文件持久化**：拍点注解写入 `{annotations_dir}/{song_name}.txt`，存在即跳过分析（B1 用 md5 缓存 json，B2 用文件名注解，各有取舍）

## 配置规范（config.py）—— 本项目可直接照抄的模式

- **所有魔法数字都进 dataclass**：`AudioSettings / BeatSettings / FadeSettings / EQSettings / CrossfadeSettings`
- 默认值即"合理出厂值"，每个字段带文档注释解释含义与取舍（如 gain_db=26 的用途）
- 环境变量覆盖最常调的项（`ANNOTATIONS_DIRECTORY`，为 Docker 工作流保留）
- `__post_init__` 做参数校验（len_crossfade >= 1 等，违规 ValueError）
- 高层 settings 通过组合低层 settings（`CrossfadeSettings.fade`/`.eq` 用 `field(default_factory=...)`）——**避免共享可变默认值**

## 兼容性规范

- `Transition`/`MultiTransition` dataclass 同时实现 `to_dict()` 与 `__getitem__`（dict 风格访问）——**旧 API 平滑过渡的范例**
- 函数签名保留默认参数，settings 优先（"settings 是唯一真相源"）

## 依赖/环境教训

- madmom 把项目钉在 Python 3.7 时代（`requires-python = ">=3.7"`），依赖故意不钉版本、靠 requirements.txt/Docker 锁定——**对新项目是反面教材**：选拍点方案时优先 librosa（B1 已验证 3.12 可用），madmom 作为可选增强
- essentia 全局关日志：`essentia.log.infoActive=False`

## 可借鉴性评分：★★★★☆（M2 的核心算法库，M1 的 EQ 过渡可参考）

---

# B3 automix（clawd139 · 神经扩散模型自动转场）

> 研究型项目：用条件扩散模型预测"DJ 动作参数曲线"，经**可微效果链**渲染转场。
> 技术栈：PyTorch + torchaudio + demucs + librosa + click + uv。MIT。

## 核心思想（对 M2 的概念启发）

- **把 DJ 动作参数化**：每首曲的每个 stem（drums/bass/vocals/other）×6 参数（gain、EQ 低/中/高、LPF、HPF）+ 全局 3 参数（reverb send、delay send、delay feedback）= 每帧 54 参数
- 扩散模型生成参数曲线 → 可微混音器执行 → 输出转场音频（end-to-end 可训练）
- `ParameterParser`：扁平张量 ↔ 结构化 dict 的解析（布局常量集中定义并有文档注释）

## 对 M2 直接可用的成果

### 1. SimpleCrossfader 基线（fade 曲线库）

`fade_type ∈ {linear, equal_power, exponential, logarithmic}`，其中：

- equal_power：`cos(πt/2)` 出 / `sin(πt/2)` 入（感知响度恒定）——与 B2 的 equal_power 一致
- 支持 cue_in/cue_out 区间裁剪——本项目 M1 的 crossfader 直接照抄此数学

### 2. 频域 DSP 技巧（DifferentiableEQ/LPF/HPF）

- **软掩码**：用 sigmoid 在频率域做带划分/滤波（`-（log_freqs−log_cutoff）/(tw/4)`），过渡平滑、可导
- **对数频率映射**：归一化 cutoff 0-1 → `2^(log_min + t·(log_max−log_min))`，音乐响应（与 B1 fx.py 的 log 扫描同思想）
- 曲线插值：`F.interpolate(linear)` 把 n_frames 控制点曲线插到采样长度
- gain 加 `avg_pool1d` 平滑防 zipper
- 输出 `torch.tanh` 软限幅防爆音

### 3. 曲目结构分析（pipeline.py analyze_audio）

- RMS 能量归一化 → 阈值分段：**intro(0.3) → drop(0.7) → breakdown(0.3)** 状态机（对 M2 的"能量曲线"和 M3 报幕都有用）
- BPM/beats + Krumhansl chroma 调性（与 B1/B2 同套路，实现更简：`np.roll` 相关）
- 分析异常：`analysis["error"]` 字段记录 + 降级默认值（128BPM/C大调）

### 4. 数据管线规范（process_track_library）

- 合成训练数据：取 A 尾部 60s + B 头部 60s，`cos(πt/2)`/`sin(πt/2)` 十字交叉——"真人转场不够用就用合成"的思路
- 目录结构约定：`{pair_id}/track_a_stems/{drums,bass,vocals,other}.wav + transition.wav + analysis.json`（**JSON 即数据 schema**）
- 幂等：已存在 analysis.json 的 pair 跳过（断点续跑）
- 并行：ProcessPoolExecutor + GPU sharding；临时目录用完清理

## 工程规范

- uv 管理 + hatchling 构建；pyproject.toml 完整（classifiers、URLs、black/isort/mypy/pytest-cov 全配好，dev/training/all extras 分层）
- `[project.scripts] automix = "automix.cli:main"`（click）
- 设备自动检测：cuda → mps → cpu，写成一个函数复用
- `log()` 统一带时间戳，控制台+文件双写（数据管线的日志规范）

## 错误处理规范（数据处理场景）

- 音频加载**多重 fallback**：torchaudio(wav) → librosa(mp3) → torchaudio 兜底
- 外部进程（demucs）：30 分钟超时、FileNotFoundError 提示安装、任何异常 log 后返回 None——**批处理绝不因单条失败中断**（与 B1 fail-fast 相反：批处理场景 fail-soft 是正确选择）
- 可选依赖降级：librosa 缺失时打印 WARNING 并走 fallback 逻辑

## 可借鉴性评分：★★★☆☆（概念参考价值高，M2 远期；SimpleCrossfader 曲线与结构分析可直接用）

---

# B4 cuekey（Supercarlillos · DJ 曲目分析管线，macOS）

> 免费 DJ 分析工具：调性（Camelot/Open Key）、BPM、能量 1-10、自动 CUE 点，含 rekordbox 集成。
> 技术栈：librosa + numpy + SQLite + click + rich + pywebview。`src/` 布局，PolyForm 许可。

## 分析管线结构（analyzer.py）—— 本项目 M1 分析子系统的范本

- `analyze_file()` 顺序串起：`detect_tempo → detect_key → detect_energy → detect_cues`，每个分析器一个独立模块（`analysis/` 子包），结果聚合成一个 `TrackAnalysis` dataclass
- 回调式批量接口：`analyze_many(paths, on_result, should_stop)` —— 结果到达即回调，支持取消/暂停（M1 加载大曲库时照抄）

## tempo.py —— 目前所见最讲究的 BPM 检测

| 函数                  | 作用                                                                                                                                       |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `fold_bpm`            | 折半/加倍进 70–180 DJ 合理区间（180 含边界）                                                                                               |
| `refine_bpm`          | 用拍子间隔中值重估 BPM：**剔除偏离中值 20% 的间隔**（漏拍/错拍），均值倒数比 tempogram 粗量化精确                                          |
| `snap_bpm`            | 吸附到整数/半整数（DAW 曲目精确拍速；离群保留原值）                                                                                        |
| `pick_metrical_level` | **修正节拍级误锁**：3:2、倍频、4:3 候选×自动相关打分 + Ellis 2007 对数正态先验（中心 125 BPM，鼓励俱乐部拍速），仅当显著更优才切换（防抖） |
| `track_beats`         | **纯 numpy 的 Ellis DP 拍子追踪器**（避开 librosa 的 numba 内核在冻结 app 中段错误的问题）                                                 |
| `local_maxima`        | 纯 numpy 局部极大值掩码                                                                                                                    |

## key.py —— 调性检测的稳健做法

- **先 `librosa.effects.harmonic()` 分离谐波分量**再算 chroma（鼓/打击乐会污染音级分布）
- `chroma_cqt(..., tuning=0.0)`（跳过 estimate_tuning 的 numba）
- **对时间取中位数**（对瞬态/噪声稳健，比均值好）
- 24 键 Pearson 相关（KK 谱），**confidence = 最佳与亚军差距归一化**

## energy.py —— 1-10 能量评分（M2 的"能量曲线"直接可用）

- 加权启发式：响度(90% 分位 RMS→dB，-28~-8dB 映射)40% + 强 onset 密度 25% + 低频占比(≤160Hz)20% + 拍速 15%
- 纯启发式、无模型、每项都注释理由——"可解释的 DJ 元数据"设计思路

## cues.py —— 自动 CUE 点（M1"自动打点"功能）

- MFCC(13) + chroma 特征 → 行归一化 → librosa 聚合聚类分段 → 段边界 = 结构变化点（intro/drop/breakdown/outro）
- **边界吸附到最近 downbeat**（落在节拍网格上）；尾部 5s 内忽略；最小间距 8s 去重；最多 8 个

## camelot.py —— 纯领域模型范本

- `Key(pitch_class, mode)` frozen dataclass，`__post_init__` 校验；一个数据对象同时输出 standard/camelot/openkey 三种记谱
- `wheel_number = (tonic*7+7)%12+1` 注释清楚（五度圈）；`parse_key()` 容错解析

## cache.py —— SQLite 分析缓存（比 B1 的 JSON 更优）

- 表 `analysis(path PK, size, mtime_ns, version, has_cues, payload)`
- **有效性三重校验：文件 size + mtime_ns + ANALYSIS_VERSION**（算法升级自动失效，版本号有注释变更史）
- payload 为 JSON 序列化的领域对象；解析异常返回 None（降级重分析）
- 缓存目录可用环境变量覆盖（`CUEKEY_CACHE_DIR`）→ 本项目可移植为 `MRDJ_CACHE_DIR`

## 批量并行分析（analyzer.py）—— 工程上最值得抄的部分

- **进程池而非线程池**（librosa CPU 密集，GIL 下线程会串行）；`spawn` 上下文；worker 数 = 核数-2 且受内存限制（每 worker ~2GB）
- **numba 缓存隔离**：多进程并发写共享 NUMBA_CACHE_DIR 会损坏缓存 → 每进程 `tempfile.mkdtemp` 私有目录（实战坑的代码化）
- `max_tasks_per_child=16` 定期回收 worker 防内存爬升
- **crash 隔离重试**：`BrokenProcessPool` 时重建池，单文件崩溃记日志并报告，多文件崩溃进 quarantine 逐个隔离重试（重启上限 10+len/25）
- `faulthandler.enable` 到日志文件（原生崩溃追踪）；`CUEKEY_TEST_CRASH` 测试钩子模拟 worker 崩溃
- 失败哲学：**批处理里一条坏文件绝不能杀死整批**（与 B1 单曲 fail-fast 形成互补）

## 文档/发布规范

- 完整社区文档集：README + CONTRIBUTING + CODE_OF_CONDUCT + CHANGELOG + DONATE
- pyproject：CLI 与 GUI 双入口（`project.scripts` + `project.gui-scripts`）、classifiers 精确、dev extras
- 打包目录 `packaging/`（PyInstaller 图标等，冻结 app 的坑都在代码注释里）

## 可借鉴性评分：★★★★★（M1 分析管线 + 并行批处理 + 缓存 + Camelot 领域模型全可抄）

---

# B5 ai-remixmate（Chunduri-Aditya · AI 混音全栈，读核心）

> 实时 DJ 引擎（Python 分析 + React 前端 + FastAPI 后端）：双歌分析 → 样本级下拍锁定 →
> 变速对齐 → stem 感知转场（人声分离）→ LUFS 母带。仓库分 `ai_remixmate_feature_lab/`
> （本报告核心）与主应用。MIT。

## 对 M2 最值钱的成果

### 1. 多维兼容性评分系统（compatibility.py）—— 直接可用

- **BPM 兼容**：先倍频归一化（目标/源折进 [0.67, 1.5]），`score = clamp01(1 - |Δ%|/16)`，>8% 出 warning
- **Camelot 调性**：同键 1.0 → 关系大小调 0.92 → 相邻 0.85 → +2 能量推进 0.72 → 远距 0.35，每个关系带说明文案
- **能量曲线兼容**：两曲线重采样到同一长度后逐点差均值
- **音色兼容**：余弦相似度映射到 0-1；**人声冲突风险**：两轨人声活跃度乘积
- 综合分：bpm0.30 + key0.25 + energy0.20 + timbre0.15 + (1-vocal)0.10
- **每个子评分统一返回 `{score, explanation[], warnings[]}`** —— AI 选歌"可解释"的规范（M2 的选曲建议可以直接照这个结构做）

### 2. 确定性转场规划（transition_plan.py）

- 转场长度以**小节**为单位：`transition_sec = bars × beatsPerBar × (60/bpm)`
- 退出点 = "最接近但不晚于 目标退出时刻 的下拍"；入场点 = 来曲第一个下拍
- 输出 CUE 建议（mix_out/mix_in）、loop 建议（量化 4 拍）、EQ/滤波自动化**文字建议**（"Reduce outgoing low EQ before bass swap"）——规则可读、可给 LLM 当提示词

### 3. 贪心自动编排（automix.py）

- 26 行实现：从曲池反复选"与当前曲兼容分最高"的下一首，链式生成转场计划，`totalConfidence = 平均分`——M2 最简可行的自动 Set 算法

### 4. 主应用架构（AGENTS.md 记录）

- **beat-grid lock**：`entry_sample_b = int(entry_time_b * sr / stretch_ratio)`——样本级校正（±半小节钳制），B1 用 scheduled_start_sample 是同一思想的实时版
- **stem 感知转场**：Demucs 分离后 bass 用专用余弦渐变斜坡；其余 stem 按相似度评分渐变；动态 EQ：A 低架下降同时 B 上升防低音冲突
- **embedding 索引**：35 维 numpy 向量（BPM/key/energy/频谱特征），JSON 持久化、无外部向量库，`/library/similar/{name}` 返回 k 近邻
- **作业队列规范**：SQLite write-through + 内存 dict（O(1) 读）、任务 ThreadPoolExecutor、写接口一律 `202 + {job_id}`、SSE 推送进度、重启把 RUNNING 回滚为 FAILED、`DELETE /jobs/{id}` 取消
- 配置三级覆盖：`config.yaml → config.local.yaml → env(REMIXMATE_<SECTION>_<KEY>)`，密钥只进 gitignored 的 local

## JSON Schema 契约规范（schemas/ 目录）—— 强烈推荐

- 15 个 schema 文件定义全部领域数据结构：`trackAnalysis / beatgrid / compatibilityScore / transitionPlan / remixRecipe / automationLane / stemManifest / cuePoint / loopState / mixerState / effectState / deckState / exportManifest / trainingEvent / modelRegistry`
- 每个 schema 严格 `additionalProperties: false` + `required` + 字段描述（如 automationLane 的 points 必须按 timeSec 升序）
- 用法：**Python dataclass 与 TypeScript 模型与 schema 三方对齐**（AGENTS.md 明确规定）——跨语言/跨模块的契约文档，本项目单语言也可用（dataclass ↔ schema 校验）

## 工程规范要点

- AGENTS.md 是"AI 协作型仓库"的模板：架构图 + 设计决策（带日期修正记录）+ API 表面表 + 常见任务步骤（加端点/加页面的 checklist）+ Gotchas + Agentic 规则（读后改/计划先行/验证循环/依赖审计/自愈≤3 次）
- 可选依赖**延迟导入**：librosa 在函数内 import，缺失 raise 明确 ImportError；测试用 `@pytest.mark.dj_analysis` 自动跳过 librosa 依赖用例
- 数据缺失降级：缺 key/能量曲线用"中性分 0.5 + warning"而非崩溃

## 可借鉴性评分：★★★★☆（M2 兼容性评分/转场计划/贪心编排可直接移植为 Python 模块）

---

# B6 dj-track-similarity（MeteorBurn · DJ 曲库相似度工作台，读核心）

> 本地优先的 DJ 曲库工作台：多模型（SONARA/CLAP/MERT/MAEST）嵌入索引 + 混合检索 + Set 规划 + 音质工具集。
> 规模很大（80+ 模块），重点读：日志系统、Set 排序约束、证据融合、AGENTS.md 工程纪律。

## 日志规范（logging_config.py）—— 本项目日志系统的天花板范本

- 文件 + 控制台双通道：文件格式带 logger 名，控制台精简；`FILE_LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(name)s %(message)s"`
- **启动按日期滚动**：从日志头解析开始日期（或 mtime），跨天自动归档 `xxx.log.YYYY-MM-DD`，保留 backup_count=1
- **stdout/stderr 镜像**：`StandardStreamLogMirror` 包装 sys.stdout/stderr，把 print 内容按行写进文件日志（stdout→INFO、stderr→WARNING）——**任何第三方库的 print 都进日志**
- asyncio 异常处理器：事件循环未捕获异常记 error + 调用链；**Windows 传输重置（10054）特判为 info 不刷屏**（`_is_windows_transport_reset`）
- `log_failure()`：error 记一句 + debug 记完整堆栈——"用户看 error，开发者看 debug"
- 环境变量配置：`DJ_TRACK_SIMILARITY_LOG / _LOG_LEVEL / _LOG_TRACK_EVENTS / _ANALYSIS_DIAGNOSTICS`
- 全库日志用 `logging.getLogger(__name__)` 命名空间（模块名即 logger 名）

## Set 排序的真实约束（set_sequence.py）—— M2 直接可抄

- 约束：同艺人每 Set 最多 1 首（`ARTIST_SET_MAX_TRACKS = 1`）、**不允许与上一首同艺人**、艺人数量压力分
- `duplicate_key()`：artist|title casefold 去重（空则用文件名）—— 排 Set 前先去重的工业做法
- 用 `Protocol` 定义候选接口（而非具体类）——测试友好

## 证据融合模式（tempo_resolution.py）

- **多证据源加权**：模型分析值（SONARA）与曲库标签并列，`TempoEvidence{bpm, alternatives, confidence, grid_stability, reliability, source}`
- 置信度感知评分：`reliability × 实测匹配 + (1-reliability) × 中性分`——证据弱时平滑回退中性值（0.5）
- 输入参数强校验：identity/type 不匹配直接 TypeError/ValueError（**防御式 API 设计**）

## 转场诊断系统（hybrid_transition.py / transition_diagnostics.py）

- 每次转场候选都产出**可解释诊断**：组件权重**版本化**（`V2_COMPONENT_WEIGHTS`）、按支持种子逐对计算再取均值、风险版本（risk_version）驱动——"每次推荐都能说清为什么"的工程化
- `Protocol + TypeAlias` 定义接口；诊断 JSON 可序列化（JsonValue）

## AGENTS.md —— 工程纪律范本（比代码更有价值）

- **安全基线**（可操作的安全规范）：源音频只读（扫描/预览/分析一律不修改文件）；SQLite 写必须走封装层 + WAL/busy 策略；破坏性维护先备份；启动不静默改旧库结构
- **dry-run-first / report-first**：Audio Doctor 先只报告、apply 需显式确认+备份+失败回滚；Dedup 同理
- **验证路由**：按变更类型选择最便宜的有效验证（文档只 diff 检查；后端跑聚焦 pytest；前端 typecheck；模型/音频测试用临时 fixture 绝不碰真实曲库）
- "可执行源码优于散文"（pyproject/tests/schemas 是权威）；主张一个真相源、不保留兼容别名

## 其他

- 前端 DESIGN.md：设计 token 化（`--app-bg/--surface/--accent`），禁用裸色值；缺失模型分析渲染为非阻塞空态而非弹窗
- 工具集模式：audio-dedup/audio-doctor/rhythm-lab 每个是独立子包（`tools/{x}/{x}/`），共享 pyproject 与测试

## 可借鉴性评分：★★★★☆（日志系统与工程纪律满分，Set 约束直接可用；主体架构对 M1 过重）

---

# B7 radio-dj（johncrash64 · Go 单二进制 24/7 AI 电台）

> 一个 ~9MB 的 Go 二进制跑完整电台：曲库选曲 + LLM DJ 报幕（intro/时间/真实天气/冷知识/点歌致谢）+ Icecast MP3 推流 + PWA 界面。48★。MIT。

## 电台大脑：LLM 导演模式（dj.go）—— M3 的核心架构

- **一次结构化调用规划一个 tanda（一组曲）**：输入 `Ctx{talk 旋钮, time_of_day, 历史曲目, 候选曲目, 点歌请求}`，输出 `Plan{setlist: [索引], breaks: [{before: 位置, kind: intro/trivia/wiki/station/time}]}`
- **系统提示词模板化**：站名/地点/当前时间/时段词全部注入（`d.p.Sub("system", {...})`）；时段词查表（dawn/morning/afternoon/night）——**防止模型按自己时区把下午说成 night**（真实踩坑）
- **JSON 模式 + 提取安全网**：`response_format=json_object` 仍可能被模型包进 prose/代码围栏 → `extractJSON` 取第一个平衡 `{...}`；计划**逐项校验**（空 setlist/索引越界）后错误回退
- **确定性回退**：LLM/网络任何失败 → 随机选曲，**电台绝不静默**（fail-safe 的终极形态——M3 必须如此）
- 口播限 `max_tokens=160`（一句话短）；规划 call 用 1200

## 提示词与本地化（i18n/）

- **全部口播文案进 JSON 语言包**（en/es）：system persona、intro/midroll/request_ack/weather_ok/weather_fallback/wiki 每种话术一个 key，`{placeholder}` 替换
- WMO 天气码 → 语言无关类别（clear/clouds/fog/rain…）→ 本地化措辞

## 可编辑技能（skills.go）—— M3 报幕定制的最佳实践

- 口播段落的提示词以 `.md` 文件存 `~/.radio-dj/skills/`，**首次启动从内置种子拷贝，用户直接改文件换口味（无需重编译）**
- Segue 轮换：station-id → time → weather → curiosity → wiki
- **时序细节**：报时段延迟到"播出时刻"才生成（producer 先跳过，consumer 在 air-time 调用）——防止播出的钟点过期（M3 同样要注意）

## TTS 抽象（tts.go）—— 直接用

- 声明式 catalog：`Provider{edge-tts/piper/say} + Voice{ID, Label}`，UI 渲染下拉，用户不用手写命令
- `BuildCommand` 生成 shell 命令，**text/outFile 全部 shell 引用转义**（`quote()`）
- **所有 LLM 输出经 `stripEmoji`**（emoji 会被 TTS 念出来/乱码）——M3 必须加这步

## 外部服务降级

- 天气：Open-Meteo（免费无 key）→ API 失败走 `weather_fallback` 泛化文案（`ok=false` 分支）
- 播报失败静默空文本（`Say` 返回 "" 时不播出）——绝不因一句话卡死电台

## 其他工程点

- `internal/` 包划分：dj（LLM）/ skills（段落）/ tts / icecast（推流源）/ supervisor（icecast 进程管理）/ library / status（PWA UI+API）/ install（launchd/systemd/OpenRC 服务化）
- 配置：`~/.radio-dj/config.json` + 环境变量（RDJ_* 前缀）；首次运行 onboarding 向导
- 说话压音乐：`sidechaincompress`（sidechain 压缩让 DJ 说话时压低音乐——硬件调音台风格）
- Go 项目另有的优势（单二进制/低内存 ~30MB）对 Python 不适用，但**架构模式完全可移植**

## 可借鉴性评分：★★★★★（M3 的 LLM 导演 + 可编辑技能 + TTS 目录 + 确定性回退，全部可移植）

---

# B8 writ-fm（keltokhy · Python 24/7 AI 网络电台）

> 379★。5 个 AI 主持人 × 8 档节目、多电台实例（WRIT/KLOD/CDEX-FM）。Claude 写稿 + Kokoro TTS 渲染 + ezstream/Icecast 推流 + 网页界面。Python（mac 目录为主）。

## 内容生成管线（content_generator/）

- **两段式**：Claude CLI 生成讲稿 → TTS 渲染音频（输出 `output/segments/` 由 feeder 按节目表播放）
- 7 种长段落（deep_dive 深度话题/新闻分析/模拟采访/双主持对谈/讲故事/听众来信/music_essay）+ 3 种短段落（station_id/show_intro/show_outro），**每类有独立的提示词模板与字数目标**（`SEGMENT_WORD_TARGETS` 定义 min/max）
- **质量闸门**：字数低于 80% 目标 → 拒绝重生成（`run_generation`）；TTS 失败重试一次
- 多声轨：panel/interview 用正则切分 `HOST_A:/HOST_B:/GUEST:` 标记，每个说话人独立语音渲染后带 0.3s 间隙拼接

## 主题管理与防重复（TOPIC_POOLS + select_topic）—— M3 防复读范本

- 15 个主题池 × 每池 15+ 选题（内建）+ 站方运营者扩展池（merge_topic_pools）
- **防重复三重**：① `_matches_avoid` 关键词排除 ② show 日志（JSONL）记录近期已播 → 过滤 ③ 全池轮过之后走 **LRU（最久未播优先）** 而非随机
- 选题 slug 提取用于文件名，`slot_topic_slugs` 阻止同档期重复

## 节目记忆（ledger / show log JSONL）

- 每次生成追加一行 JSON（日期/类型/主题/摘要）→ 注入规划器提示词："已覆盖，不要重复"
- **关键注释**（真实教训）：show log 不注入单段提示词——因为"最近主题列表"会变成模型的"建议银行"（跨批次锚定），改由 select_topic 在池层面过滤
- 听众消息：真实消息文件（JSON）过滤"hi/hey"类无效消息、按已读排序，注入段落到提示词

## 编排器（context.py / operator brief）

- 每档节目先让 Claude 生成结构化计划（JSON 数组：type+topic+note），再逐段生成并携带"EARLIER IN THIS EPISODE"上下文维持主线
- **Operator Brief**：把站情（当前节目/后续档期/主题池/活跃线索/听众事件/日记）汇总成文本给 operator agent，意图卡（intent card）字段化（mode/intent/avoid/use_threads）
- TYPE_ALIASES 归一化 Claude 的段类型命名错误（"deepdive"→"deep_dive"）

## 多实例与进程管理

- `writ` CLI（tmux 管理）：每站独立 station_config（mount/API 端口/agent 类型）、独立输出/队列/日志目录
- 3 种 TTS 引擎可插拔（kokoro 默认/chatterbox 克隆音色/voxtral 多语），每引擎独立 venv 隔离 PyTorch 依赖，配置里 per-engine 音色映射
- 并发控制：`fcntl.flock` 文件锁串行化 TTS 重活；daemon 脚本 + launchd

## 对 M3 的价值

- 把"电台内容"提升到**节目策划**层：主持人人设（persona.py）、节目主题聚焦、段落类型体系、编辑记忆——比 radio-dj 的"单曲间报幕"更进一层
- 文本先于音频：脚本存 JSON 元数据（scripts_dir），音频文件命名 `{seq}_{type}_{topic}_{ts}.wav` 可解析
- 质量闸门/重试/LRU 防重复/多实例配置——M3 可以直接复用

## 可借鉴性评分：★★★★☆（M3 的内容策划体系 + 防重复 + 质量闸门；代码偏 macOS 单机脚本风格）

---

# B9 mixx-dj-mcp（sandraschi · LLM 控制 Mixxx 的 MCP 服务器）

> FastMCP（Python）服务器，把 Mixxx 的 OSC 控制对象（CO）封装成 40+ 个 MCP 工具，
> 供 Claude/Cursor 等 LLM 直接操控 DJ 软件。含 Web UI、REST、Tauri/NSIS 桌面壳。

## 架构（对 M3 控制层就是现成蓝图）

```
LLM (Claude/Cursor) ⇄ FastMCP server ⇄ OSC UDP bridge ⇄ Mixxx（11118/11119 端口）
```

- `bridge/protocol.py`：**OSC 地址映射表集中管理**——所有 `/deck[N]/...` 地址与 Mixxx 内部 Control Object 一一对应，带完整注释文档（哪些是 Mixxx→外发状态、哪些是外→Mixxx 命令）
- `bridge/osc_bridge.py`：UDP 桥，`get_bridge()` 单例
- `server.py`：FastMCP 注册 + FastAPI（REST/SSE）+ CORS（为 Tauri WebView）

## 工具设计规范 —— 本项目 M3 照抄

- **Portmanteau 模式**（一词多义工具）：每个领域一个大工具 + `operation: Literal[...]` 枚举，如 `mixx_deck(operation="play_pause|stop|load|cue_set|loop_beat|rate_set|sync_enable|hotcue_activate|keylock|seek|scratch|quantize|video_enable", deck, value, ...)`
  - 为什么：LLM 工具调用时，**宁可一个入口多参数，也不几十个小工具**（减少 LLM 选错工具的概率、方便参数补全）
  - `Literal` 枚举即工具文档——IDE/LLM 自动提示合法值
- **统一返回结构**：`{"success": bool, "message": 人话, "data": {...}}`——LLM 能直接读懂并复述
- **错误返回带恢复建议**："track_path required for load operation"（缺参提示），"Unknown tool: xxx"
- 参数校验：必填参数缺失返回 `success: false` 而非抛异常；数值钳制（`max(1, min(64, beats))`）
- 参数命名直白：`enable`/`beats`/`hotcue`/`value`，docstring 标注"PORTMANTEAU PATTERN" + SUPPORTED OPERATIONS 列表 + Examples

## 工具域划分（tools/ 一域一文件）

`deck_control`（播放/走带）、`mixer`（横推/EQ/监听）、`effects`（效果链）、`library`（曲库搜索/加载）、`stems`（人声分离）、`transitions`（AI 转场建议）、`set_sequencer`（AI 编排 Set）、`smart_crate`（LLM 建 crate）、`vinyl`（DVS 校准）、`controller`（USB 硬件检测）、`skin_manager`、`daw`（导出）、`recording`、`history`、`ai_dj`、`analyzer`、`prefab_cards`（UI 状态卡）
→ **M3 控制面设计：deck/mixer/effects/library 四个域 + 状态回读，直接映射**

## 双入口

- MCP（LLM 用）：`register_all_tools(mcp)` 批量注册
- REST（Web UI/脚本用）：`tool_dispatch.py` 从 MCP 注册表**反射出 dispatch dict**，REST 调 `dispatch_tool(name, args)`——**一个实现、两个入口**（M3 可复用：控制接口只在 MCP 层写一次）

## 工程规范

- AGENTS.md 极简实用：端口表、常用命令（uv sync/just lint/uv run pytest）、关键文件表（每个文件一句话用途）、**Standards 段**（FastMCP 版本、返回结构、错误带恢复建议、CORS 配置）
- 配置：`MixxConfig.from_env()`（环境变量驱动）
- 测试：`uv run pytest tests/ -q`；lint：ruff（justfile）

## 可借鉴性评分：★★★★★（M3 控制层的直接模板：portmanteau 工具 + 统一返回 + OSC 映射表 + 双入口）

---

# B10 claudio（hllqkb · 私人 AI 音乐电台，TypeScript）

> 46★。AI 音乐电台：Claude 生成歌单 + DJ 口播词 + Fish Audio TTS，网易云音乐源。
> pnpm monorepo：apps/server（Fastify + TS）+ apps/web（React 19 + Vite + PWA）。MIT。

## 核心链路（plan.ts + plan-enrich.ts）—— 本项目 M3 的核心概念验证

```
用户意图 → context.buildContext() → claude.generatePlan() → 混合队列(歌曲/TTS/静音)
        → enrichPlanItems（song→NCM搜索取URL；tts→TTS合成URL）→ 播放器顺序执行
```

- **"计划 = 混合物品队列"**：Claude 输出 `items[]`，每项类型是 `song | tts | silence`——歌、口播、留白在一个队列里按序播放。**这正是 M3 需要的播放模型**（B1 的"下一曲+转场"升级为任意物品序列）
- 计划参数 zod 校验：`trigger: manual|auto|scheduled`、`maxSongs 1-20`、`withDj`、`scene`（场景：专注/低落等）
- 计划生命周期事件（WebSocket 广播）：`plan_started → plan_finished → queue_updated`
- **enrich 步骤**：LLM 给"查询词"（song.query）而不是歌曲 ID——**用搜索词解耦 LLM 与音乐源**，换源（网易云→本地库）只改 enrich 实现

## 上下文构建（context.buildContext）

- 输入 + scene（场景标签）→ 组装给 Claude 的上下文（含当前播放/历史/用户输入/场景）
- DJ 人格是**独立 markdown 文件**（config/agent.md）：「你是 Claudio…DJ 口吻，轻松有趣，中英混搭；用户说下一首直接执行；情绪低落推荐舒缓音乐」——人格/行为准则与代码分离，改人设只改 md

## 前端交互设计（M3 的 UI 参考）

- 6 种音频可视化（AudioSpectrum/AudioVisualizer/SpectrumBars…）、KaraokeLyrics 歌词滚动、DjMessages（DJ 消息流）、ChatArea（与 AI DJ 对话侧栏）、IntentInput（自然语言点歌输入框）
- MediaSession API（锁屏/耳机控制）、PWA、i18n 中英双语、深浅主题、播放历史/统计（top artists/分钟数/收藏）
- 音频封装：`AudioPlayer.ts`（HTMLAudioElement wrapper）统一队列/进度/错误

## 工程规范

- CLAUDE.md 中文书写、简洁：架构一句话 + 常用命令 + **Code Standards**（TS strict、4 空格缩进、Zustand 状态、Conventional Commits、分支模型）+ 目录说明 + **Known Gaps（明确列出的已知缺口）**——"诚实文档"文化
- 服务层划分清晰：services/（ncm/claude/tts/weather…）与 routes/（薄路由）分离，app.services 注入
- 状态：Zustand（playerStore）；实时：WebSocket（now_playing/queue/DJ messages）
- 一键启动脚本 start.sh（自动清理旧进程、Ctrl+C 全停）

## 可借鉴性评分：★★★★☆（"混合物品队列 + 搜索词解耦 + 人格 md 文件"对 M3 极有价值；整体为 TS 需移植）

---

# B11 wrzdj（wrzonance · DJ 点歌台全栈，读核心）

> 点歌管理系统五件套：FastAPI 后端（SQLAlchemy 2.0 + PostgreSQL + Alembic）+ Next.js 仪表盘 +
> Node.js 设备桥（Denon/Pioneer/Serato/Traktor 插件化）+ Electron 桥 UI + 树莓派 Kiosk。9★。

## 点歌状态机（M3 点歌互动直接照抄）

- `NEW → ACCEPTED → PLAYING → PLAYED` / `NEW → REJECTED`（可重开）
- **状态机强制**：非法迁移返回 400（`NEW → PLAYED` 不允许）
- **单活跃播放约束**：每场活动只有一首 PLAYING，新曲转 PLAYING 时自动把上一首归档为 PLAYED（`clear_other_playing_requests()`）
- 手动 Mark Playing 同时写 NowPlaying 表（kiosk 显示）；设备桥自动检测的曲目覆盖一切手动状态
- 投票：幂等 + 原子自增（`vote.py`）

## LLM 网关（LLM-PLUGIN.md）—— M3 的 LLM 抽象层范本

- **适配器插件架构**：`LlmAdapter` ABC + registry + 类型化错误契约，第三方适配器放 `LLM_PLUGIN_DIR/` 即插即用
- 调用链：`Gateway.dispatch(db, actor, request, purpose)` → 解析连接器（per-DJ 最近使用 → 组织默认）→ adapter 翻译请求/响应 → **provider 错误映射为类型化 `LlmError` 子类** → 记录调用日志 + 回退策略
- 工具翻译：JSON-Schema `ToolSpec` → 各 provider 的 tool/function 形状（`tool_translation.py`）
- 内置适配器：OpenAI API Key / OpenAI-compatible（Ollama/vLLM/LMStudio）/ Anthropic SDK
- **凭据管理**：`EncryptedText` 列加密存储（无环境变量路径！），`LlmCallLog`/`LlmAuditEvent` 审计

## 推荐引擎（recommendation/）

- 多阶段管线：profile → search → score → dedupe；`scorer.py`：BPM 兼容、调和混音、流派亲和、**艺人多样性惩罚**；`camelot.py`（含半速/双速）
- `mb_verify.py`：**MusicBrainz 验证检测 AI 生成的填充曲目**（防 LLM 推荐不存在的歌）——M3 防幻觉的好办法
- LLM 调用强制 `tool_use` schema

## 安全与限流规范（M3 若做 Web 面直接抄）

- 角色三档：admin / dj / pending（待审批）；`deps.py` 三个鉴权依赖；自注册限速 3/min + Cloudflare Turnstile 人机验证
- 全局错误处理器：**生产环境一律泛化 500，防 token/凭据泄露**
- slowapi 限流 `@limiter.limit("N/minute")`；kiosk 配对码（排除 O/0/I/1 的 6 字符）+ 64-hex session token + 5 分钟 TTL
- 登录锁（lockout.py）、安全头（security_headers.py）、CSV 注入防护（csv_safe.py）、banner 图片路径穿越防护（`Path.is_relative_to`）
- 系统设置存 DB 单例（非环境变量）——管理员可运行时开关注册/验证/集成

## 数据库迁移规范

- Alembic 版本 001→046 完整演化史（OAuth token 加密迁移、时区修复、外键清理…）——**数据演进的教科书式记录**

## 可借鉴性评分：★★★★★（M3 点歌状态机 + LLM 适配器网关 + 安全规范 + 推荐管线全可移植到本项目）

---

# B12 mixxx（mixxxdj/mixxx · C++/Qt 顶级开源 DJ 软件，只读核心）

> 7010★。唯一"完全开源 + 长期活跃 + 三平台 + 硬件支持完善"级别的完整 DJ 软件。GPL-2.0。
> 本次只读架构核心：AGENTS.md、src/engine（engine/mixer/xfader/channelmixer）。

## 核心架构（AGENTS.md 提炼）

- **ControlObject / ControlProxy**：`[Group], key_name` 的全局控件对象——所有组件（UI/控制器/引擎）通过命名 CO 通信，**松耦合的架构基石**（M1 的"指令总线"就是它的简化版）
- **Engine 线程纪律**：实时音频线程**零分配、零锁、可发信号但不可收信号**（Qt 信号不能反向进入音频线程）
- `parented_ptr`：Qt 对象树所有权管理

## 引擎结构（src/engine/）

- `EngineMixer`：主混合器，注册 64 路预分配通道（`kPreallocatedChannels=64` 防运行期分配）；`process(bufferSize)` 由 SoundManager 单线程调用
- 通道体系：`enginechannel.h` 基类 → `enginedeck`（DJ 盘）/ `engineaux`（辅助）/ `enginemicrophone`（麦克风）/ preview deck
- `enginebuffer`：单曲引擎（seek/loop/rate/keylock/scratch/position 全在 CO 上）
- `enginexfader`：横推算法——**常量功率（CONSTPWR）与加法（ADDITIVE）两种曲线 + powerCalibration + transform**（M1 的横推直接参考：等功率曲线+校准）
- `channelmixer.cpp`：信号流注释清晰——清空输出 → 逐通道算增益 → 过效果 → 混入输出；**GainCache 记录 oldGain/newGain/fadeout 实现渐变（无咔嗒）**
- `enginetalkoverducking` + `enginesidechaincompressor`：**说话压低（sidechain 压缩）在引擎内实现**（radio-dj 用 ffmpeg 命令做，mixxx 是引擎原生能力）
- `engineworker`：引擎侧任务调度（波形渲染等）不阻塞音频线程

## 其他值得抄的点

- `soundio/`：音频设备管理；`controllers/`：MIDI/OSC/HID 映射体系（JS/XML 脚本）
- `waveform/`、`rendergraph/`、`shaders/`：GPU 波形渲染
- `util/`：`samplebuffer`、`SampleUtil`（内存对齐的音频工具）、`parented_ptr`、`timer`（ScopedTimer 性能探针）
- `test/`：引擎级单元测试与集成测试（QtTest）
- 真实项目纪律：.clang-format/.clang-tidy/.pre-commit、codespell、Doxyfile 文档、多语言翻译（.tx）

## AI 协作政策（AGENTS.md）—— 值得所有开源项目借鉴

- 不接受自主 AI PR/issue；AI 可协助编码但提交/推送/PR 必须由真人完成；**AI 生成的文本必须带免责声明**（AI 伦理的正面模板）

## 可借鉴性评分：★★★★★（架构参照：CO 总线 + 引擎线程纪律 + 通道化 + xfader 曲线 + sidechain）

---

# C 汇总：跨项目规范归纳与 MrAutoDJ 落地建议

## C1 可借鉴点速查（按里程碑）

### M1 虚拟 DJ 台

| 来源               | 借鉴点                                                                                                         |
| ------------------ | -------------------------------------------------------------------------------------------------------------- |
| B1 songs-automixer | 引擎状态机(IDLE/PLAYING/MIXING)+锁、样本级定时切歌、预渲染变速管线、epoch 防陈旧 worker、CLAUDE.md 不变量清单  |
| B2 pyCrossfade     | 逐小节渐变变速、3 频 EQ 交叉淡化（中频 dip）、click_protect、equal_power 曲线、settings dataclass 体系         |
| B4 cuekey          | 分析管线模块化（tempo/key/energy/cues 分文件）、SQLite 缓存(版本化)、进程池批处理+numba 隔离、Camelot 领域模型 |
| B12 mixxx          | CO 指令总线、引擎线程零分配零锁纪律、xfader 常量功率曲线、sidechain 压低                                       |

### M2 AI 自动 DJ

| 来源                   | 借鉴点                                                                                                                            |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| B2 pyCrossfade         | 离线批量混音算法库（可直接作为 M2 渲染后端）                                                                                      |
| B5 ai-remixmate        | 兼容性评分（BPM 倍频归一化/Camelot 档位/能量/音色/人声冲突+权重）、转场计划（下拍对齐+CUE/loop 建议）、贪心编排、JSON Schema 契约 |
| B4 cuekey              | 能量 1-10 评分、自动 CUE 点（结构聚类+下拍吸附）                                                                                  |
| B3 automix             | SimpleCrossfader 曲线库、结构分析（intro/drop/breakdown 状态机）                                                                  |
| B6 dj-track-similarity | Set 排序约束（同艺人限制/去重 key）、证据融合加权、可解释诊断                                                                     |

### M3 Claude 电台

| 来源               | 借鉴点                                                                                                                                       |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| B7 radio-dj        | LLM 导演一次调用规划 tanda、确定性回退（绝不静默）、可编辑技能 md、TTS provider 目录+shell 转义、去 emoji、i18n 提示词包、报时延迟到播出时刻 |
| B8 writ-fm         | 段落类型体系+字数闸门、主题池防重复（LRU）、节目记忆 JSONL、质量闸门重试、意图卡                                                             |
| B9 mixx-dj-mcp     | portmanteau 工具模式（operation Literal）、统一返回 {success,message,data}、OSC/控制映射表、MCP+REST 双入口                                  |
| B10 claudio        | **混合物品队列（song\|tts\|silence）**、搜索词解耦音乐源、人格 md 文件、计划生命周期事件                                                     |
| B11 wrzdj          | 点歌状态机（单活跃约束）、LLM 适配器网关（加密凭据+类型化错误）、推荐引擎（含 MusicBrainz 防幻觉）、安全/限流规范                            |
| B1 songs-automixer | 紧急自动混音（A 键）→ M3 无 LLM 时的手动兜底引擎                                                                                             |

## C2 文件分类 / 目录结构规范（共性归纳）

1. **单向分层**：入口 → 分析 → 应用/服务 → 引擎（B1），或 routes(薄) → services(业务) → db（B11/B10）
2. **src/ 布局**（B4/B9/B6）：`src/<pkg>/` 源码 + tests/ 对等；`[tool.hatch] packages = ["src/cuekey"]`
3. **一域一文件**：tools/deck_control.py、routes/requests.py、analysis/tempo.py——文件名即领域词汇表
4. **配置与代码分离**：dataclass 默认值（B2）、YAML+env 覆盖（B5）、环境变量集中（B6）、DB 单例（B11）
5. **资源/数据目录约定**：samples/、assets/、config/、data/、output/（writ-fm 的 `{show}/{slot}/{seq}_{type}_{slug}_{ts}.wav` 命名规范）
6. **文档地位高**：AGENTS.md/CLAUDE.md 与代码同级维护；架构图+设计决策+Gotchas 三件套（B1/B5/B11）

## C3 代码规范（共性）

1. 类型注解全开（`from __future__ import annotations`）；frozen dataclass 做领域对象（Key、TrackAnalysis）
2. 常量集中 + 注释理由（HPF_MIN_HZ 为什么是 300）；纯函数优先（transition.py/plan 规划器）
3. 可选重依赖**延迟导入**（librosa 在函数内 import + 明确 ImportError）
4. 不变量以文档清单固化（B1 Key invariants）；每个文件 docstring 说清职责与调用约束
5. 版本管理：uv + hatchling + pyproject 全配（black/isort/mypy/pytest），console script 入口

## C4 错误处理与日志规范（对比归纳）

| 场景         | 推荐做法                                                                                                    | 来源   |
| ------------ | ----------------------------------------------------------------------------------------------------------- | ------ |
| 启动期       | fail-fast：探测依赖/设备，缺失即明确报错退出（exit 2 + 修复指引）                                           | B1     |
| 运行期批处理 | fail-soft：坏文件记日志跳过，绝不中断整批                                                                   | B4/B3  |
| 单曲失败     | 降级默认值（empty_record / 中性分 0.5）+ 不抛 KeyError                                                      | B1/B5  |
| LLM/外部服务 | 确定性回退（随机选曲/泛化文案），核心服务绝不静默                                                           | B7     |
| 外部进程     | 超时+提示安装+异常 log 返回 None                                                                            | B3     |
| API          | 统一返回结构 + 错误带恢复建议 + 生产环境泛化 500                                                            | B9/B11 |
| 日志         | 文件+控制台双通道、stdout/stderr 镜像、log_failure（error 一句+debug 堆栈）、按日期滚动、asyncio 异常处理器 | B6     |
| 并发异步     | epoch/版本号使陈旧结果失效；faulthandler+worker crash 日志                                                  | B1/B4  |

## C5 测试与 CI 规范（共性）

1. 纯逻辑（转场规划/兼容性评分）直接单测——**把决策做成纯函数**是共同前提（B1/B5/B6）
2. 无头测试：`__new__` 跳过设备/重活，合成 numpy 直驱回调（B1）
3. 进程池崩溃测试钩子（CUEKEY_TEST_CRASH）、pytest marker 跳过重依赖（B5）
4. CI 纪律：ruff/pytest/uv；"用最便宜的能抓住错的验证"（B6 验证路由）

## C6 MrAutoDJ 分阶段落地建议

1. **M1 起步**：参考 B1 整体骨架（main → analyzer → app → engine），引擎+UI 分离；
   分析子系统照 B4（模块化+SQLite 缓存）；变速预渲染管线照 B1（rubberband）+ B2（EQ 过渡）；
   引擎内部用 B12 的 CO 总线思想（deck 控制全部走命名控制对象）
2. **M2**：把 M1 的"下一曲+转场"升级为 B10 的混合队列；兼容性评分照 B5、Set 约束照 B6、批量渲染照 B2
3. **M3**：控制面照 B9（portmanteau 工具 + MCP/REST 双入口）、电台调度照 B7（导演+回退+技能文件）、
   内容策划照 B8（段落体系+防重复+记忆）、点歌互动照 B11（状态机+安全）、UI 概念照 B10

---

> 本报告为研读汇总，任务勾选状态见 `x.progress.md`。

---

# B13 Pioneer DJ DDJ-FLX4 控制器学习报告（一比一复刻依据）

> 资料来源：官方用户手册（165 页）、Mixxx 开源映射文档（中文）、Mixxx MIDI 映射表（281 控件）。
> 目标：MrAutoDJ 虚拟 DJ 台按此布局与功能一比一复刻。


## 1. 布局总览（四大功能区）

```
┌─────────────────────────────────────────────────────┐
│ 1 Browse 浏览区（LOAD×2 + Rotary 旋钮）              │
├───────────────────────────┬─────────────────────────┤
│ 2 Deck 1 盘区（16 部件）   │ 2 Deck 2 盘区（同左）    │
├───────────────────────────┴─────────────────────────┤
│ 3 Mixer 混音区（TRIM/EQ×3/CFX/CUE/Fader/横推等 15 件）│
├─────────────────────────────────────────────────────┤
│ 4 Effects 效果区（Beat FX：通道选择/效果选择/拍数/深度）│
└─────────────────────────────────────────────────────┘
```

## 2. Browse 浏览区（每盘 2 件）

| 部件 | 功能 | SHIFT 组合 |
|---|---|---|
| LOAD 按钮 ×2 | 加载选中曲目到对应盘；**按两次=Instant Doubles**（从空闲盘复制曲目到播放盘、同位置播放） | D1: 跳到 Related Tracks；D2: 缩放浏览区 |
| Rotary 选择旋钮 | 转动=移动光标；按下=切换焦点（树/曲目列表） | 转动=缩放波形 |

## 3. Deck 盘区（每盘 16 部件，核心）

| # | 部件 | 按下 | 播放中 | SHIFT 组合 |
|---|---|---|---|---|
| 1 | IN 按钮 | 设循环入点 | 用转盘微调入点 | 循环入点调整模式 |
| 2 | OUT 按钮 | 设循环出点并开始循环 | 用转盘微调出点 | 循环出点调整模式 |
| 3 | 4BEAT/EXIT | 开始 4 拍 Auto Beat Loop | 取消循环 | 设置/取消 Active Loop |
| 4 | CUE/LOOP CALL ◁ | 调用 CUE/循环点 | **循环减半** | 删除调用点 |
| 5 | CUE/LOOP CALL ▷ | 调用 CUE/循环点 | **循环加倍** | CUE 待机保存/循环保存 |
| 6 | BEAT SYNC | 同步到主盘 BPM/节拍网格 | 取消同步 | 切换 TEMPO 量程（±6/10/16/WIDE%） |
| 6 | BEAT SYNC 长按 | **设为主盘** | - | - |
| 7 | TEMPO 推子 | 变速（量程可切） | - | - |
| 8 | HOT CUE 模式键 | 进入热 CUE 模式（Pad 用） | - | Keyboard 模式 |
| 9 | PAD FX1 模式键 | Pad FX 模式 1 | - | Pad FX 模式 2 |
| 10 | BEAT JUMP 模式键 | Beat Jump 模式 | - | Beat Loop 模式 |
| 11 | SAMPLER 模式键 | Sampler 模式 | - | Key Shift 模式 |
| 12 | Performance Pads ×8 | 按模式触发功能 | - | 视模式 |
| 13 | PLAY/PAUSE | 播放/暂停 | - | Serato: Stutter |
| 14 | CUE | 暂停时设 CUE；播放中回 CUE 并暂停（Back Cue）；按住=Cue Point Sampler | - | 回到曲首 |
| 15 | SHIFT | 组合键修饰 | - | - |
| 16 | Jog 转盘 | **顶面 Vinyl 模式开=搓碟；顶面/外圈=弯音 Pitch Bend**；SHIFT+顶面=高速快进/退 | - | - |

### Pad 八种模式（性能打击垫）
| 模式 | Pad 1-8 功能 |
|---|---|
| Hot Cue | 未亮=存热 CUE；亮=跳转（暂停时按住=预听）；SHIFT+亮=删除 |
| Beat Loop | 1/4、1/2、1、2、4、8、16、32 拍循环（Pad 位置即拍数） |
| Beat Jump | 前/后跳 1、2、4、8 拍；SHIFT+Pad7/8 跳 16 倍 |
| Sampler | 加载采样/播放/停止卸载 |
| Keyboard（Mixxx 映射为 Stems） | Pad1-4=人声/鼓/贝斯/其他 静音切换；Pad5-8=stem FX |
| Key Shift（Pitch Shift） | Pad 设置绝对半音（±1-4）；SHIFT+Pad 相对增减；Pad1/8 复位 0 |
| Pad FX1/2 | 效果触发（rekordbox 未实现于 Mixxx） |

## 4. Mixer 混音区（15 件）

| # | 部件 | 功能 |
|---|---|---|
| 1 | TRIM 旋钮 ×2 | 每通道预增益 |
| 2 | MASTER LEVEL | 主输出音量 |
| 3 | 耳机 CUE（master） | 主输出送入耳机 |
| 4 | Bluetooth MIDI 指示灯 | 连接状态 |
| 5 | 通道电平指示 ×2 | 通道音量（过推子前） |
| 6 | EQ（HI/MID/LOW）×2 | 三频增强/衰减 |
| 7 | MIC LEVEL | 麦克风音量 |
| 8 | CFX 旋钮 ×2 | SMART CFX 关=Sound Color FX（中心=原声）；开=Smart CFX |
| 9 | SMART CFX 按钮 | 开/关；SHIFT=换预设 |
| 10 | 耳机 CUE（通道）×2 | 通道送耳机；SHIFT+点按=Tap BPM |
| 11 | HEADPHONES MIX | 耳机监听平衡（CUE 通道 vs 主输出） |
| 12 | HEADPHONES LEVEL | 耳机音量 |
| 13 | SMART FADER 按钮 | 智能横推模式（自动音量/低音/BPM 适配） |
| 14 | Channel Fader ×2 | 通道音量（SHIFT+推=触发 Fader Start） |
| 15 | Crossfader | 左右通道平衡（曲线可设；SHIFT+推=Fader Start） |

## 5. Effects 效果区（6 件）

| # | 部件 | 功能 | SHIFT |
|---|---|---|---|
| 1 | BEAT FX CH SELECT 开关 | 效果目标通道（CH1/CH2/双） | - |
| 2 | BEAT FX SELECT | 切换效果类型 | 反向切换 |
| 3 | BEAT ◁ | 拍数-1（效果同步长度） | BPM Auto 模式 |
| 4 | BEAT ▷ | 拍数+1 | BPM Tap 模式 |
| 5 | BEAT FX LEVEL/DEPTH | 效果参数 | - |
| 6 | BEAT FX ON/OFF | 开/关 | Release FX |

## 6. 前后面板

- **Rear**：USB 供电口、USB 设备口（PC/Mac/iOS/Android）、Android MONO/STEREO 开关、MASTER 输出（RCA）、MIC 输入（1/4" TS）、MIC ATT 衰减、Kensington 锁孔
- **Front**：PHONES 耳机输出（3.5mm）

## 7. MIDI 映射要点（Mixxx 281 控件，供硬件对接）

- 信号格式：`0x9X`=Note On（按钮）、`0xBX`=CC（推子/旋钮）、`0xBX/0x3F` 等=LSB/MSB 双字节高精度推子、`0x94/0x95`=Pad 通道
- Deck1 用通道 1（0x90/0xB0），Deck2 用通道 2（0x91/0xB1）；FX 区用 0x94；Crossfader/耳机等 Master 用 0xB6
- 代表映射：PLAY=0x90/0x0B、CUE=0x90/0x0C、Loop IN=0x90/0x10、OUT=0x90/0x11、Beatloop 4=0x90/0x10（4BEAT 与 IN 同键复用）、Tempo=CC 0x20(LSB)+0x00(MSB)、Crossfader=0xB6/0x1F(LSB)+0x3F(MSB)、EQ 三频=CC 0x27/0x2B/0x2F(MSB)+0x07/0x0B/0x0F(LSB)、Jog 顶面=0xB0/0x22（Vinyl）、外圈=0xB0/0x21、Jog 触摸=0x90/0x36
- Pad 模式键：HOT CUE=0x90/0x1B、KEYBOARD=0x90/0x69、PAD FX1=0x90/0x1E、PAD FX2=0x90/0x6B、BEAT JUMP=0x90/0x20、BEAT LOOP=0x90/0x6D、SAMPLER=0x90/0x22 系
- **LED 反馈**：每个按钮/旋钮有对应 LED 控制（Note/CC 输出），Mixxx 映射含 LED 状态逻辑（如 Pitch Shift 模式的灯阵）

## 8. MrAutoDJ 对照（差距清单）

### 已实现（M1）
- 双盘播放/暂停/CUE（含 Back Cue 语义）、Loop IN/OUT/4BEAT/加倍减半、Beat Sync 待接、Tempo 变速、Jog 弯音、三频 EQ、横推（等功率）、通道/主音量、双输出耳机监听

### 未实现（一比一复刻需补）
1. **Browse 区**：LOAD 双按=Instant Doubles；Rotary 旋钮（光标/树切换）；波形缩放
2. **Jog 转盘**：顶面搓碟（Vinyl 模式）；外圈/顶面 Pitch Bend 区分；Jog 触摸检测；SHIFT+转=高速搜索
3. **Pad 8 模式**：Hot Cue 灯态/预听、Beat Loop 拍数矩阵、Beat Jump 前后跳、Sampler、Key Shift 半音（LED 灯阵）
4. **Mixer**：TRIM 预增益、通道电平指示、CFX/Smart CFX 效果旋钮、Smart Fader、Fader Start、Tap BPM、MIC（输入）
5. **Effects**：Beat FX 全套（通道选择/效果选择/拍数/BPM Auto-Tap/深度）
6. **组合键体系**：全局 SHIFT 修饰（每键第二功能）、长按（主盘设置）、双按（Instant Doubles）
7. **LED 反馈体系**：按钮灯态（Hot Cue 亮/灭、模式指示、Pitch Shift 灯阵）
8. **Slip 模式 / Censor / Stutter** 等表演功能（Mixxx 已映射：reverseroll 等）

> 结论：MrAutoDJ 下一步 UI/交互迭代按本报告第 2-5 节一比一布局；MIDI 硬件支持（M2 预留）按第 7 节信号表对接，Mixxx 的 .midi.xml 为现成映射蓝本。

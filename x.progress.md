# MrAutoDJ 源码研读任务清单（x.progress.md）

> 目标：通读 12 个参考仓库，提炼本项目（Python 虚拟 DJ 台 → AI 自动 DJ → Claude 电台）可借鉴的
> 代码结构、文件分类规范、代码规范、错误处理规范，逐步产出报告至 `w.study.md`。

> **任务清单纪律**（2026-11-05 定案，对齐 CapsulePulse；细则见 AGENTS.md 同名节）：
> - **既有 A/B/C/D/E/F/G/H/I/J 字母系列编号与格式原样保留、只增不删**——它们是已完成工作的勾选依据，不再按此方式新立任务
> - **自此起新任务改用三线编号轨道**：`PL{NNN}` 功能里程碑 / `FIX{NNN}` 审计修复（与审计附录 `A{NNN}` 恒同号）/ `PATCH{NNN}` 小修小改；组格式 `### PL{NNN}: {标题} [来源引用]`（来源：[plan#附录] / [problems#N] / [audit#A{NNN}]），条目格式 `- [ ] PL{NNN}.{序号} {标题} —— {做法（文件/函数级）}；验证：{可执行可断言}`
> - **勾选注记**：完成时改 `[x]` 并句尾追加 `（YYYY-MM-DD 已验证：{一句话结论}）`；结论如实，不达标不降级宣布
> - 新组追加在区末尾（从上到下 = 从旧到新）；已完成组全量保留

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

## D. M1 虚拟 DJ 台任务清单

- [x] D0.1 安装依赖 + ffmpeg
- [x] D0.2 base.json 音频参数核对
- [x] D0.3 冒烟验证基线
- [x] D1.1 扫描支持格式
- [x] D1.2 分析骨架（解码 → tempo/key/energy/cues）
- [x] D1.3 BPM 检测（fold/refine/snap）
- [x] D1.4 拍点追踪（Ellis DP）
- [x] D1.5 downbeat 相位
- [x] D1.6 调性（KK 24 键）
- [x] D1.7 Camelot 轮盘
- [x] D1.8 能量 1-10
- [x] D1.9 自动 CUE 点
- [x] D1.10 SQLite 缓存（三重校验）
- [x] D1.11 进程池批处理
- [x] D1.12 失败降级
- [x] D1.13 CLI
- [x] D2.1 引擎骨架（流+锁+状态机）
- [x] D2.2 解码归一化
- [x] D2.3 播放控制
- [x] D2.4 播放填充
- [x] D2.5 样本级定时切歌
- [x] D2.6 等功率曲线
- [x] D2.7 三频 EQ
- [x] D2.8 横推
- [x] D2.9 音量
- [x] D2.10 CUE
- [x] D2.11 循环
- [x] D2.12 变速预渲染
- [x] D2.13 Keylock
- [x] D2.14 双输出监听
- [x] D2.15 回调纪律
- [x] D3.1 prepare（SKIP/STRETCH + epoch）
- [x] D3.2 mix_now（对拍对齐 + 守卫）
- [x] D3.3 参数失效
- [x] D4.1 主窗口布局
- [x] D4.2 打碟机控件
- [x] D4.3 波形
- [x] D4.4 曲库表格
- [x] D4.5 状态栏日志
- [x] D5.1 无头引擎探针
- [x] D5.2 GUI 无头初始化
- [x] D5.3 端到端脚本
- [x] D5.4 冒烟验证
- [x] D5.5 提交 V0.1

## E. M1.5 FLX4 交互复刻任务清单

- [x] E1.1 Hot Cue 槽位（8 槽存/跳/删/预听 + 灯态）
- [x] E1.2 Beatgrid 跳转（±拍 + Skip 对齐）
- [x] E1.3 Key Shift 半音（±12 + 预渲染）
- [x] E1.4 Jog 接口（触摸/搓碟/弯音/搜索）
- [x] E1.5 VU 电平采集（预分配环形）
- [x] E1.6 Slip 模式（隐藏真实位置）
- [x] E1.7 Sampler 槽位（8 槽）
- [x] E1.8 效果库扩展（Echo/Delay 延迟线）
- [x] E1.9 传输辅助（Fader Start/Tap/Censor/Stutter）
- [x] E2.1 全局 SHIFT 组合键
- [x] E2.2 Pad 打击垫（1×8 + 5 模式 + 灯态）
- [x] E2.3 Jog 转盘（滚轮弯音/拖动搓碟/搜索/Vinyl）
- [x] E2.4 Beat FX 面板（效果库/通道/拍数/深度）
- [x] E2.5 Mixer 补全（TRIM/VU/Fader Start/Tap）
- [x] E2.6 Instant Doubles（LOAD 双按）
- [x] E2.7 LED 灯态联动
- [x] E2.8 表演功能键（Slip/Censor/Stutter）
- [x] E3.1 四区布局重排（Browse + 双 Deck + Mixer/Effects）
- [x] E4.1 无头引擎探针
- [x] E4.2 端到端脚本
- [x] E4.3 冒烟 + GUI 无头初始化
- [x] E4.4 提交 V0.2（由用户执行）

## F. 任务清单（F1-F3 = P1-P3 修复，V0.21；F4-F7 = M1.6 UI 拟物改版，V0.22）

> 规划：2026-08-11 定稿。P1-P3 修复已随 V0.21 提交；M1.6 UI 拟物改版为 V0.22（V0.21 被修复占用故顺延）；Git 提交拆分由用户决定。
> 验证约定：P1-P3 为听感/手感问题，修完必须 GUI 实测；M1.6 每步无头截图 + 用户对照 Figma 设计稿迭代。
> 做法说明：`—— 做法` 为执行要点，子任务均需自查代码上下文后动手。

### F1. P1 Echo 回绕跳读修复（engine.py）

- [x] F1.1 复核根因（2026-08-11 完成：`FeedbackDelay.process()` 第 252 行 `start = max(0, delay - self._pos)`，回绕后 `_pos(≈1912) < delay(11025)` 误判未充满、整段跳读）—— 数值验证：回绕后 4 整块 continue 跳过（≈0.21s 无回声窗口，与现象吻合）
- [x] F1.2 修复：删除 `start` 判断，恒从块头读取 —— 改 `process()`：删 `start = max(0,...)` 与 `if start >= frames: continue`；`read = (self._pos - delay) % self._buf_len` 整块读，保留回绕两段读/写；零初始化天然提供初始"未充满"
- [x] F1.3 无头验证（TDD：先 FAIL 后 PASS）—— `.temp/probe_p1.py`：29 脉冲 × 3 tap 回声能量断言；修复前 Echo 丢 4/Delay 丢 18（FAIL 复现），修复后全部达标（PASS）；对照音频 `.temp/echo_out_fail.wav` / `echo_out_pass.wav`
- [x] F1.4 GUI 听测（2026-08-11 用户实测确认：Echo/Delay >5s 无周期中断，修复生效）

### F2. P2 弯音不归零修复（ui + engine）

- [x] F2.1 方案选定（2026-08-11：方案 A）—— UI 侧单发 QTimer 80ms 脉冲归零（改动小、不动实时线程）；方案 B（引擎侧时间戳超时衰减）侵入实时线程，弃用；结论已记录 y.problem.md P2
- [x] F2.2 实现方案 A —— `ui.json` 加 `jog_bend_reset_ms: 80`；`main_window.py`：`__init__` 初始化 `_bend_pending{letter}` + 每盘单发 QTimer（超时 → `jog_bend(0.0)` 归零）；`_on_bend_release(letter, v)` 记录 pending 并重启定时器；bend 接线带盘标识；删除未初始化字段 `_bend_timer_pending` 依赖
- [x] F2.3 无头验证（TDD：先 FAIL 后 PASS）—— `.temp/probe_p2.py` 13 项断言：修复前 5 项 FAIL（rate 卡 ±0.02 不归零复现），修复后 13/13 PASS（单次/连续 3 格/负弯音/双盘独立均自动归零）；引擎层 4 项（生效/钳制 ±0.5/步长推进/归零恢复）通过
- [x] F2.4 GUI 实测（2026-08-12 用户确认：方向正确（上加速/下减速）、减速无卡顿、归零生效；每格步进与累积参数后续再调优）

### F3. P3 搓碟语义修复（engine + jog_wheel）

- [x] F3.1 引擎触摸锁定 —— `_fill_playing` 在 Slip 分支后加 `_jog_touched` 分支：位置只由 `jog_scratch` 驱动、不自动推进（输出当前位置重复 = 唱片停转）；Slip 在前保证 slip 期间 `_slip_actual` 继续暗中推进
- [x] F3.2 scratch 驱动与释放续播 —— 触摸期间 `jog_scratch(delta)` 改 `_position`（已有，含钳制）；`jog_touch(False)` 后下一块恢复推进（非 slip 就地继续，符合 FLX4 默认语义）
- [x] F3.3 增益标定 —— `ui.json` 加 `jog_scratch_gain: 256`（基础每像素样本）+ `jog_scratch_speed_ref: 800`（px/s 参考）；`jog_wheel` 新增 `_scratch_gain(dx, dt)` 速度映射（gain = base × clamp(speed/ref, 0.5, 3.0)，慢速细腻/快速大幅）+ `QElapsedTimer` 测速；删除硬编码 `SCRATCH_GAIN=256`
- [x] F3.4 GUI 实测（2026-08-12 用户确认：平滑变速刮擦顺滑，手停静音、Slip 落回均正常；增益手感调优留待后续）

### F4. M1.6 前置准备（2026-08-11 更新：多模态主模型路线替代 Figma MCP）

> 决策背景：Figma 无法操作（无设计稿/token），用户选择更换多模态主模型（方案 A）——AI 直接读图核对，Figma MCP 降级为备选（见 z.plan.md 附录）。

- [x] F4.1 更换多模态主模型 —— 用户已切换（2026-08-13 确认，read 工具可读图）
- [x] F4.2 视觉能力验证 —— DDJ-FLX4 参考图读取成功，布局要素/控件分布/主色系提取无误
- [x] F4.3 收集布局参考 —— 用户提供 FLX4 官方面板渲染图（.reference/dj-controller/DDJ-FLX4）+ B13 部件清单
- [x] F4.4 生成布局规格单 —— `docs/ui_layout.md`：四区 ASCII 图 + 部件表（Browse/Deck/Mixer/Effects 四区 30+ 控件）+ 配色方案 + 尺寸基准（1280×800 画板、Jog 140×140、Pad 35×35 等）+ 交互语义
- [x] F4.5 ui.json 配色 token —— panel_base/panel_edge/panel_inset/silk_text + glow_orange/blue/green/white + pad_colors[5] 已注册；加载验证 OK（panel_base=#1c1e22 等）
- [x] F4.6 冒烟 —— 全模块 import + token 加载验证通过

### F5. 原语控件库（ui/widgets/，全 paintEvent 自绘 + 静态层 QPixmap 缓存）

- [x] F5.1 PanelFrame —— QFrame 子类；paintEvent：QRoundedRect 路径填充垂直渐变（panel_base→panel_edge）+ 顶部高光带 + 内阴影；标题 QLabel 叠放（silk_text、uppercase、字距）；只画静态、一次渲染缓存
- [x] F5.2 RotaryKnob —— QWidget 子类；静态层（30° 扇形刻度环+外圈+凹槽）QPixmap 缓存；动态层：指针线按 value 旋转；mousePress/Move 垂直拖拽（dy→value 映射）、wheelEvent 步进、doubleClick 复位；`valueChanged(float)` 信号
- [x] F5.3 GlowButton —— QAbstractButton 子类；paintEvent 按态绘制：常态内凹座（inset+内阴影）、按下/active 画 QRadialGradient 辉光（led_color 扩散）+ 亮色文字；`set_led(on, color)`；pressed/released 信号
- [x] F5.4 FaderSlider —— QWidget 子类；静态层：水平/垂直凹槽（内阴影）+ 两端刻度 + 中央线；动态层：金属帽（垂直渐变+高光棱）；拖拽 + wheel + doubleClick 回中；`valueChanged` 信号
- [x] F5.5 LedStrip —— QWidget 只读；`set_level(0..1)` 触发 update；paintEvent 画 N 段：段高度按 level 截止，绿→黄→红分带（阈值常量进 ui.json）
- [x] F5.6 MiniDisplay —— QWidget 只读；`set_text(str)`；paintEvent：黑底圆角 + 荧光绿等宽文字 + 微弱辉光（半透明多层绘制模拟）
- [x] F5.7 自检与样例截图 —— 确认 ui/widgets/ 内零 `import modules/`；写 `.temp/preview_primitives.py`：offscreen 渲染 PanelFrame+旋钮+按钮+推子+LedStrip 样例 → `.temp/ui_preview/primitives.png`，AI 读图自检质感 + 用户确认第一版观感

### F6. 四区组合替换（按布局规格单）

- [x] F6.1 Mixer 区 —— TRIM/EQ×3/MASTER 换 RotaryKnob、通道推子/横推换 FaderSlider、VU 换 LedStrip、Fader Start/Tap 换 GlowButton；valueChanged 浮点映射直连引擎（原 /100 换算删除）
- [x] F6.2 Deck 区 —— deck_widget：PLAY/CUE/循环/Beatloop/Keylock 换 GlowButton（播放 LED 橙色）；pad_widget：8 键 + 5 模式键换 GlowButton（35×35，五模式色灯阵）
- [x] F6.3 Jog 升级 —— 金属渐变外圈 + 播放橙色指示点 + 中心屏（BPM/VINYL 标识），set_playing/set_info 接口由 \_tick 驱动
- [x] F6.4 Beat FX 面板 —— 效果下拉改互斥 GlowButton 组（LED 标识）、拍数改 MiniDisplay、DEPTH 改 RotaryKnob、FX ON/AUTO/TAP 换 GlowButton
- [x] F6.5 Browse 区 —— LOAD A/B（橙 LED）/目标盘/SHIFT/打开 换 GlowButton
- [x] F6.6 检验 —— probe_p6：32/32 PASS（原语类型 17 项 + 信号接线 12 项 + 截图 3 项）；冒烟 OK；截图 .temp/ui_preview/layout_v6.png + deck_a/pad_a/beat_fx
- [x] F6.7 读图对照参考图（2026-08-12 多模态验证：layout_v6.png 四列布局对齐 FLX4，深色面板+控件质感到位，方块字体为 offscreen 模式限制）

### F7. 验证与收尾

- [x] F7.1 无头定稿 —— `QT_QPA_PLATFORM=offscreen` 初始化 MainWindow + `grab()` 全窗口截图定稿（layout_final.png 1650×800，多模态读图确认四列布局/深色主题/控件质感到位）；冒烟 import 全模块 + 版本号 ver 0.22
- [x] F7.2 GUI 实测回归 —— 用户实测确认（2026-08-12）：交互/灯态/SHIFT/听感/F1-F3 复核均 OK；已知不足后续迭代（用户授权先当已实现）
- [x] F7.3 连带文档 —— README 使用说明/项目结构（ui/widgets/）、z.plan.md M1.6 勾选、y.problem.md P1-P3 改 ✅、x.progress.md F 系列勾选
- [x] F7.4 提交 V0.22（由用户执行，Git 拆分用户决定）

## G. 审计修复任务清单（依据 z.plan.md 附录：全量代码审计报告 2026-08-12）

> 规划：2026-08-12 生成。按 P0→P1→P2→P3 顺序执行；每项修复后跑对应检验（probe_p1/2/3/5/6 + 新增用例）确认通过才算完成；版本号与 Git 拆分由用户决定。
> 做法说明：`—— 做法` 为执行要点，每项先自查代码上下文再动手。

### G0. P0 正确性修复（7 项）

- [x] G0.1 analyzer 采样率硬编码 —— `analyzer.py` `engine_sr = 44100` → `int(_SC.base.get("sample_rate", 44100))`；验证：probe_g0 断言配置驱动 + beats 索引在曲内范围
- [x] G0.2 搜索分支形状错误 —— 抽 `Deck._fill_resample()` 公共方法（step 样本线性插值到 frames，step==frames 直通），弯音与正向搜索共用；验证：`jog_search(0.5)` fill 不崩、推进正确、输出非静音
- [x] G0.3 fade 除零 —— `start_mix` 内 `_fade_samples = max(1, int(fade_seconds*sr))`；验证：`start_mix(fade=0)` 不崩、\_fade_samples≥1、转场输出非静音
- [x] G0.4 rotary 指针绘制 —— 原 QRectF 当"点"取 center 致线段错位 → 直接 `drawLine(圆心, 端点)`（QPointF）；验证：绘制不崩 + 端点几何断言；截图待多模态核对
- [x] G0.5 pad 灯态冲突 —— 8 键去掉 `setCheckable(True)`（点按辉光由 isDown 驱动、业务灯态由 set_led 驱动，防 isChecked 残留灯阵失真）；验证：点击发一次信号 + 无 checked 残留 + set_led 控制灯态
- [x] G0.6 panel set_title 崩溃 —— 无标题构造时惰性创建 `_label`（hasattr 检查）；验证：`PanelFrame().set_title("X")` 不崩 + 标签存在
- [x] G0.7 themes 接线 —— `main.py` 在 MainWindow 前调 `apply_theme(app)`（QSS 此前从未生效）；验证：main.py 含调用 + 应用后 QSS 非空

### G1. P1 去重（4 项）

- [x] G1.1 解码归一化统一 —— 新建 `utils/audio_decode.py`（`decode_audio(path, channels, frame_rate)`：pydub 解码 + 按位深归一化）；`engine.load_audio` 与 `analyzer._decode_mono` 引用（mono 取 `[:,0]`）；验证：probe_g1 16/24-bit 峰值≈0.8 且两处一致 + 源码断言去重
- [x] G1.2 金属渐变抽公共皮肤 —— 新建 `ui/widgets/_skins.py`（`metal_gradient()/metal_pen()/top_highlight_pen()`），jog_wheel/fader_slider/rotary_knob 三处引用替换各自渐变（色值统一 208,212,218→150,154,160→112,116,122）；验证：probe_g1 渲染不崩 + 截图待多模态核对
- [x] G1.3 拍长/钳制/步进公共化 —— ① `Deck._beat_len(bpm)` 提取（beat_jump/set_beatloop 共用）；② `key_shift_max: 12` 进 base.json，engine/transition_manager 双处引用（\_KEY_SHIFT_MAX）；③ `wheel_step_divisions: 20` 进 ui.json，rotary_knob/fader_slider 滚轮步进引用；验证：probe_g1 行为等价 + 源码断言
- [x] G1.4 表头配置化 —— `main_window` 用 `_SC.ui.get("table_headers")` 驱动表头与列数（原硬编码 ["Mix",…] vs 配置 ["状态",…] 不一致问题解决）；验证：probe_g1 表头文本/列数与配置一致

### G2. P2 配置化（3 组）

- [x] G2.1 modules 参数进 base.json —— ① engine：max_gain/vu_buffer/eq_freqs[100,1k,10k]/eq_gain_db[6,-30]/slot_count/jog_bend_max=0.5/jog_search_max=16/fx_echo+fx_delay 预置（Echo/Delay 类与 Beat FX 联动引用）；② transition_manager：mix_trigger_margin_seconds/default_fade_seconds/default_restore_seconds；③ transition.py：max_drift_beats/tempo_match_tolerance；④ analyzer：min_bpm/max_bpm（能量权重与 CUE 参数组暂留代码内，后续迭代）；验证：probe_g2 16 项配置驱动断言 + 行为等价（越界槽位忽略等）
- [x] G2.2 ui 配色去硬编码 —— main_window（\_UI_COLORS 死变量改 \_UI + LOAD/Mix 橙）×3、deck_widget（播放 LED 橙）、beat_fx（效果键橙）、jog_wheel（#ff7a2f/#e8ecf0/#8a9099/#1a1a1a → token）共 8 处；验证：probe_g2 源码断言无残留字面量色值
- [x] G2.3 兑现配置承诺 —— ui.json 补 `led_green_threshold: 0.6`/`led_yellow_threshold: 0.85`（led_strip 原读不存在的键）/`jog_search_step: 4.0`（SEARCH_WHEEL_STEP 改读配置）；table_headers 已随 G1.4 启用；验证：probe_g2 键存在 + 控件读取值一致

### G3. P3 清理（5 组）

- [x] G3.1 死代码清理 —— ① `ui/vu_meter.py` → archived/（被 LedStrip 替代，零引用）；② shift_state：删零调用 `toggle()`/`active`，`changed` 信号接线到 SHIFT 按钮 LED（glow_blue）；③ fader_slider `_TRAVEL`；④ main_window：QMessageBox 导入/`_on_search_release` 占位接线/`_UI_COLORS` 说明区引用；⑤ engine `_last_out_pos`（只写不读）；⑥ transition_manager `_next_bpm/_next_downbeats`（只写不读）；⑦ convert `to_int/to_optional_float` + analyzer `to_float` 死导入；验证：probe_g3 源码断言 + grep 确认
- [x] G3.2 死模块标注 —— ① utils.retry 标注"规划中（M3 网络接入启用）"；② config.settings 标注"规划中（UI 窗口几何/主题持久化接入）"；③ file_utils.clear_cache 标注"保留供热重载/测试"；验证：probe_g3 关键字断言
- [x] G3.3 说明区同步 —— engine（补常量组/FeedbackDelay 类/分配取舍说明/D2 更新）、jog_wheel（0.02/×256 过时 → 0.05/动态增益/配置键）、analyzer（补 7 函数）、stretcher（补 \_smootherstep_integral）、convert（"analyzer 复用"失实修正）；验证：probe_g3 关键字覆盖
- [x] G3.4 类型注解统一 —— engine Optional×6/tm Optional×4 → `| None`（typing import 清理）；get_gains→`tuple[float,float]`、vu_levels→`list[float]`、\_sample_playing→`tuple[int,int]|None`、\_tap_times→`list[float]`、fold_ratio→`tuple[float,str]`、\_detect_cues→`list[int]`、scan_folder→`list[str]`、analyze_many paths→`list[str]`；验证：probe_g3 源码断言 + import 不崩
- [x] G3.5 延迟导入上移 + 参考标注移除 —— ① main_window：DeckWidget/JogWheel/PadWidget/BeatFxWidget 顶层导入 + `import time as _time` 顶层；② engine `import time` 顶层；③ deck_widget `Path` 顶层；④ 移除 jog_wheel/pad_widget/beat_fx/shift_state 第 2 行"参考：w.study.md…"标注（AGENTS.md 禁令）；验证：probe_g3 源码断言
- [x] G3.6 检验 —— probe_g3 全 PASS + 全量回归（g0/g1/g2/p1/p2/p3/p5/p6 全绿）+ 冒烟 + 截图（纯代码清理无读图需求）

### G4. 验证与收尾

- [x] G4.1 全量回归 —— probe_p1/p2/p3/p5/p6/g0/g1/g2/g3 **9/9 PASS** + 冒烟 OK + layout_audit.png（1650×800）；多模态读图核对 G0-G3 无视觉回退
- [x] G4.2 GUI 实测（2026-08-12 用户确认）—— 交互/灯态/听感 + G0 修复项复核均正常；后续将进行多轮审计迭代
- [x] G4.3 文档同步 —— z.plan.md 审计附录标注已修项、README 移除 vu_meter 条目、x.progress.md G 系列勾选
- [x] G4.4 提交（由用户执行，Git 拆分用户决定）

## H. 第二轮审计修复任务清单（依据 z.plan.md 附录 A002：全量代码审计报告（第二轮，2026-08-12））

> 规划：2026-08-12 生成。按 P0→P1→P2→P3 顺序执行；每项修复后跑对应检验（复用 probe_g0-g3 模式 + 新增用例）确认通过才算完成；多模态节点：涉及截图核对时停下通知切换。
> 做法说明：`—— 做法` 为执行要点（含简单修复方案）。

### H0. P0 正确性修复（7 项）

- [x] H0.1 analyzer hop 脱钩（2026-08-12）—— `hop = 512` 删除，mfcc/chroma 直接用 `ANALYSIS_HOP`（配置变更 CUE 检测跟随）；验证：probe_h0 源码断言 PASS
- [x] H0.2 DeckEQ setter 无锁（2026-08-12）—— `_set_coeffs` 改单条元组赋值 `self._b, self._a = b / a0, a / a0`（原子替换，回调不会读到新旧混配）；验证：probe_h0 断言 + 系数行为回归
- [x] H0.3 waveform 1D 防护（2026-08-12）—— `mono = audio if audio.ndim == 1 else np.mean(audio, axis=1)`（1D 不再 AxisError）；验证：probe_h0 1D set_audio/grab 不崩
- [x] H0.4 main_window 无锁写 \_position（2026-08-12）—— Deck 新增公开 `set_position_samples(samples)`（持锁 + clamp），main_window Instant Doubles 改用之；验证：probe_h0 设置/clamp 断言 + 源码断言无直写
- [x] H0.5 min==max 除零（2026-08-12）—— rotary `_angle()`/fader `_ratio()` 分母 `max(span, 1e-9)`；验证：`RotaryKnob(0,0)`/`FaderSlider(0,0)` 构造+grab 不崩
- [x] H0.6 deck_widget 采样率配置化（2026-08-12）—— 进度换算改 `_SR = _SC.base["sample_rate"]`（44100 字面量删除）；验证：probe_h0 源码断言
- [x] H0.7 static_config 校验（2026-08-12）—— mapping/data `isinstance(dict)` 校验 + 缺 base/ui 键抛 RuntimeError（原静默降级掩盖错误）；验证：probe_h0 源码断言

### H1. P1 去重（4 项）

- [x] H1.1 拍数阶梯单源（2026-08-13）—— beat_fx_widget 导出 `BEAT_LADDER = [1,2,4,8,16,32]`（\_beats_delta 引用），main_window Beat Loop Pad 引用（原双处字面量消除）；验证：probe_h1 源码断言
- [x] H1.2 path→entry 提取（2026-08-13）—— main_window 新增 `_entry_by_path(path)`（双击加载/Instant Doubles 共用），重复查找消除；验证：probe_h1 命中/未命中行为断言
- [x] H1.3 KEY_SHIFT_MAX 单源（2026-08-13）—— engine 改公开 `KEY_SHIFT_MAX`（原 \_KEY_SHIFT_MAX），transition_manager import 引用（原双处读键消除）；验证：probe_h1 源码 + 值一致断言
- [x] H1.4 stretcher 渲染样板 + engine 死 import（2026-08-13）—— 抽 `_render_via_cli(audio, sr, args_fn, prefix, cb)` 公共管道（tmpdir/sf.write/finally 清理收敛，shutil.rmtree 简化）；make_transition_buffer（--centre-focus + timemap）/make_keylock_buffer（--pitch）改为 args_fn 调用，行为等价；engine.py:13 死 import（plan_transition/tempo_compatible 无调用点）删除；验证：probe_h1 源码断言 + 全量回归（probe_g1/g3 断言同步新状态）

### H2. P2 配置化（4 项）

- [x] H2.1 analyzer 能量权重+CUE 参数（2026-08-13）—— `energy_weights`/`cue_params` 进 base.json；`ENERGY_WEIGHTS`/`CUE_PARAMS` 模块常量读取，\_detect_energy 权重与 \_detect_cues（max_cues/min_spacing/n_mfcc）引用；验证：probe_h2 配置断言 + 无字面量
- [x] H2.2 engine FX 参数群（2026-08-13）—— `knob_deadzone`/`fx_trans_ladder`/`fx_hpf_range`/`fx_lpf_range`/`fx_echo_depth`/`fx_delay_depth` 进 base.json；EQ 死区×3/FX 深度×2/Fader Start×1 的 0.01 改 `KNOB_DEADZONE`，Trans 阶梯/HPF/LPF 对数范围/Echo/Delay 深度映射改配置常量；验证：probe_h2 配置断言 + 无 0.01 字面量
- [x] H2.3 themes QSS token 化（2026-08-13 代码完成）—— QSS 内 6 色（#1a1a1a/#2a2a2a/#222222/#111111/#003300/#0d0d0d）全部改引用 ui.json token（panel_inset/panel_edge/panel_base/背景色），说明区"零硬编码"矛盾修复；验证：probe_h2 源码断言 PASS + **截图多模态核对（待切换）**
- [x] H2.4 logger 路径+轮转+控制台兜底（2026-08-13）—— `log_dir`（显式配置优先，Windows 默认 %LOCALAPPDATA%/MrAutoDJ）+ `log_max_bytes`/`log_backup_count` 进 base.json；FileHandler→RotatingFileHandler；stderr `reconfigure(errors="replace")` 防特殊字符崩溃；验证：probe_h2 日志特殊字符（☃）写入不崩

### H3. P3 清理（5 组）

- [x] H3.1 def 内 import 全清（2026-08-13）—— engine/analyzer（utils 顶层导入）、main_window（tempo_compatible 用顶层已有导入 + import 顺序修正）、rotary_knob（math 顶层）、transition_manager（make_keylock_buffer 合并顶层 import）；验证：probe_h3 源码断言
- [x] H3.2 def 内 def 提升（2026-08-13）—— tm `_work` 闭包 → 模块级 `_prepare_work(manager, next_path, my_epoch, plan)`；main_window `_on_result` 闭包 → 模块级 `_on_analysis_result(window, ...)`；验证：probe_h3 断言 + prepare/分析流程回归（冒烟）
- [x] H3.3 glow_white 修正 + skins 收敛（2026-08-13 代码完成）—— glow_button 辉光文字改 `_GLOW_WHITE`（原纯白不一致）；jog_wheel 描边→`metal_pen(2)`、rotary_knob 高光→`top_highlight_pen(60)`；验证：probe_h3 源码断言 + **截图对比待多模态核对**
- [x] H3.4 死代码（2026-08-13）—— settings.CONFIG_DIR 删除（含说明区）；`_detect_cues` 注解 `list[int]`→`list[dict]`；main_window `_SC.ui`→`_UI` 统一（3 处）；ui.json quota_warn_percent 保留（M3 预留）；验证：probe_h3 断言 + grep
- [x] H3.5 说明区 + 小项（2026-08-13）—— beat_fx/main_window 说明区补配置键、deck_widget 44100 注释同步、glow_button/mini_display 文本 elide、pad_colors 空列表兜底、beat_fx 尺寸 44→48、Key Shift 双灯语义确认（Pad1/8 均复位键，双灯同亮为预期，加注释）、fade_seconds→DEFAULT_FADE_SECONDS、16777248→Qt.Key_Shift、range(8)→SLOT_COUNT；验证：probe_h3 断言 + 冒烟

### H4. 验证与收尾

- [x] H4.1 全量回归（2026-08-13）—— 13 个 probe（p1/p2/p3/p5/p6/g0/g1/g2/g3/h0/h1/h2/h3）**13/13 PASS** + 冒烟 OK + layout_h.png（1650×800）定稿 + 版本 ver 0.24
- [x] H4.2 GUI 实测（2026-08-13 用户确认）—— H0 修复项复核（EQ 旋钮/进度显示/加载/分析）界面正常
- [x] H4.3 文档同步（2026-08-13）—— z.plan.md 附录 A002 标注已修（P0-P3 ✅）、x.progress.md H 系列全部勾选、README 徽章 ver 0.24、base.json ver 0.24
- [x] H4.4 提交 V0.24（由用户执行，Git 拆分用户决定）

## I. 第三轮审计修复任务清单（依据 z.plan.md 附录 A003：全量代码审计报告（第三轮，2026-08-13））

> 规划：2026-08-13 生成（作为次日修复任务）。按 I0→I4 顺序执行；每项修复后跑对应检验确认通过才算完成；多模态节点：涉及截图核对时停下通知切换。
> 做法说明：—— 做法 为执行要点（含简单修复方案）。
> 执行：2026-11-05 完成 I0-I4（I4.2/I4.4 待用户）；I0.5/I2.6 为 A003 表列明但原清单遗漏的补录项。

### I0. P0 正确性修复（4 项 + 补录 1 项）

- [x] I0.1 analyzer hop NameError（P1 回归，2026-11-05）—— analyzer.py `_detect_cues` hop_length=hop 引用已删局部变量 → CLI 批量分析崩溃；改 hop_length=ANALYSIS_HOP；验证：probe_i0 源码断言 + 9s 合成音频 _detect_cues 功能不崩（NameError 消除）
- [x] I0.2 _fill_resample step==0（2026-11-05）—— engine 正向搜索 |rate|<0.000244 时 step==0 → 空数组负索引 IndexError 静音卡死；搜索/弯音两调用点均 step = max(1, int(round(...)))；验证：probe_i0 jog_search(±0.0001) fill 不崩且输出非静音（曲头反向静音为正确语义，探针先 seek 离开曲头）
- [x] I0.3 Censor 曲头反向清除（2026-11-05）—— engine `_fill_playing` 反向分支删 _reverse=False 置位，到曲头钳 0 保持反向停留（仅 censor(False) 恢复）；验证：probe_i0 按住 10 块越过曲头 _reverse 仍 True + 释放恢复正向推进
- [x] I0.4 MIXING 播放键 UI 失实（2026-11-05）—— main_window 导入 State，_tick 播放判定改 `deck.state in (State.PLAYING, State.MIXING)`；验证：probe_i0 假引擎 MainWindow：MIXING 态 _tick 后播放键"暂停"、IDLE 态"播放"
- [x] I0.5 空 cue 切片 timemap[-1] IndexError（2026-11-05 补录，A003 P2 表列明但原清单遗漏；A003 标注 transition_manager.py:208 系笔误，实际在 stretcher.py）—— make_transition_buffer 入口加非空立体声校验 + timemap 空校验，抛可读 ValueError 由 on_done(None, exc) 上报不崩溃；验证：probe_i0 空输入断言

### I1. P1 去重（3 项）

- [x] I1.1 双 BPM 路径统一（2026-11-05）—— Deck 加公开 `bpm` property（读锁内 _bpm）；_on_beatloop 与 Pad Beat Loop 统一走 _on_beatloop（deck.bpm 驱动，BPM 未知状态栏提示，删除 or 120.0 静默假设）；验证：probe_i1 property/钳制/双入口行为一致 + main_window 无 deck._bpm 直读
- [x] I1.2 BeatFxWidget 公开接口（2026-11-05）—— 新增 is_on()；_apply_beat_fx 改公开调用；验证：probe_i1 开关两态断言 + 源码无 _onoff 跨控件私有访问
- [x] I1.3 _apply_mode_color 重复表达式（2026-11-05）—— 改调 self.mode_color()；验证：probe_i1 源码断言 + 模式切换灯色行为等价

### I2. P2 配置化（5 项 + 补录 1 项）

- [x] I2.1 配置键层级修复（2026-11-05）—— led_strip/mini_display 顶层读 warning/danger/accent 改 _UI["colors"] 子对象（对齐 themes.py 路径，改配置即生效）+ 说明区补层级；验证：probe_i2 取值与 ui.json colors 一致
- [x] I2.2 pad 硬编码 8 → SLOT_COUNT（2026-11-05）—— pad_widget 三处字面量改引用 engine.SLOT_COUNT（槽位单源）；main_window Key Shift 半音表加越界防护（表长固定 8）；验证：probe_i2 pad 键数=SLOT_COUNT + 越界灯态忽略
- [x] I2.3 LedStrip 段数进配置（2026-11-05）—— ui.json 加 `led_segments: 12`；_SEGMENTS 读配置，main_window 显式 12 删除；验证：probe_i2 双处一致
- [x] I2.4 settings 配置防御（2026-11-05）—— user_config_path/default_theme 改 .get() 兜底；主题白名单改 base.json `themes` 派生（新增键 ["light","dark"]，兜底恒含 DEFAULT_THEME）；验证：probe_i2 白名单一致 + 非法主题回默认
- [x] I2.5 配置缺键防御（2026-11-05）—— analyzer CUE_PARAMS 三键/engine ECHO_PRESET/DELAY_PRESET 直接索引改 .get(key, 默认)；验证：probe_i2 清空配置后 _detect_cues/Echo/Delay 不崩
- [x] I2.6 convert to_float 拦截 nan/inf（2026-11-05 补录，A003 P3 遗留项）—— math.isfinite 兜底，坏数据回 default 不污染 BPM/能量下游计算；验证：probe_i2 nan/inf/nan 字符串全断言

### I3. P3 清理（6 组）

- [x] I3.1 rubberband 前置检查（2026-11-05）—— `_render_via_cli` 缺可执行文件抛可读 RuntimeError（原 [None,...] 进 subprocess 报晦涩 TypeError）；main_window._on_prepare 前置探测提示（不阻断——SKIP 直混转场不受影响）；验证：probe_i3 mock 缺失断言报错信息
- [x] I3.2 死代码清理（2026-11-05）—— pad_light() 零调用删除；jog_wheel QLabel 死导入删除；transition_manager numpy 转 TYPE_CHECKING 守卫（注解仍可查）；engine 恒 False 分支删除（与 I0.2 合并执行）；beat_fx 四死信号（CH/AUTO/TAP/bpm）标注"预留未接线（M1.7 批次 1 启用）"控件保留；验证：probe_i3 源码断言
- [x] I3.3 函数内 import 残留（2026-11-05）—— analyzer `_warm_worker` import tempfile 上移顶层（librosa 重依赖按约定豁免）；验证：probe_i3 源码断言无函数内 import（librosa 除外）
- [x] I3.4 注释/文档失实批量（2026-11-05）—— H0.2 注释"原子替换"改"缩短混配窗口"（如实）；等功率换算两处失实说法删除；deck_widget/waveform/themes 说明区补齐（glow_orange/sample_rate/1D/base.json）；themes.apply_theme 默认主题改读 base.json（签名 None）；main_window 布局注释改五列视图；README 补 audio_decode/x.progress 描述/拟物五列标题；验证：probe_i3 断言
- [x] I3.5 性能与细节（2026-11-05）—— glow_button set_led 状态未变不重绘（去 ~180 次/秒无效重绘）；set_fx 复用 Biquad 实例换系数 + keep_zi 保留延迟状态（防深度扫动咔嗒）+ Biquad.bypass()；mini_display elide 先 setFont 再度量（修 H3.5 引入的度量错位）；waveform _SC.ui→_UI 统一；_fill_resample 死分支删除（同 I3.2 恒 False 分支）；验证：probe_i3 重绘计数/实例复用/zi 保留/绘制顺序断言；深度扫动听感留 GUI 实测
- [x] I3.6 分析 worker 防御（2026-11-05）—— closeEvent 置 _closing flag、回调前检查（防关窗后 emit 已删 C++ 对象崩溃）；load_library 代次 _library_epoch +1 随线程携带、回调 epoch 不一致丢弃（防换文件夹混库）；验证：probe_i3 关窗/过期/当前 epoch 三态断言

### I4. 验证与收尾

- [x] I4.1 全量回归（2026-11-05）—— **17/17 probe PASS**（p1/p2/p3/p5/p6/g0/g1/g2/g3/h0/h1/h2/h3 + i0/i1/i2/i3）+ 冒烟 import 全模块 OK + GUI 无头初始化 OK + layout_i.png（1650×800）定稿；**多模态读图核对完成**（2026-11-05）：layout_i.png 与 layout_h.png 逐项一致（五列布局/面板/控件/配色零回退）；layout_i_loaded.png 加载态核对（波形渲染+播放头/播放键橙色辉光/Jog 播放指示点/VU 分带点亮）
- [x] I4.2 GUI 实测（2026-11-05，AI 执行 + 用户授权）—— ① CLI 真机分析：`-m modules.analyzer --folder .temp/test_audio` 完整跑通 9/9（I0.1 修复在真实 CLI 路径生效），broken.wav 可读报错降级不中断；② 真实引擎静音端到端（probe_i4_gui，主音量 0）：解码 (N,2)/播放推进/Censor 曲头保持反向/start_mix→MIXING→PLAYING/FX 深度扫动复用实例不崩/VU 采集；③ 加载态截图读图核对（见 I4.1）。注：FX 咔嗒消除的主观听感建议日常使用中复核
- [x] I4.3 文档同步（2026-11-05）—— z.plan A003 标注已修 + 补录项说明、x.progress I 系列勾选、README 修正（I3.4 同步）、版本号 ver 0.25（base.json + README 徽章）
- [x] I4.4 提交 V0.25（2026-11-05，用户授权 AI 执行；w.study.md 预存改动未纳入，另行处理）

## J. M1.7 虚拟控制台完善与外观层任务清单（依据 z.plan.md 附录：M1.7 工作计划 V2）

> 规划：2026-11-05 落盘（方案 2026-08-13 定稿）。批次 0→1→2→3→4 顺序执行；批次 0 尺寸只定基准（缩放因子留批次 4）；每步无头截图 + AI 读图核对（本会话模型已具备视觉能力）+ 用户确认最终视觉。
> 做法说明：—— 做法 为执行要点，先自查代码上下文再动手。

### J0. 批次 0：UI 优化（前置，不动功能与引擎）

- [x] J0.1 布局进配置（2026-11-05）—— `splitter_library_pct`/`splitter_main_pcts` + `spacing_sm/md/lg` 进 ui.json；main_window 网格常量替换散落 6/8/10/12；body/main 加 stretch 因子（双 Deck 拉伸、其余定比）；验证：probe_j0 源码断言无硬编码比例
- [x] J0.2 Browse 顶栏分组（2026-11-05）—— LOAD 组/搜索组/状态组按网格间距分组；LOAD/搜索/打开/目标盘/SHIFT 五控件 Tooltip
- [x] J0.3 部件大小分级进配置（2026-11-05）—— `button_min_width/height` 32×32（GlowButton）、`knob_size_mixer` 32 / `knob_size_fx` 28、`jog_size` 140（钳制 120-180）、`pad_btn_size` 42 全部进 ui.json；验证：probe_j0 断言各控件实际尺寸
- [x] J0.4 原语控件禁用态视觉（2026-11-05）—— GlowButton/RotaryKnob/FaderSlider paintEvent 检查 `isEnabled()` → `setOpacity(0.35)`（灰显统一视觉语言）
- [x] J0.5 部件位置按 FLX4 语义（2026-11-05）—— Deck 区右侧 TEMPO 竖置位（`_tempo_a/b` 禁用推子占位 + 标签，Pitch 滑块保留作量程指示 + Tooltip）；Mixer 底部 PHONES 行（CUE A/B + 平衡/音量占位禁用）；deck_widget Keylock 灰显 + Tooltip"批次 1 接入"
- [x] J0.6 死控件灰显标注（2026-11-05）—— Beat FX AUTO/TAP/CH1/CH2/1+2 五控件禁用 + Tooltip"预留（批次 1 接线）"；拍数 ± 保留（有本地可见反馈，对齐方案 0d 清单；probe_p6 兼容）
- [x] J0.7 操作反馈与状态显性化（2026-11-05）—— `_bind_value_tip` 数值 Tooltip（TRIM/MASTER ×倍率、EQ dB 换算、横推左右占比、DEPTH %）；EFFECTS 区 FX 状态 MiniDisplay（`_update_fx_status`，经 `_apply_beat_fx`/`_toggle_target` 联动，效果名大写对齐硬件小屏观感）
- [x] J0.8 可用性（2026-11-05）—— 空格 = 播放/暂停目标盘（keyPressEvent 实现，子控件持有焦点时不干扰搜索输入）；Ctrl+F 聚焦搜索（QShortcut）；Browse 行 Tab 顺序；窗口标题带版本号
- [x] J0.9 检验（2026-11-05）—— probe_j0 全 PASS + **全量回归 17/17 PASS** + 冒烟 OK + layout_j.png 空载/加载态截图 AI 读图核对（批次 0 改动全部呈现：分组/增大/灰显/TEMPO 位/耳机位/状态小屏，零布局破坏；e2e 静音端到端重跑 PASS——一次 VU=0 为设备瞬时争用非回归）

### J1. 批次 1：功能补齐（2026-11-05 完成；目测项按用户授权闭环）

- [x] J1.1 引擎实时变速与重渲染（P4 闭环）—— `Deck.set_tempo_rate` 乐速倍率（TEMPO 实时变速，插值填充音高随速变化）；Keylock/Key Shift 经 `stretcher.make_tempo_buffer`（恒速 timemap + 可选 --pitch）后台重渲染烘焙（`_apply_rebias`：去抖 300ms + epoch 防陈旧 + MIXING 让路 + `_swap_buffer` 位置域重映射 cue/hot cue/loop/slip/搓碟；keylock 关卸载烘焙回原速域）；`_beat_len` 乘烘焙比保乐理拍长
- [x] J1.2 TEMPO 推子与量程 —— 竖置推子启用 + 量程循环按钮（±6/±10/±16/WIDE，`tempo_ranges` 进 base.json），量程切换保持乐速（滑块重映射）；原 Pitch 滑块转只读反显；手动动推子解除该盘 Beat Sync
- [x] J1.3 Beat Sync —— SYNC 键（deck_widget）：对齐另一盘 `effective_bpm`（乐速倍率钳当前量程内），LED 蓝色；无 BPM 防御提示
- [x] J1.4 循环键行 —— IN/OUT（入点标记→出点闭合激活）/4BEAT/◀减半/▶加倍（`loop_in/loop_out/loop_halve/loop_double` + `loop_active` 公开属性）
- [x] J1.5 Key Shift 真实变调 —— Pad Key Shift 经同一重渲染管线烘焙 --pitch（时长不变位置无损），归零还原
- [x] J1.6 Beat FX 拍数接线 —— `set_fx_beats`：Echo/Delay 延迟 = beats/4 拍（BPM 驱动、钳 1.9s）、Trans 门控周期随拍数；set_tempo/tap 联动重配
- [x] J1.7 Beat FX AUTO/TAP/CH 启用 —— AUTO（曲目 BPM 时基校验）/TAP（点按测速）/CH1/CH2/1+2（FX 作用通道选择，`_apply_beat_fx` 通道化 + 切通道清残留）
- [x] J1.8 耳机监听启用 —— `AudioEngine.ensure_cue_player` 惰性创建（失败降级提示）；CUE A/B 独占预听（`Deck.cue_buffer` 当前位切片）+ 监听音量；平衡旋钮预留（需双源混音 v2）
- [x] J1.9 检验 —— probe_j1 全 PASS（含真实 rubberband Keylock 渲染闭环 + 域重映射断言）+ 全量回归（probe_j0 同步批次 1 后预期）

### J2. 批次 2：Theme 化（2026-11-05 完成）

- [x] J2.1 token 动态化 —— 新建 `ui/palette.py`（token()/color() 运行期现取 + ThemeBus 广播 + ThemeAware 混入统一清缓存刷新）；8 个自绘控件模块级 QColor 常量全部改 paint 时现取
- [x] J2.2 主题注册表 —— dark = ui.json 原生 / light = ui.json + `theme_light` 覆盖表（ui.json 新增浅色 token 集）；themes.py 改 palette 驱动（apply_theme/switch_theme）
- [x] J2.3 切换入口 —— Ctrl+T 运行期循环切换（token 表 + QSS 重建 + 静态 LED 重涂 `_apply_static_leds` + FX 效果键 `reapply_leds`），全控件刷新无重启
- [x] J2.4 检验 —— probe_j2 全 PASS（token 切换/未知主题拒绝/缓存失效/双主题渲染/截图）+ layout_j2_light.png 读图核对（浅色协调、Jog 金属与中心屏本色保留）

### J3. 批次 3：贴图拟物化（A 路线，2026-11-05 完成）

- [x] J3.1 程序化贴图缓存 —— 新建 `ui/widgets/_textures.py`：拉丝金属纹理离线渲染 → PNG 磁盘缓存（cache/ui_textures/，gitignore 可重建），三级查找 内存→磁盘→现渲染；键 = 名称_主题_尺寸（主题/分辨率天然隔离）
- [x] J3.2 PanelFrame 贴图底 —— 渐变+拉丝线程序化绘制替换为贴图 drawPixmap（裁剪圆角），高光带/描边保留；主题切换随缓存失效自动换贴图
- [x] J3.3 检验 —— probe_j34 J3 段全 PASS（写盘/回读/主题键控/渲染）+ 贴图文件落盘确认

### J4. 批次 4：大小缩放（2026-11-05 完成）

- [x] J4.1 全局缩放 —— 新建 `ui/scale.py`（`s()` 统一换算，ui.json `ui_scale` 启动读取）；应用到 GlowButton 最小尺寸/RotaryKnob/FaderSlider/LedStrip/MiniDisplay/Jog/Pad/间距网格/TEMPO 与横推长度/FX 小屏
- [x] J4.2 检验 —— probe_j34 J4 段全 PASS（monkeypatch SCALE=1.5 全控件尺寸 ×1.5 + 缩放态渲染）；默认 1.0 行为不变

---

# PL/FIX/PATCH 任务轨道（2026-11-05 起：三线编号，规则见 AGENTS.md 任务清单纪律；以上字母系列封存仅作历史勾选依据）

## 已完成 ✅

### PL001: UI 评审修复（截断与列宽 / 面板补丁 / 激活态层级） [评审 2026-11-05 → z.plan.md 附录 PL001] ✅

> 结果：probe_pl001 全 PASS + 22/22 探针回归 + after 截图核对全过；执行中升级两处根因（GlowButton 无 sizeHint 覆写、五列最小宽超主区→Pad 全宽化 + mins/shares 机制）；遗留 PanelFrame 标题重叠记 y.problem#P5。16/16 条勾结，已随 V0.2.6.1 提交推送（98ae909）。详见 z.plan.md 附录 PL001。

> 来源：taste-skill（app-screens 模式）UI 评审，overall 6.0，Top3 = 截断与列宽 / 面板补丁与状态诚实 / 激活态层级。方案（四组措施 + 验证方案）见 z.plan.md 附录 PL001，做法均已到文件/函数级。
> 执行约定：走 progress-task 流程——每条先写探针断言（先 FAIL 后 PASS）再实现；before 截图已存 `.temp/ui_preview/review/`，收尾出 after 对比；不动引擎层与配色 token 值。

#### 组 A：截断与列宽

- [x] PL001.1 splitter 列宽下限与比例重申 —— `ui/main_window.py _build_ui()`：曲库/deck/mixer/effects 四面板 `setMinimumWidth(260/420/230/250)`；新增 `_apply_splitter_sizes()` 集中 body/main 两级 `setSizes`，构造调用一次 + `QTimer.singleShot(0, ...)` show 后重申（曲库塌缩根因 = show 后 sizeHint 重算覆盖初始比例）；验证：probe_pl001 断言 1650×800 show 后 `library_panel.width() >= 260`（先 FAIL 后 PASS）（2026-11-05 已验证：show 后曲库 320/deck 422/effects 290（probe 断言过））
- [x] PL001.2 GlowButton 文本自适应缩字 —— `ui/widgets/glow_button.py paintEvent()`：elide 前按 `QFontMetrics.horizontalAdvance(text)` 与可用宽比较，超宽字号降一档（pointSize-1，最低 8）再 elide；验证：probe_pl001 对 LOAD A/B、FX 5 键、CH 3 键、模式 5 键、FaderStart/Tap、PHONES 2 键断言 `horizontalAdvance(text) <= width()-6`（先 FAIL——当前 Tr…/Ec…/Beat L… 截断复现——后 PASS）（2026-11-05 已验证：22 键 text_fits 全过；根因 = 无 sizeHint 覆写（补文本驱动 hint））
- [x] PL001.3 BeatFxWidget 效果/通道两行布局 —— `ui/beat_fx_widget.py __init__()`：row1 拆 `fx_row`（FX+效果 5 键）与 `ch_row`（CH1/CH2/1+2）两行；AUTO/TAP 保持 row2 右置；验证：probe_pl001 断言 FX 键文本完整 + 截图目检两行不溢出（2026-11-05 已验证：FX/CH 两行 + 8pt + 去 FX 标签 + 边距归零，5 键全完整）
- [x] PL001.4 Pad 模式键硬件短名 —— `ui/pad_widget.py`：新增 `PAD_MODE_LABELS = {"Beat Loop": "LOOP", "Beat Jump": "JUMP", "Sampler": "SMP", "Key Shift": "KEY", "Hot Cue": "CUE"}`（信号值 PAD_MODES 不变），模式键构造文本用 LABELS，`_select_mode`/`_apply_mode_color`/main_window `_on_pad` 逻辑零改动；验证：probe_pl001 断言模式键文本完整 + 点击发原模式值（行为等价）（2026-11-05 已验证：短名 CUE/LOOP/JUMP/SMP/KEY，业务值不变（行为等价断言过））
- [x] PL001.5 Mixer/PHONES 按钮短名 —— `ui/main_window.py _build_mixer_panel()`：FaderStart 文本 `{label} FS`、Tap 文本 `TAP`；PHONES 键 `CUE A/B`→`CA`/`CB`（tooltip 全名保留）；验证：probe_pl001 文本完整断言 + tooltip 非空断言（2026-11-05 已验证：A FS/B FS/TAP/CA/CB 全完整，tooltip 全名保留）

#### 组 B：面板补丁与状态诚实

- [x] PL001.6 QSS 背景作用域改造 —— `ui/themes.py _build_qss()`：删 `QMainWindow, QWidget { background: {bg} }` 全局实底，改全局 `QWidget { background: transparent; color: {fg}; }` + 定点实底（QTableWidget/QLineEdit/QStatusBar/QMainWindow 保留 bg）；验证：probe_pl001 源码断言无全局 QWidget 实底规则 + dark/light 双主题 grab 不崩 + QTableWidget/QLineEdit 仍有实底（浅色可读）——**B1 后重截 zoom_mixer 定位 EQ/横推残留色块（B2 前置）**（2026-11-05 已验证：全局透明 + 定点实底，双主题应用过，表/输入框实底在）
- [x] PL001.7 Mixer 残留色块清除 —— B1 后若 EQ 标签下 90×70 / 横推旁 120×200 色块仍残留：`.temp/probe_block.py` objectName 临时描边逐容器排除（候选：row2 拉伸 QLabel、xf_col 横推标签被 stretch 拉高）；修复（横推标签 `xf_col.addWidget(QLabel, 0, Qt.AlignHCenter)` + 行高固定等）；验证：after 截图 zoom_mixer 无色块（目检）（2026-11-05 已验证：B1 后色块自愈消失（zoom_mixer 目检），无遗留）
- [x] PL001.8 LedStrip 未亮段可见框架 —— `ui/widgets/led_strip.py _segment_color()` 未亮分支 `panel_inset`→`panel_edge` + `paintEvent()` 段顶 1px 6% 白描边；验证：probe_pl001 断言未亮段色 == panel_edge + zoom_mixer 截图 VU 框架目检可见（2026-11-05 已验证：未亮段=panel_edge+描边，VU 框架暗面板可见（截图目检））
- [x] PL001.9 Jog 中心屏重叠修复 —— `ui/jog_wheel.py`：Vinyl checkbox 改独立行（圆盘 paintEvent 圆心 y 下移 checkbox 高/2 + 半径同步收缩，或 checkbox 移底部 18px 头部行，实现取简）；验证：probe_pl001 断言 checkbox geometry 与中心屏文本区不相交 + zoom_deck_a 截图 "---- BPM" 无叠字（先 FAIL——当前重叠复现——后 PASS）（2026-11-05 已验证：checkbox 钉顶部（AlignTop），中心屏 20.0 BPM 无叠字（相交断言过））

#### 组 C：激活态层级

- [x] PL001.10 效果键初始橙光 —— `ui/beat_fx_widget.py __init__()` 末尾补调 `self._select_fx("HPF")`；验证：probe_pl001 断言构造后 HPF 键 `_led_color == QColor(ui.json glow_orange)`（先 FAIL——当前白光——后 PASS）（2026-11-05 已验证：构造即 _select_fx(HPF)，初始橙光（断言过））
- [x] PL001.11 激活辉光分档 + FX ON 描边激活 —— `ui/widgets/glow_button.py paintEvent()`：`isChecked()`（非按压）态辉光半径 ×0.85、外圈 alpha 220→150（按压/LED 常亮不变）；FX ON 描边激活：`ui/beat_fx_widget.py` 构造 FX ON 时启用新描边模式（checked 画 1.5px led 色圆角描边 + 文字亮色，不整面辉光），主操作唯一性还给 Mix Now；验证：probe_pl001 断言 checked 态绘制参数分档生效 + zoom_effects 截图目检（2026-11-05 已验证：_glow_params 三档 + FX ON 描边激活（断言+目检））
- [x] PL001.12 Pitch 滑块拟物化 —— `ui/deck_widget.py`：QSlider → `FaderSlider(-8, 8, 0, Qt.Horizontal, length=200)`；`set_pitch_display()` 改 `set_value` + blockSignals 防回环；`ui/themes.py` 清 QSlider QSS 规则；验证：probe_pl001 断言 pitch 控件 isinstance FaderSlider + set_pitch_display 后 slider 值正确且不 emit pitch_changed + zoom_deck_a 截图目检（2026-11-05 已验证：Pitch=FaderSlider，反显 3.5 不回环（断言过））
- [x] PL001.13 曲库空态引导 —— `ui/main_window.py _build_ui()`：曲库表格上叠居中 QLabel（silk 12px）"打开文件夹加载曲库 · 双击曲目加载到目标盘"，`load_library()` 追加行后 `setVisible(False)`；验证：probe_pl001 断言空库时引导可见、加载后隐藏（2026-11-05 已验证：空库引导句可见、加载后隐藏（断言过））
- [x] PL001.14 light 主题辉光降档 —— `ui/widgets/glow_button.py paintEvent()`：辉光 alpha 按 `palette.current()` 分档（dark 220 / light 150，中心 110/70）；验证：probe_pl001 断言 light 下 alpha 参数 + light_loaded 截图目检光晕不发脏（2026-11-05 已验证：light 辉光 150/70 < dark 220/110（断言过））

#### 组 E：检验与收尾

- [x] PL001.15 探针与全量回归 —— 新建 `.temp/probe_pl001.py`（组 A-D 全部断言，TDD 先 FAIL 后 PASS）；全量 21 既有探针重跑 PASS（p5/p6/j0 的文本/布局断言随 A2-A5 同步更新）；冒烟 import；验证：RESULT 全 PASS（2026-11-05 已验证：probe_pl001 全 PASS + 22/22 探针回归 + 冒烟 OK）
- [x] PL001.16 after 截图对比与文档 —— 重跑 `.temp/review_shots.py` 出 after 组（dark 空载/加载、light 加载、三特写）与 before 逐项目检（截断清零/无色块/VU 框架/Jog 无叠字/FX ON 描边/空态引导）；多模态读图核对；文档同步（本组勾选 + z.plan 附录 PL001 状态回写 + README 徽章随版本）；提交（四段式 V0.2.6.1，用户执行）（2026-11-05 已验证：after 截图 dark/light×3 特写目检全过；说明区 8 文件同步；y.problem 补 P5）

## 未完成

### PL002: M2 AI 自动 DJ（兼容性评分 / Camelot 选曲 / Set 规划 / 自动转场） [plan#M2 → z.plan.md 附录 PL002]

> 方案（设计决策/五组措施/验证方案/边界）见 z.plan.md 附录 PL002；核心 = `modules/automix.py` 占位转正（确定性贪心编排，非 LLM）+ 分析器 timbre 字段（缓存 V2）+ TransitionManager 桥与自动循环 + Effects 推荐区 UI。人声冲突维度明确不做（依赖缺位，里程碑偏差已记录）。
> 执行约定：评分/规划/解析全为纯函数 TDD（先 FAIL 后 PASS）；桥接用假引擎；全量回归关注 g1/i2 缓存断言（V2 首跑重分析属预期）。

#### 组 A：评分核心（automix.py 纯逻辑）

- [x] PL002.1 Camelot 打分表 —— `automix.py` 新增 `key_score(key_a, key_b) -> float`：复用 `analyzer.parse_key`（解析异常 → 0.5 中性）；打分表 = 同键 1.0 / 同字母相邻号 0.9 / 同号异字母 0.85 / 对角相邻 0.6 / 其余 0.2 / 任一 "?" 0.5（模块级 `_KEY_SCORES` 常量）；验证：probe_pl002_score 打分表全用例（先 FAIL——占位恒 0.5——后 PASS）（2026-11-05 已验证：打分表全用例过（含双记谱归一 _parse_key_any——占位红灯后实现））
- [x] PL002.2 维度分与聚合 —— `automix.py` 新增 `bpm_score`（复用 transition.fold_ratio：r_eff==1→1.0 / half/double→0.75 / 线性衰减 / bpm≤0→0.4）、`energy_score`（exp(-(Δ/2)²)、缺→0.5）、`timbre_score`（欧氏距离高斯、缺→0.5）+ 重写占位 `compatibility_score(track_a, track_b) -> {overall, scores, warnings}`（四维加权 `base.json automix_weights`，维度缺失入 warnings）；验证：probe_pl002_score 聚合与权重断言（2026-11-05 已验证：四维分+聚合+warnings 过；权重配置和=1（automix_weights））
- [x] PL002.3 评分探针 —— 新建 `.temp/probe_pl002_score.py`（~15 断言：打分表/倍速/中性值/权重和=1/缺失中性），首跑红灯；验证：转绿 RESULT PASS（2026-11-05 已验证：probe_pl002_score PASS（首跑 ImportError 红灯→转绿））

#### 组 B：分析扩展与曲库接入

- [x] PL002.4 音色概要字段 —— `analyzer.py` 新增 `_detect_timbre(y, sr) -> [c, b, r]`（spectral_centroid/bandwidth/rolloff(0.85) 全程均值按固定参考范围归一 [200,6000]/[200,4000]/[1000,10000]Hz）；`analyze_file` 组装 `record["timbre"]`；`ANALYSIS_VERSION = 2`（旧缓存自动失效重分析）；验证：probe 断言 440Hz 正弦 vs 白噪质心分离 + 版本失效路径（2026-11-05 已验证：timbre 三维归一（正弦/白噪质心分离断言过）；ANALYSIS_VERSION=2）
- [x] PL002.5 艺人解析与条目构造 —— `library.py` 占位转正：新增 `parse_artist(path) -> str | None`（Path.stem 首个 " - " 分割取左段；空/超 40 字 → None）与 `entry_from(path, record) -> dict`（`{path, name, artist, bpm, key, energy, timbre, record}`）；验证：probe_pl002_score 补文件名用例（标准/无分隔/超长/中文）（2026-11-05 已验证：parse_artist/entry_from 全用例过（标准/无分隔/超长/中文/空记录））
- [x] PL002.6 UI 曲库迁移 —— `main_window.py`：`_append_row`/Instant Doubles 的条目构造改调 `library.entry_from`（`_library` 条目新增 name/artist/timbre 字段，表格五列渲染不变）；验证：冒烟 + probe_g1（表头/兼容标记）不回归（2026-11-05 已验证：_append_row 走 entry_from；probe_g1 表头/兼容标记不回归）

#### 组 C：Set 规划（automix.py 纯逻辑）

- [x] PL002.7 弧线与贪心链 —— `automix.py` 新增 `plan_set(entries, start, length) -> {sequence, explanations, warnings, arc}`：能量弧线目标 `base.json automix_energy_arc=[0.5,0.8,1.0,1.0,0.7]` 按 length 归一插值；每步评分 = `overall × exp(-|e_now - arc_i|/0.3)` 取最高；约束 = 已播去重 + 同艺人间隔 `automix_same_artist_gap=3`（候选不足降级并 warnings 声明）；explanation 列贡献前二的维度（如 "Key 8A→8B 关系调；BPM 倍频"）；验证：probe_pl002_set（先 FAIL 后 PASS）（2026-11-05 已验证：plan_set 贪心链全断言过（max 稳定取首防同分 dict 比较 TypeError））
- [x] PL002.8 Set 探针 —— 新建 `.temp/probe_pl002_set.py`：合成 8 曲曲库（可控 BPM/Key/energy/artist）断言序列长度/去重/同艺人间隔/弧线贴合/explanation 非空；验证：转绿 RESULT PASS（2026-11-05 已验证：probe_pl002_set PASS（S9 用例修正：3 曲库 length=2））

#### 组 D：自动转场调度与 UI 接入

- [x] PL002.9 推荐桥 AutomixController —— `automix.py` 新增 `class AutomixController`：`__init__(tm, entries_getter)` / `recommend(now_meta) -> {entry, explanation} | None` / `auto_mode` 开关 / `on_mix_started()`（自动模式记录已播 + 经 `tm.prepare` 链式装填下一曲，cue=下一曲首 downbeat 或 0）；验证：probe_pl002_bridge 假 tm 断言调用序列（2026-11-05 已验证：Controller recommend 排除自身/已播、无 BPM None、prepare_next 经 tm 断言过）
- [x] PL002.10 转场 EQ 渐变 —— `transition_manager.py mix_now()`：启动后守护线程 8 步 × fade/10 调 `now_deck.eq.set_low(-1 → 0)`（末步恢复；mark_stale/新 mix 抢占时线程退出）；**回调线程零改动**（纪律不破）；验证：probe_pl002_bridge 断言渐变首末值与线程退出（2026-11-05 已验证：EQ 渐变首末值+token 抢占退出断言过；scheduled 延迟到触发；回调零改动）
- [x] PL002.11 自动循环接线 —— `main_window.py`：`_on_mix` 成功后若 `auto_mode` 调 `on_mix_started()` 链式 prepare；手动 Prepare/Load 置 `auto_mode=False` + 状态栏提示（防双源）；`closeEvent` 停控制器；验证：probe_pl002_bridge 手动操作退出自动模式断言（2026-11-05 已验证：手动 Prepare/Load/InstantDoubles 退出 AUTO（_set_automix_ui 三同步——修 checked 与 LED 脱节）；closeEvent 停）
- [x] PL002.12 UI 推荐区 —— `main_window._build_effects_panel()`：Prepare 按钮上方加推荐行（MiniDisplay 推荐曲名 + QLabel explanation 摘要 + `Auto Next` GlowButton 单次推荐装填 + `AUTO` GlowButton 勾选自动模式蓝色 LED）；接线 `_on_recommend/_toggle_automix`；验证：probe_pl002_bridge 控件存在与信号 + 截图目检（2026-11-05 已验证：推荐区窄列适配（110 小屏+NEXT 短名，explanation 独立行）截图完整可读）
- [x] PL002.13 桥接探针 —— 新建 `.temp/probe_pl002_bridge.py`（假引擎+假 tm：recommend 选择/链式 prepare 序列/EQ 渐变首末值/手动退出自动模式）；验证：转绿 RESULT PASS（2026-11-05 已验证：probe_pl002_bridge PASS（R1-R6/E1-E3/L1-L4））

#### 组 E：检验与收尾

- [x] PL002.14 全量回归 —— probe_pl002_score/set/bridge 全 PASS + 既有 22 探针重跑（g1/i2 缓存断言观察 V2 重分析自愈）+ 冒烟 + Effects 推荐区截图；验证：RESULT 全 PASS（2026-11-05 已验证：25/25 探针 PASS（22 回归+3 新）+ 冒烟 OK + Effects 截图读图）
- [x] PL002.15 文档与提交 —— README 特性补 M2 段落、z.plan 里程碑 M2 勾选 + 本附录状态回写、x.progress 勾选、live 用户验收（真曲库 Auto Next 单步 + AUTO 短 Set 听感）、提交（四段式 V0.2.7.0，用户执行）（2026-11-05 已验证：README M2 段落/本组勾选/附录状态回写完成；提交 736029c + 版本收口 aa0c9c1 已推送；**2026-11-06 用户 live 听感验收通过**）

## PATCH（小修小改轨道）

### PATCH001: UI 小修与对拍可视化（面板标题占位 / 曲库列宽 / 波形下拍网格） [用户 2026-11-06 → z.plan.md 附录 PATCH001]

> 三件小修：P5 面板标题重叠（y.problem#P5 转实施）、曲库"调性/能量"列被裁（PL001 评审遗留）、波形下拍网格（M2 对拍可视化）。方案见 z.plan.md 附录 PATCH001。

- [x] PATCH001.1 面板标题占位 —— `panel_frame.py` 新增 `CONTENT_TOP_MARGIN = 26`；`main_window.py` 五处面板内容布局顶边距改用之（browse/lib/deck/mixer/effects）；验证：probe 断言面板首子控件 y ≥ 26（先 FAIL 后 PASS）（2026-11-06 已验证：CONTENT_TOP_MARGIN=26 常量 + 五面板顶边距接入；probe 断言首子控件 y≥26（deck/mixer/effects 全过））
- [x] PATCH001.2 曲库列宽 —— `_build_ui()` 表格建列后固定宽（状态 40/BPM 60/调性 64/能量 48，曲名弹性）；验证：probe 断言四列宽和 ≤ 库面板内容宽（先 FAIL——当前调性/能量被裁——后 PASS）（2026-11-06 已验证：定宽 40/60/64/48 + 曲名弹性；断言四列和 ≤ 库面板内容宽（调性/能量可见））
- [x] PATCH001.3 波形下拍网格 —— `waveform_widget.py` 新增 `set_grid(downbeats)` + `paintEvent` 包络前画 accent alpha 40 竖线（样本→x 按 _duration 映射）；`main_window` 两处装填传 `downbeats`；验证：probe 断言网格存储/映射/换曲更新 + 截图目检（2026-11-06 已验证：set_grid + 包络前 alpha 40 竖线；存储/映射/换曲断言过；探针抓出 paintEvent 变量顺序 NameError（真 GUI 崩溃）已修；密集包络段网格被淹没属预期权衡（安静段可见））
- [x] PATCH001.4 检验与收尾 —— `.temp/probe_patch001.py` 全 PASS + 25 探针回归 + 冒烟 + 截图读图；y.problem P5 改 ✅；文档同步；提交（feat: V0.2.7.2）（2026-11-06 已验证：probe_patch001 PASS + 25/25 回归（j0 版本断言同步 0.2.7）+ 冒烟 + 截图读图（标题占位/列宽目检过）；y.problem P5 ✅）

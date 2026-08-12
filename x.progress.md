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

# MrAutoDJ 项目说明

Python 桌面 DJ 应用，三步路线：虚拟 DJ 台（双打碟机/波形/EQ/横推）→ AI 自动 DJ（调和混音/自动转场/Set 规划）→ Claude 电台（LLM 报幕 + 点歌互动）。GUI 用 PySide6，中文注释为主。验证以无头探针（`.temp/probe_*.py`）全量回归 + 冒烟 import 为门禁，无独立 lint 脚本与构建步骤。

> **文档分工**（2026-11-05 对齐 CapsulePulse 规范）：进度与任务清单看 `x.progress.md`、方案与审计归档看 `z.plan.md`、问题备忘看 `y.problem.md`、源码研读沉淀看 `w.study.md`；本文件不承担项目状态行职责。

## 运行与验证

- 入口 `main.py`：GUI 为默认模式；版本单一来源在 `config/static/base.json` 的 `version` 字段（三段式 `X.Y.Z`），其他模块用 `get_static_config().base["version"]` 引用
- **提交前全量门禁（硬性工作流）**：改动涉及 `modules/`、`ui/`、`utils/`、`config/` 的提交，提交前必须跑全量探针回归（`.temp/` 下既有 probe 逐个 RESULT PASS）+ 冒烟 import（下方命令清单）+ 涉及视觉的出截图核对；不通过不得宣称完成，环境缺依赖先报告用户、不得静默跳过
- 没有测试/lint 命令。改动后验证（冒烟 import 全模块清单——FIX005.15 补全，新增模块须同步回填）：`.\.venv\Scripts\python.exe -c "import main, modules.engine, modules.analyzer, modules.library, modules.automix, modules.radio, modules.stretcher, modules.transition, modules.transition_manager, config.settings, config.static.static_config, ui.main_window, ui.beat_fx_widget, ui.deck_widget, ui.jog_wheel, ui.pad_widget, ui.palette, ui.scale, ui.shift_state, ui.themes, ui.waveform_widget, ui.widgets._skins, ui.widgets._textures, ui.widgets.fader_slider, ui.widgets.glow_button, ui.widgets.led_strip, ui.widgets.mini_display, ui.widgets.panel_frame, ui.widgets.rotary_knob, utils.logger, utils.file_utils, utils.retry, utils.convert, utils.audio_decode"`。不要直接跑 GUI 验证（会弹窗阻塞）；涉及解码链路（pydub 为延迟导入，import 冒烟测不出）另跑真实解码断言：合成 wav → `decode_audio` 查幅度
- GUI 无头初始化验证（不弹窗）：`$env:QT_QPA_PLATFORM="offscreen"; .\.venv\Scripts\python.exe -c "from PySide6.QtWidgets import QApplication; from ui.main_window import MainWindow; app = QApplication([]); w = MainWindow(); print('GUI init OK')"`
- 依赖（`requirements.txt`）：PySide6、sounddevice、librosa 等，按需添加（见 z.plan.md 技术栈）

## 环境陷阱

- `.venv` 是机器绑定的：`pyvenv.cfg` 的 `home` 指向创建时机器的 Python 路径。换机器/换用户后解释器损坏，症状是 VSCode Python 扩展报 `write EPIPE / Shutting down server`（Jedi 语言服务器无法启动）。重建：`Remove-Item -Recurse -Force .venv; py -3.14 -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt`，然后在 VSCode 重选解释器
- opencode 的 pylsp 配置在 `.opencode/opencode.json`，路径硬编码为 `E:\CodeMission\MrAutoDJ\.venv\Scripts\python.exe`——换机器需同步修改
- 音频设备：sounddevice 在 WSL 下无设备（需 WSLg）；Windows 原生运行
- **Mimosa 安全钩子**（2026-11-05 实测沉淀）：① Bash 内直接写源码/配置（`sed -i`/`cp`/重定向等）会被 PreToolUse 钩子拒绝——**修改既有文件一律用 edit 类工具精确替换**，钩子借此对候选代码做安全检查；② `git commit` 前钩子自动扫描改动，高危发现会强制拦截（如路径穿越类模式）——修复后重试即可通过，软警告（扫描结论不完整）按兼容策略放行但不得宣称"项目安全"；③ 补跑完整扫描用 Mimosa 扫描工具，报告落仓库外
- 探针/验证脚本对音频设备有依赖（VU 采集、输出流）——设备被占用或瞬时不可用会出现偶发 FAIL，先复跑一次排除设备争用再判代码回归

## 结构与约定

- 包结构按依赖单向分层（参考 mrboard / AccelWorld）：`utils/` 通用工具（logger/file_utils/retry/convert，无业务依赖）→ `config/` 配置 → `modules/` 业务核心（engine 音频引擎、analyzer 曲目分析、library 曲库、automix AI 编排、radio 电台调度，无 GUI 依赖）→ `ui/` 界面（main_window 主窗口、deck_widget 打碟机、waveform_widget 波形、themes 主题 QSS）→ `data/` 静态数据
- `config/` 配置分两类（对齐 mrboard）：
  - **静态配置**（`config/static/`，只读，json 驱动）：`static_config.py` 加载器 + `config.json` 引导映射表 + `base.json`（应用参数：版本/采样率/块大小/缓存路径等）+ `ui.json`（UI 参数：颜色/阈值/表头）；模块顶层 `_SC = get_static_config()` 一次性解包，运行时零 IO
  - **用户配置**（`config/settings.py`，可读写）：AppConfig dataclass，存项目内 `config/user_config.json`（路径由 base.json `user_config_path` 指定）
- **参数约定**：可调参数一律走 `config/static/*.json`，禁止代码硬编码；版本号唯一来源为 `base.json` 的 `version` 字段
- `main.py` 收编 GUI 分发；模块间顶层 import，不要使用函数内延迟 import（librosa 等重依赖除外，可在函数内导入）
- 提交信息按 Git 注意章节的 Commit 提交规范书写（四段式版本，如 `feat: V0.2.6.1，摘要...`）
- 项目规划与方案文档在 `z.plan.md`，源码研读报告在 `w.study.md`，任务清单在 `x.progress.md`
- `.agents/skills/` 为项目 skill 目录（**不入版本控制**，2026-11-06 定案；本地八件：自建 audit-project / audit-report / progress-task + 工具 opencode-skill-creator + 引入 taste-skill / qa-review / diagram-design / collection-curator——源 F:\Collection）；skill 只描述能力与流程，规范权威源在 AGENTS.md
- `.reference/` 目录是外部项目的 git clone（浅克隆），**不纳入本仓库版本控制**；需要更新时重新 clone

## 任务清单纪律（x.progress.md，2026-11-05 定案，对齐 CapsulePulse）

> 适用边界：**自此定案起新立的任务**按本节三线编号轨道执行；既有 D/E/F/G/H/I/J 字母系列**编号与格式原样保留、不再追加**（已完成内容是历史勾选依据，只增不删）。

- **条目做法必须写到文件/函数级**：`—— 做法` 部分指明改哪个文件、哪个函数/模块、新增什么结构/键/方法、怎么改（细到可照做）；禁止一句话概括后只留验证方式
- **验证方式必须可执行、可断言**：写明探针名/断言项/命令/live 步骤；TDD 任务先写红灯探针再实现（修复前 FAIL 复现、修复后 PASS）
- **编号轨道三线**（自系列项目 CapsulePulse 引入）：`PL{NNN}` 功能里程碑 / `FIX{NNN}` 审计修复（由 audit-report 归档生成）/ `PATCH{NNN}` 小修小改——用户日常提出的小功能与小调整（不源自审计、不走审计轮），编号自下一可用号递增；方案入 z.plan.md 附录、执行条目入 x.progress.md 任务组，做法/验证标准与 PL 同规
- **A/FIX 编号绑定**：审计报告附录 `A{NNN}` 与其修复任务组 `FIX{NNN}` **恒同号**；取号 = 下一可用号（`max+1`，A 侧不独立取号）；轮次叙述（"第 N 轮"）与编号解耦——FIX 号被非审计批占用时审计顺延取号防撞号（既有 A001/A002/A003 与 G/H/I 系列的历史对应关系不变）
- **已完成组全量保留、只增不删**；任务组从上到下 = 从旧到新，新组追加在区末尾（详见 x.progress.md 头部规则）
- 勾选注记：条目完成时改 `[x]`，句尾追加 `（YYYY-MM-DD 已验证：{一句话结论}）`——结论如实，不达标不降级宣布
- 立项方案（z.plan 附录）的实现措施与任务条目同标准：一律拆到文件/函数级

## 工程原则（设计哲学，所有项目通用）

> 设计哲学总纲（与 CapsulePulse 同源）；下文"代码规范"为项目细则，两者冲突时以本项目边界为准。

### 核心思想

- 以第一性原理思考问题：理解需求背后的真实目标，而非直接套用已有模式或技术方案
- 优先解决本质问题，避免为假设中的未来需求提前设计复杂系统
- 在保证长期可维护性的前提下，选择当前最简单、可靠、清晰的实现方案

### 简洁与设计

- 遵循 KISS：优先选择简单直接的实现，避免不必要的复杂度
- 遵循 DRY：避免重复逻辑，但不要为了消除少量重复而创建过度抽象
- 遵循 SOLID 思想：职责清晰、降低模块耦合，提高可维护性和扩展能力

### 架构

- 不长期保留废弃方案：优先删除过时代码，而不是增加兼容层、fallback 或临时迁移逻辑
- 不进行未经验证的架构设计：避免提前引入抽象、配置和间接层
- 从最小可工作的版本开始逐步演进，每次修改建立在已有可运行系统之上
- 永远不要用未来可能需要的复杂性，牺牲当前产品的可用性

### 代码质量

- 保持模块职责明确，避免一个模块承担过多职责
- 优先使用成熟、稳定、维护良好的第三方库，而不是重复造轮子
- 使用项目已有依赖解决问题之前，不要随意新增依赖
- 在引入新方案前，先检查已有代码、依赖、文档和能力
- 避免为了"看起来更优雅"而增加实际复杂度

### 工程决策

- 优先选择长期可维护的方案，而不是只能临时运行的解决方案
- 代码应该服务于业务目标，而不是为了展示技术复杂度
- 如果简单方案已经满足需求，不要主动升级为复杂方案

## 代码规范

### 错误策略（参考研读报告 w.study.md C4 章）

常驻桌面应用 + 音频实时线程的错误处理主线：**不崩溃、不阻塞、有提示、能自愈**。

- 统一错误类型：业务错误定义分类异常，携带中文消息；UI 只认分类不认细节
- 引擎实时线程纪律：音频回调内**零 IO、零分配、锁内操作保持短**；回调异常 fail-soft（静音降级），绝不抛出到 UI 线程
- 降级不中断：分析失败返回 `empty_record()`（bpm=0/key="?"），单曲失败不影响曲库加载
- 缓存兜底：网络/分析失败返回上次缓存数据 + 标注来源，不显示空白
- 宽容解析：外部数据（分析结果、配置）数字字段弹性转换，坏 JSON 返回空不崩溃，None 语义区分"未记录"与 0
- 节流 + 去重：非必要不频繁刷新；in-flight 去重
- 保留旧数据：刷新失败保留旧视图，成功后视图才替换
- 只读防误写：分析缓存数据库**消费侧**只读（未来任何外部消费方必须开 `file:...?mode=ro` + uri=True 只读连接）；缓存库当前仅经 AnalysisCache 单一连接读写（FIX005/A5 裁决对齐实现——原"专用短连接"表述与实现不符）
- 渲染进度回调异常静默忽略（FIX005/S2 登记，stretcher `_safe_progress`）：场景——rubberband 渲染的进度回调（UI 层注入）抛错；降级行为——异常吞掉、渲染本体照常完成；理由——进度显示是装饰层，回调失败不得杀死渲染线程
- **容错登记制**（2026-11-05 对齐 CapsulePulse）：以上降级条目即本项目的容错白名单——**新增任何静默兜底/降级必须先在此登记**，写明场景、降级行为与理由三要素；未登记的静默吞错一律按规范违反处理（错误要么向上传播、要么明确记录）

### 函数注释规则

- 每个函数定义下方紧跟 `#` 注释，说明该函数的用途和核心逻辑（1-3 行）
- **禁止使用 docstring（三引号字符串）替代 `#` 注释**——函数/类/模块文档统一走 `#` 注释体系，docstring 不承担注释职责；单行 docstring 当注释用属于违规
- 每个 `.py` 文件末尾必须有完整的函数逻辑说明区，用 `# =====` 分隔，涵盖文件中所有函数/模块级常量：
  - 输入、输出、逻辑步骤
  - 设计理由（为什么这样做）
  - 异常处理说明
  - 关联的配置或外部依赖

### 代码约定

- 注释必须用 `#`，禁止 `//` 或其他语言注释符号；所有注释使用中文
- **正式程序文件（main.py 及 modules/、ui/、utils/、config/ 下的 .py）的注释中禁止出现任何与 `.reference/` 相关的参考标注**（如"参考：.reference/…"、"照抄自…"等）；参考来源信息只允许写在 `.temp/` 临时脚本或文档（w.study.md / x.progress.md）中
- 命名风格：函数/变量用 `snake_case`，类用 `CamelCase`，常量用 `UPPER_CASE`
- `_` 前缀：函数名前加 `_` 表示模块内部私用，如 `_format_tokens()`，外部模块不应直接调用
- `def main()`：每个可独立运行的脚本都有 `main()` + `if __name__ == "__main__": main()`
- 类型注解：优先使用 Python 类型注解，包括 `typing` 模块和 `| None` 语法
- dataclass：配置聚合优先用 `@dataclass`
- import 顺序：标准库 → 第三方库 → 本地模块，每组之间空行分隔
- f-string：字符串格式化优先用 f-string，避免 `.format()` 或 `%`
- 推导式：优先用列表/字典推导式而非手写 for 循环构建集合
- 布尔值判断：用 `if x:` / `if not x:` 而非 `if x == True:` / `if x is False:`
- 空值判断：用 `if x is None:` / `if x is not None:` 而非 `if x == None:`
- 异常捕获：避免裸 `except:`，至少用 `except Exception:`，指定具体异常类型更好；捕获多个异常类型可用 `except (Exc1, Exc2):`
- 行长度：每行尽量不超过 100 字符（超过时在运算符或逗号后换行）
- 空格约定：逗号后加空格、冒号前不加空格（切片冒号两侧不加）、赋值/比较运算符两侧加空格、函数定义前后各空两行、类定义前后各空两行、方法之间空一行
- 字符串引号：普通字符串用双引号，文档字符串用 `"""` 三引号；f-string 内含大量双引号时允许外层使用单引号
- 路径处理：强制使用 `pathlib` 代替 `os.path`
- 临时文件：所有临时生成的脚本/文件必须写入项目根目录下的 `.temp/` 文件夹（已 gitignore）
- **禁止以注释替代类型**：能用类型注解表达的约束（`int | None`、`Callable`、`Literal`）不写进注释；单行 `#` 注释用于解释"为什么"，不复述代码本身做什么
- **文件修改必须用 edit 类工具**：修改既有文件（.py/.md/.json）一律用 edit 的精确 oldString/newString 替换，**禁止用 Bash 内 sed/python -c/重定向改文件**（易踩引号/缩进坑，且绕过 Mimosa 安全扫描——钩子会直接拒绝）；新建 .temp 探针脚本不受限
- **版本双轨**（2026-11-05 对齐 CapsulePulse）：机器版本只存 `config/static/base.json` 的 `version`（三段式 `X.Y.Z`）；对外正式文本**分两类**——**README 徽章用三段式**（值 = base.json 即时推进），**commit 标题用四段式 `VX.Y.Z.R`**（前三段与 base.json 一致，第四段 R 为修订号，只随提交历史记录、不入任何配置文件；递增规则见 Commit 提交规范）；`main.py --version` 打印 base.json 原值
- 音频数组约定：引擎统一 `(N, 2) float32 [-1, 1] @ 44100Hz`；分析用独立 22050Hz mono 路径

## Git 注意

- `.gitignore` 忽略 `.venv`、`.reference/`、`archived/`、`.temp/`、`.opencode/`、`.mimosa/`（安全扫描缓存）、`.agents/`（项目 skill，本地工具不入库）、`opencode-go.json`（含配额凭据）、`config/user_config.json`、`cache/` —— 对这些文件的修改不会出现在 `git status` 中；`AGENTS.md` 已纳入版本控制
- 严禁将 API key、authCookie、workspaceId 等凭据提交到仓库
- 未经用户明确要求，不得擅自执行 `git add`、`git commit` 或任何其他 Git 写操作
- **远程与身份**：远程 `git@takechance:pyapple12/MrAutoDJ.git`（SSH 别名 `takechance` = pyapple12 账号，与 CapsulePulse 同款别名方案）；仓库级身份 `git config user.name pyapple12` + `user.email takechance_bao@188.com`

### Commit 提交规范（V3，2026-11-05 修订；对齐 CapsulePulse 版本双轨）

- **标题行**：`<type>: V<版本>，<摘要>`——版本为四段式 `VX.Y.Z.R`（如 `V0.2.6.1`）：前三段与 `config/static/base.json` 的 `version` 一致，第四段 R 为修订号（不入配置文件，见"版本双轨"条）；摘要一句话概括核心
- **版本递增**：`feat`/`fix`/`refactor`/`perf` 提交前先 bump 第四段 R（R+1）；base.json 前三段推进时 R 回到 1；`docs`/`test`/`style`/`chore` 不强制
- **type 全集**（conventional 风格）：
  - `feat` 新功能 / `fix` 修复 / `refactor` 重构（行为不变）/ `perf` 性能
  - `docs` 文档 / `test` 测试 / `style` 格式 / `build` 构建依赖 / `ci` CI / `chore` 杂项 / `revert` 回滚
- **正文**（默认必写，仅 docs/style 微调可省）：`- ` 列表逐条"具体做了什么"，每条一个功能块、一行自然中文、≤ 100 字符；体例＝`主题：内容（细节；细节）`，同主题多细节用 `；` 分隔。样例：`- 实时变速：TEMPO 推子接 set_tempo_rate（插值填充音高随速变化；量程 ±6/10/16/WIDE 配置驱动）`
- **禁止项**：内部编号（PL001.1/FIX001.2/D1 等任务编号）、验证/回归数字（如"全量回归 506 项通过"）、英文混排描述
- **提交范围**：一个版本的所有连带改动一次提交（源码 + 配置 + 文档同步）
- **流程**：每次提交前 AI 必须 `git status` + `git diff`（含 `--stat`）核对改动范围无误，再草拟完整 commit 内容（add 清单 + 标题 + 正文）交用户确认；用户审阅后自行执行 `git add`/`git commit`/`git push`（AI 不执行 git 写操作；用户明确要求 AI 代执行时按其指示执行，提交前仍须核对）

## 操作注意

- 执行命令前先检测当前 shell（Windows 下为 pwsh）：使用 PowerShell 兼容命令（`Select-String` 替代 `grep`，`Get-ChildItem` 替代 `ls` 等），避免 Linux-only 工具
- pwsh 会话带 `-NoProfile` 不加载 `$PROFILE`，输出中文前必须先设置编码：`[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;`
- 未经用户明确要求，不得擅自执行 `git add`、`git commit` 或任何其他 Git 写操作
- **多模态模型约定**：当前默认模型 deepseek-v4-flash **无视觉能力**（读图工具返回 `Cannot read: this model does not support image input`）；需要读图的任务（UI 截图核对、参考图分析、布局规格单生成等）**必须先通知用户切换多模态模型**（如 Qwen3.8 max）再执行；**未实际读到图时严禁声称"能读到"或编造图片内容**——图读失败如实报告

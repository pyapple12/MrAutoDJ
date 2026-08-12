# MrAutoDJ 项目说明

Python 桌面 DJ 应用，三步路线：虚拟 DJ 台（双打碟机/波形/EQ/横推）→ AI 自动 DJ（调和混音/自动转场/Set 规划）→ Claude 电台（LLM 报幕 + 点歌互动）。GUI 用 PySide6，中文注释为主。无测试套件、无 lint 脚本、无构建步骤（起步阶段）。

## 运行与验证

- 入口 `main.py`：GUI 为默认模式；版本常量 `VERSION` 单一来源在 `config/static/base.json` 的 `version` 字段，其他模块用 `get_static_config().base["version"]` 引用
- 没有测试/lint 命令。改动后验证：`.\.venv\Scripts\python.exe -c "import main, modules.engine, modules.analyzer, modules.library, config.settings, config.static.static_config, ui.main_window, ui.deck_widget, ui.waveform_widget, ui.themes, utils.logger, utils.file_utils, utils.retry, utils.convert"`。不要直接跑 GUI 验证（会弹窗阻塞）
- GUI 无头初始化验证（不弹窗）：`$env:QT_QPA_PLATFORM="offscreen"; .\.venv\Scripts\python.exe -c "from PyQt6.QtWidgets import QApplication; from ui.main_window import MainWindow; app = QApplication([]); w = MainWindow(); print('GUI init OK')"`
- 依赖（`requirements.txt`）：PySide6、sounddevice、librosa 等，按需添加（见 z.plan.md 技术栈）

## 环境陷阱

- `.venv` 是机器绑定的：`pyvenv.cfg` 的 `home` 指向创建时机器的 Python 路径。换机器/换用户后解释器损坏，症状是 VSCode Python 扩展报 `write EPIPE / Shutting down server`（Jedi 语言服务器无法启动）。重建：`Remove-Item -Recurse -Force .venv; py -3.14 -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt`，然后在 VSCode 重选解释器
- opencode 的 pylsp 配置在 `.opencode/opencode.json`，路径硬编码为 `E:\CodeMission\MrAutoDJ\.venv\Scripts\python.exe`——换机器需同步修改
- 音频设备：sounddevice 在 WSL 下无设备（需 WSLg）；Windows 原生运行

## 结构与约定

- 包结构按依赖单向分层（参考 mrboard / AccelWorld）：`utils/` 通用工具（logger/file_utils/retry/convert，无业务依赖）→ `config/` 配置 → `modules/` 业务核心（engine 音频引擎、analyzer 曲目分析、library 曲库、automix AI 编排、radio 电台调度，无 GUI 依赖）→ `ui/` 界面（main_window 主窗口、deck_widget 打碟机、waveform_widget 波形、themes 主题 QSS）→ `data/` 静态数据
- `config/` 配置分两类（对齐 mrboard）：
  - **静态配置**（`config/static/`，只读，json 驱动）：`static_config.py` 加载器 + `config.json` 引导映射表 + `base.json`（应用参数：版本/采样率/块大小/缓存路径等）+ `ui.json`（UI 参数：颜色/阈值/表头）；模块顶层 `_SC = get_static_config()` 一次性解包，运行时零 IO
  - **用户配置**（`config/settings.py`，可读写）：AppConfig dataclass，存项目内 `config/user_config.json`（路径由 base.json `user_config_path` 指定）
- **参数约定**：可调参数一律走 `config/static/*.json`，禁止代码硬编码；版本号唯一来源为 `base.json` 的 `version` 字段
- `main.py` 收编 GUI 分发；模块间顶层 import，不要使用函数内延迟 import（librosa 等重依赖除外，可在函数内导入）
- 提交信息按 Git 注意章节的 Commit 提交规范（V2）书写，如 `feat: V0.09，UI 改版与维护...`
- 项目规划与方案文档在 `z.plan.md`，源码研读报告在 `w.study.md`，任务清单在 `x.progress.md`
- `.reference/` 目录是外部项目的 git clone（浅克隆），**不纳入本仓库版本控制**；需要更新时重新 clone

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
- 只读防误写：分析缓存数据库一律只读连接（`mode=ro`）

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
- 音频数组约定：引擎统一 `(N, 2) float32 [-1, 1] @ 44100Hz`；分析用独立 22050Hz mono 路径

## Git 注意

- `.gitignore` 忽略 `.venv`、`.reference/`、`archived/`、`.temp/`、`.opencode/`、`opencode-go.json`（含配额凭据）、`config/user_config.json`、`cache/` —— 对这些文件的修改不会出现在 `git status` 中；`AGENTS.md` 已纳入版本控制
- 严禁将 API key、authCookie、workspaceId 等凭据提交到仓库
- 未经用户明确要求，不得擅自执行 `git add`、`git commit` 或任何其他 Git 写操作

### Commit 提交规范（V2，2026-08-10 定稿）

- **标题行**：`<type>: V<版本>，<摘要>`——版本号与 base.json `version` 字段一致；摘要一句话概括核心（可用括号列重点）
- **type 全集**（conventional 风格）：
  - `feat` 新功能 / `fix` 修复 / `refactor` 重构（行为不变）/ `perf` 性能
  - `docs` 文档 / `test` 测试 / `style` 格式 / `build` 构建依赖 / `ci` CI / `chore` 杂项 / `revert` 回滚
- **正文**（改动大时可选）：`- ` 列表，每个功能块一行自然中文描述，每行 ≤ 100 字符
- **禁止项**：内部编号（P2/S8/D1 等规划编号）、验证/回归数字（如"全量回归 506 项通过"）、英文混排描述
- **提交范围**：一个版本的所有连带改动一次提交（源码 + 配置 + 文档同步）
- **流程**：由 AI 根据 `git status`/`git diff` 核对清单并草拟 commit 内容（git add 清单 + message）→ 用户审阅后自行执行 `git add`/`git commit`/`git push`（AI 不执行 git 写操作）

## 操作注意

- 执行命令前先检测当前 shell（Windows 下为 pwsh）：使用 PowerShell 兼容命令（`Select-String` 替代 `grep`，`Get-ChildItem` 替代 `ls` 等），避免 Linux-only 工具
- pwsh 会话带 `-NoProfile` 不加载 `$PROFILE`，输出中文前必须先设置编码：`[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;`
- 未经用户明确要求，不得擅自执行 `git add`、`git commit` 或任何其他 Git 写操作
- **多模态模型约定**：当前默认模型 deepseek-v4-flash **无视觉能力**（读图工具返回 `Cannot read: this model does not support image input`）；需要读图的任务（UI 截图核对、参考图分析、布局规格单生成等）**必须先通知用户切换多模态模型**（如 Qwen3.8 max）再执行；**未实际读到图时严禁声称"能读到"或编造图片内容**——图读失败如实报告

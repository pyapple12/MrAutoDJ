# MrAutoDJ 源码研读任务清单（x.progress.md）

> 目标：通读 12 个参考仓库，提炼本项目（Python 虚拟 DJ 台 → AI 自动 DJ → Claude 电台）可借鉴的
> 代码结构、文件分类规范、代码规范、错误处理规范，逐步产出报告至 `w.study.md`。

## A. 前期准备

- [x] A1 扫描 12 个仓库目录结构，评估规模与阅读范围
- [x] A2 建立 w.study.md 报告骨架（每个项目一节 + 汇总规范章节）

## B. 逐个阅读参考仓库

### B1 dj-engine / songs-automixer_python（36 文件 · 全读）

- [x] B1.1 读 main.py / automix 核心包，记录引擎结构
- [x] B1.2 记录 TUI（Textual）交互与命令绑定方式
- [x] B1.3 记录节拍匹配 / 变速 / 渐变 / backspin 实现
- [x] B1.4 记录错误处理与测试组织

### B2 dj-engine / pyCrossfade（33 文件 · 全读）

- [x] B2.1 读 pycrossfade 核心包与 pyproject.toml
- [x] B2.2 记录混音引擎 / 节拍对齐 / EQ 过渡算法
- [x] B2.3 记录库结构规范（模块划分、类型、文档）
- [x] B2.4 记录测试与 CI 规范

### B3 ai-autodj / automix（36 文件 · 全读）

- [x] B3.1 读 automix 核心包，记录 AI 选曲/转场逻辑
- [x] B3.2 记录配置（pyproject.toml / 数据组织）
- [x] B3.3 记录可借鉴的规范化写法

### B4 ai-autodj / cuekey（55 文件 · 全读）

- [x] B4.1 读 src/cuekey（analysis / ui），记录 BPM/调性分析管线
- [x] B4.2 记录打包（packaging）与发布规范
- [x] B4.3 记录文档规范（CONTRIBUTING/CHANGELOG/Code of Conduct）

### B5 ai-autodj / ai-remixmate（445 文件 · 读核心）

- [x] B5.1 读 ARCHITECTURE.md / DJ_ENGINE_IMPROVEMENT_PLAN.md，理解总体设计
- [x] B5.2 读引擎核心（转场 / 人声分离 / LUFS 母带）
- [x] B5.3 读配置系统（config.yaml）与前后端结构
- [x] B5.4 记录其工程化规范（pre-commit、Docker、AGENTS.md/CLAUDE.md）

### B6 ai-autodj / dj-track-similarity（465 文件 · 读核心）

- [x] B6.1 读 DESIGN.md / README，理解 embedding 相似度方案
- [x] B6.2 读 src/dj_track_similarity 核心代码
- [x] B6.3 读前端（frontend）与 CLI/API 组织方式
- [x] B6.4 记录工具集（tools/audio-dedup 等）与测试规范

### B7 claude-radio / radio-dj（59 文件 · 全读）

- [x] B7.1 读 main.go / internal 包，梳理 LLM 报幕 + 推流架构
- [x] B7.2 记录调度（Scheduler）、语音/播报与"技能"体系
- [x] B7.3 记录 Go 风格的项目结构对 Python 的映射启示

### B8 claude-radio / writ-fm（60 文件 · 全读）

- [x] B8.1 读 writ 核心包，记录 Claude 报幕稿生成 + TTS 播报链路
- [x] B8.2 记录配置（config/）、调度（SCHEDULE.md）、运维脚本
- [x] B8.3 记录其 Python 工程组织与测试

### B9 claude-radio / mixx-dj-mcp（230 文件 · 读核心）

- [x] B9.1 读 SPEC.md / PRD.md / llms.txt，理解 MCP 控制 DJ 的设计
- [x] B9.2 读 src（工具注册、FastMCP 用法）与 bridge
- [x] B9.3 记录 MCP 工具分类与鉴权/错误处理规范

### B10 claude-radio / claudio（162 文件 · 读核心）

- [x] B10.1 读 PRODUCT_SPEC_AI_RADIO.md / DEVELOPMENT_SPEC，理解产品设计
- [x] B10.2 读 apps 前后端结构（React/Fastify）
- [x] B10.3 记录 Claude 生成歌单/口播 + TTS 的调用链与提示词设计
- [x] B10.4 记录其可视化与交互设计要点

### B11 claude-radio / wrzdj（1070 文件 · 读核心）

- [x] B11.1 读 ARCHITECTURE.md / README，理解点歌台总体架构
- [x] B11.2 读 server（曲目检测、API）与 bridge
- [x] B11.3 读 kiosk/dashboard 前端交互
- [x] B11.4 记录部署（docker-compose/render）与安全规范

### B12 arch-soft / mixxx（5953 文件 · 只读核心模块）

- [x] B12.1 架构总览：README / src 目录树 / CMakeLists / AGENTS.md
- [x] B12.2 引擎核心：src/engine（engine、mixer、player、channels）
- [x] B12.3 波形与渲染：src/waveform、src/effects、src/library
- [x] B12.4 规范提炼：错误处理（VERIFY/Q_ASSERT 用法）、日志（Logging）、测试、样式（.clang-format）

## C. 汇总产出（写入 w.study.md）

- [x] C1 12 个项目"可借鉴点"分项目汇总
- [x] C2 归纳文件分类规范 / 目录结构规范（跨项目共性）
- [x] C3 归纳代码规范（命名、类型、依赖管理、配置管理）
- [x] C4 归纳错误处理与日志规范（跨项目对比）
- [x] C5 归纳测试与 CI 规范
- [x] C6 输出对 MrAutoDJ 的分阶段落地建议（M1/M2/M3 各参考哪些）

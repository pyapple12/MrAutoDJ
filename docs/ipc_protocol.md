# MrAutoDJ IPC 协议 v1.2（PL003/PL004/PL005）

> Tauri 壳 ↔ Python sidecar 的 WebSocket 协议权威定义。实现：`modules/gateway.py`；
> 任何协议变更必须先改本文档（版本号递增），再改实现。
> v1.1（PL004.1）：控制面指令全集（对照 main_window 接线清单），tick 帧扩灯态字段。
> v1.2（PL005）：曲库/分析/波形数据层——`library_scan`/`waveform` 指令、
> `analysis`/`analysis_done`/`prepared`/`mix_started`/`wave` 事件帧、
> 二进制峰值帧启用；`load` 响应扩 downbeats/name 并自动记录盘 meta；
> 均为 v1 内兼容扩展（`protocol_version` 保持 1，见 §7）。

## 1. 概述

- **传输**：WebSocket（`127.0.0.1`，动态端口，sidecar 启动后以 `gateway ready port=<N>` 行输出实际端口）
- **协议版本**：`protocol_version = 1`（不兼容变更时递增，hello 帧携带）
- **帧类型**：文本帧 = JSON（UTF-8）；二进制帧仅服务端下行（波形峰值，PL005 启用）
- **通道**：RPC（请求-响应）与事件（服务端推送）双通道，共用一条连接

## 2. 握手

客户端连接建立后，服务端**立即**推送一条 `hello` 帧：

```json
{
  "type": "hello",
  "protocol_version": 1,
  "version": "0.2.7",
  "sample_rate": 44100,
  "tick_hz": 30
}
```

| 字段 | 含义 |
| --- | --- |
| `protocol_version` | 协议版本号（客户端校验不匹配即断开提示升级） |
| `version` | 应用版本（`config/static/base.json` 的 `version`） |
| `sample_rate` | 引擎采样率（秒↔样本换算基准） |
| `tick_hz` | 状态推流频率（事件帧 §5） |

## 3. RPC（请求-响应）

入站帧：`{"id": <int>, "cmd": "<指令名>", "args": {…}}`

出站响应：

```json
{"id": 1, "ok": true, "result": {…}}
{"id": 2, "ok": false, "error": {"code": "bad_args", "message": "deck 必须是 'a' 或 'b'"}}
```

- `id` 由客户端生成，响应原样带回（匹配请求）；无法解析的帧 `id` 为 `null`
- `args` 缺省视为 `{}`；必填参数缺失/类型错误 → `bad_args`
- 未收录指令 → `unknown_cmd`

### 3.1 指令表（v1.1 共 36 条，分区编号对照 UI 区）

**传输（T1-T8，对照 Deck 传输区）**

| # | cmd | args | result | 语义 |
| --- | --- | --- | --- | --- |
| T1 | `load` | `deck`, `path`, `bpm?` | `{duration, bpm}` | 解码（线程池）→ 装填播放；`bpm` 提供时对齐 |
| T2 | `play` | `deck` | `{playing}` | 幂等播放（仅 `paused` 时翻转） |
| T3 | `pause` | `deck` | `{paused}` | 幂等暂停 |
| T4 | `cue` | `deck` | `{cue_seconds}` | 设置 CUE 并回到 CUE |
| T5 | `seek` | `deck`, `seconds` | `{position}` | 秒→样本定位（负值钳 0） |
| T6 | `set_volume` | `volume` | `{volume}` | 主音量 0..2（>1 boost，对齐 UI 域） |
| T7 | `set_xfader` | `position` | `{position}` | 横推 -1..1（-1=A 全出，0=居中，1=B 全出） |
| T8 | `mix` | `deck` | `{triggered}` | 转场触发；tm 未注入 → `not_ready` |

**TEMPO / Sync / 循环（D1-D6，对照 Deck 区 TEMPO/Sync/循环键行）**

| # | cmd | args | result | 语义 |
| --- | --- | --- | --- | --- |
| D1 | `set_tempo_rate` | `deck`, `rate` | `{rate}` | 乐速倍率（前端按量程换算）；手动变速解除该盘 Sync |
| D2 | `cycle_tempo_range` | `deck` | `{range, wide, label}` | 量程循环 ±6/±10/±16/WIDE（网关状态） |
| D3 | `set_sync` | `deck`, `on` | `{synced, rate?, target?}` | Beat Sync 对齐另一盘有效 BPM（钳量程）；BPM 未知 → `bad_state` |
| D4 | `set_loop` | `deck`, `on` | `{on}` | 循环开关 |
| D5 | `loop` | `deck`, `action: in/out/halve/double` | `{action, loop_active}` | 循环四动作 |
| D6 | `beatloop` | `deck`, `beats` | `{beats, bpm}` | 按当前盘 BPM 设拍循环；BPM 未知 → `bad_state` |

**表演键（P1-P5，对照表演键行 + Tap）**

| # | cmd | args | result | 语义 |
| --- | --- | --- | --- | --- |
| P1 | `set_keylock` | `deck`, `on` | `{on}` | Keylock 变速不变调（rubberband 后台重渲染） |
| P2 | `set_key_shift` | `deck`, `semitones` | `{semitones}` | 移调（钳 ±key_shift_max） |
| P3 | `slip` / `censor` | `deck`, `on` | `{on}` | 滑行 / 消音开关 |
| P4 | `stutter` | `deck` | `{ok_pressed}` | 结巴重复（按下触发） |
| P5 | `tap` | `deck` | `{bpm}` | 点按测速（0=未成拍） |

**Mixer（M1-M5，对照 Mixer 区 TRIM/EQ/FaderStart/装载）**

| # | cmd | args | result | 语义 |
| --- | --- | --- | --- | --- |
| M1 | `set_pregain` | `deck`, `gain` | `{gain}` | TRIM 前级增益 |
| M2 | `set_eq` | `deck`, `band: low/mid/high`, `gain` | `{band, gain}` | 三频 EQ |
| M3 | `fader_start` | `on` | `{on}` | 推子启动开关（全局） |
| M4 | `instant_doubles` | `deck`, `path` | `{position}` | 复制曲目到另一盘同位置（E2.6 语义） |
| M5 | `set_target` | `deck` | `{target}` | 目标盘切换（mix/prepare 的 now 盘） |

**Jog / Pad（J1-J5，对照转盘与 Pad）**

| # | cmd | args | result | 语义 |
| --- | --- | --- | --- | --- |
| J1 | `jog_touch` | `deck`, `on` | `{on}` | 转盘触摸态 |
| J2 | `jog_scratch` | `deck`, `delta` | `{position}` | 搓碟位移（样本，块内平滑消费） |
| J3 | `jog_bend` | `deck`, `rate` | `{rate}` | 弯音（钳 ±jog_bend_max；前端管累积与超时归零） |
| J4 | `jog_search` | `deck`, `rate` | `{rate}` | SHIFT 高速搜索（钳 ±jog_search_max） |
| J5 | `pad` | `deck`, `idx`, `mode`, `shift` | 按模式 | 五模式：Hot Cue（shift=清除/无=有则播放无则设）/ Beat Loop（拍梯 1-2-4-8-16-32；shift=关循环）/ Beat Jump（1/2/4/8 拍，前 4 后 4）/ Sampler（shift=卸载/有则播放）/ Key Shift（半音表 0,+1,+2,+3,-3,-2,-1,0；shift=累加/0 复位） |

**Beat FX（F1-F5，对照 Beat FX 区）**

| # | cmd | args | result | 语义 |
| --- | --- | --- | --- | --- |
| F1 | `set_fx` | `effect`, `depth`, `on` | `{fx}` | 效果/深度/开关全量应用（前端持完整状态）；通道外盘自动清除 |
| F2 | `set_fx_channel` | `channel: 1/2/both` | `{fx}` | 通道切换（清旧+应用新防残留） |
| F3 | `set_fx_beats` | `beats` | `{beats}` | 拍数（Echo/Delay 延迟 = beats/4 拍） |
| F4 | `fx_auto` | — | `{beats}` | 以通道盘曲目 BPM 为时基；通道内有无 BPM 盘 → `bad_state` |
| F5 | `fx_tap` | — | `{bpm}` | 通道第一盘点按测速；未成拍 → `bad_state` |

**Phones 监听（H1-H2，对照耳机监听区）**

| # | cmd | args | result | 语义 |
| --- | --- | --- | --- | --- |
| H1 | `phones_preview` | `deck` | `{active: deck/null}` | 独占切换（再点同盘停止；无设备 → `not_ready`） |
| H2 | `set_phones_volume` | `volume` | `{volume}` | 监听音量 0..1 |

**推荐 / Automix（A1-A4，对照推荐区；automix 注入后激活——曲库数据由 `library_scan` 填充）**

| # | cmd | args | result | 语义 |
| --- | --- | --- | --- | --- |
| A1 | `recommend` | — | `{name, explanation}` | 推荐下一曲（名称+中文理由）；无推荐 → `bad_state` |
| A2 | `set_automix` | `on` | `{on}` | AUTO 自动接歌开关 |
| A3 | `prepare_next` | — | `{entry: {path, name}}` | 以目标盘为 now 预备下一曲（烘焙异步完成推 `prepared` 事件帧）；失败 → `bad_state` |
| A4 | `mix`（见 T8） | `deck` | `{triggered}` | 转场触发；Mix 完成（30Hz 轮询消费）推 `mix_started` 事件帧并滚动盘 meta，AUTO 开时自动链式装填下一曲 |

**曲库 / 波形（L1-L2，PL005）**

| # | cmd | args | result | 语义 |
| --- | --- | --- | --- | --- |
| L1 | `library_scan` | `folder` | `{files: [{path,name,bpm,key,energy,analyzed}], analyzing}` | 扫描目录 → 缓存命中填充 → 后台线程分析（逐曲 `analysis` 事件帧回填）；分析中重复调用 → `bad_state`；fake 模式合成条目即时返回 |
| L2 | `waveform` | `path`, `width?`（默认 2000，钳 200..4000） | `{width, duration}` | 解码 → 峰值降采样 → 下发 **wave 元数据帧 + 二进制 peaks 帧成对**（顺序见 §4.2） |

`deck` 取值 `"a"` | `"b"`，非法即 `bad_args`。`shift`（J5）为显式布尔参数（前端 Shift 键状态）。

## 4. 事件帧（服务端主动推送）

### 4.1 tick 状态帧（`tick_hz` 频率，默认 30Hz）

```json
{
  "type": "tick",
  "t": 123456.789,
  "a": {"state": "playing", "paused": false, "position": 12.5, "duration": 210.0,
         "bpm": 128.0, "cue": 3.2, "vu": 0.512,
         "tempo_rate": 1.06, "key_shift": 2, "keylock": true,
         "loop": false, "slip": false,
         "hot_cues": [true, false, false, false, false, false, false, false],
         "sampler_loaded": [false, false, false, false, false, false, false, false]},
  "b": {"…同构…"},
  "target": "a",
  "tempo_range": {"a": 6, "b": 6},
  "sync": {"a": false, "b": false},
  "fx": {"effect": "echo", "depth": 0.3, "on": true, "channel": "1", "beats": 4},
  "cue_active": null
}
```

- 盘级（a/b）：`state`：`idle` / `playing` / `mixing`；`position`/`duration`/`cue` 单位**秒**；
  `vu` 0..1；`tempo_rate` 乐速倍率；`key_shift` 半音；`keylock`/`loop`/`slip` 灯态 bool；
  `hot_cues`/`sampler_loaded` 为 8 槽 bool 数组（`slot_count` 可配）
- 顶级：`target` 目标盘；`tempo_range` 两盘量程（±6/±10/±16/100=WIDE）；`sync` 两盘 Sync 灯态；
  `fx` Beat FX 组状态（网关持有）；`cue_active` 当前监听盘（null=未监听）
- `t`：服务端单调时钟，仅供客户端算抖动
- tick 帧可丢弃（见 §8 流控）；**绝不进音频回调**——纯事件循环读锁内状态

### 4.2 事件帧（v1.2 全集）与二进制峰值帧

**`wave` 波形帧（元数据 + 二进制成对，L2 触发）**：先推 JSON 元数据帧，**紧随**一条
二进制帧（同一客户端出站队列顺序保证成对）：

```json
{"type": "wave", "path": "…", "width": 2000, "duration": 210.0,
 "bpm": 128.0, "downbeats": [0, 46875, …]}
```

二进制帧载荷 = `MRWK`（4 字节幻数）+ f32 **little-endian** 数组（(width, 2) 交错
[min, max] 列）；客户端按 `(len-4)/8` 列解析。元数据帧后若无二进制帧（队列满丢弃）
客户端可重新请求。实现解析参考 `modules/waveform_data.peaks_from_bytes`。

**`analysis` 分析进度帧（逐曲，后台线程回填）**：

```json
{"type": "analysis", "path": "…", "name": "song.mp3", "ok": true,
 "bpm": 128.0, "key": "8A", "energy": 5, "error": ""}
```

失败降级：`ok=false` 且 `error` 非空（中文原因），不中断整批。

**`analysis_done`**：`{"type": "analysis_done", "succeeded": N, "total": M}`

**`prepared` 预备完成帧**：`{"type": "prepared", "deck": "a", "ok": true,
"path": "…", "name": "…", "error": ""}`（烘焙异步完成回执，失败 error 中文）

**`mix_started` 转场完成帧**：`{"type": "mix_started", "deck": "a", "now": "…",
"now_name": "…", "finished": "…", "chained": true}`（来曲 meta 已滚动、
AUTO 开时 chained=已自动链式装填）

## 5. 错误码表

| code | 含义 | 典型场景 |
| --- | --- | --- |
| `unknown_cmd` | 未收录指令 | 指令拼写错误 / 前后端版本不匹配 |
| `bad_args` | 参数缺失/非法 | `deck` 非 a/b、数值字段缺失 |
| `bad_state` | 引擎状态不满足指令 | Sync/Beatloop 无 BPM、无曲监听、FX 通道无 BPM 盘、无推荐 |
| `not_ready` | 功能未接入 | `mix`（tm 未注入）、推荐/AUTO（automix 未注入）、监听无设备 |
| `engine_error` | 引擎执行失败 | 解码失败、文件不存在（message 含中文原因） |
| `bad_json` | 入站帧非合法 JSON | 客户端序列化错误 |

错误 `message` 一律中文，可直接展示给用户；客户端 UI 只认 `code` 分类。

## 6. 心跳与重连

- **心跳**：由 websockets 库内置 ping/pong 承担（默认 20s 间隔），协议层不重复造；客户端库开启对应配置即可
- **重连**：客户端职责——连接断开后指数退避重连（建议 0.5s 起、×2、上限 5s），重连成功以收到新 `hello` 为准；v1 前端在连接状态屏显示"重连中"
- **就绪握手**（sidecar 启动侧）：Tauri 壳 spawn `python -m modules.gateway` 后轮询 stdout 的 `gateway ready port=<N>` 行取得端口；此行输出后服务已可接受连接

## 7. 版本兼容

- 客户端收到 `protocol_version` 与自身不支持的范围不符：断开并提示升级
- v1 内新增指令/新增 result 字段视为兼容变更（旧客户端忽略未知字段）
- 移除指令、变更参数语义：`protocol_version` 递增

## 8. 流控（服务端实现约束，客户端可知）

- 每客户端出站队列 64 帧、唯一写出者协程；队列满时**丢弃 tick 帧**（状态可自愈，下一帧即最新），RPC 响应不主动丢弃
- 落后超过一个推送周期时重对齐推送时钟，防雪崩追赶

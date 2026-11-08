# MrAutoDJ IPC 协议 v1（PL003）

> Tauri 壳 ↔ Python sidecar 的 WebSocket 协议权威定义。实现：`modules/gateway.py`；
> 任何协议变更必须先改本文档（版本号递增），再改实现。

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

### 3.1 指令表（v1 共 8 条）

| cmd | args | result | 语义（对齐引擎/主窗方法） |
| --- | --- | --- | --- |
| `load` | `deck`, `path`, `bpm?` | `{duration: 秒, bpm}` | 解码（线程池）→ 装填播放；`bpm` 提供时 `set_tempo` 对齐 |
| `play` | `deck` | `{playing}` | 幂等播放：仅 `paused` 时翻转（Deck.pause 为 toggle） |
| `pause` | `deck` | `{paused}` | 幂等暂停：仅未暂停时翻转 |
| `cue` | `deck` | `{cue_seconds}` | 设置 CUE 并回到 CUE（先设后回，UI 同款语义） |
| `seek` | `deck`, `seconds` | `{position: 秒}` | 秒→样本定位；负值钳 0 |
| `set_volume` | `volume` | `{volume}` | 主音量 0..1（钳制） |
| `set_xfader` | `position` | `{position}` | 横推 0..1（0=A 全出，1=B 全出，钳制） |
| `mix` | `deck` | `{triggered}` | 转场触发；v1 未接入转场管理时返回 `not_ready`（协议占位） |

`deck` 取值 `"a"` | `"b"`，非法即 `bad_args`。

## 4. 事件帧（服务端主动推送）

### 4.1 tick 状态帧（`tick_hz` 频率，默认 30Hz）

```json
{
  "type": "tick",
  "t": 123456.789,
  "a": {"state": "playing", "paused": false, "position": 12.5, "duration": 210.0,
         "bpm": 128.0, "cue": 3.2, "vu": 0.512},
  "b": {"state": "idle", "paused": true, "position": 0.0, "duration": 0.0,
         "bpm": 0.0, "cue": 0.0, "vu": 0.0}
}
```

- `state`：`idle` / `playing` / `mixing`（引擎 State 枚举序列化值）
- `position` / `duration` / `cue` 单位**秒**（float）；`vu` 0..1（峰值表）
- `t`：服务端单调时钟（`time.monotonic()`），仅供客户端算抖动，不做墙钟对齐
- tick 帧可丢弃（见 §8 流控）；**绝不进音频回调**——纯事件循环读锁内状态

### 4.2 二进制峰值帧（预留，PL005 启用）

服务端下行 `bytes` 帧，little-endian `f32` 数组，用于波形渲染（服务端复用
`_build_peaks` 峰值提取）。v1 不发送；客户端应忽略收到的二进制帧。

## 5. 错误码表

| code | 含义 | 典型场景 |
| --- | --- | --- |
| `unknown_cmd` | 未收录指令 | 指令拼写错误 / 前后端版本不匹配 |
| `bad_args` | 参数缺失/非法 | `deck` 非 a/b、数值字段缺失 |
| `not_ready` | 功能未接入 | `mix` 转场管理未注入（v1） |
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

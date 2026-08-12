# 已知问题与增强备忘（y.problem.md）

> 目的：记录已发现但不属于当前阶段范围的问题/增强项，供未来评估
> 记录格式：状态 [✅ 已完成 / 📌 待评估] / 来源（讨论日期/场景）

---

## 📌 待修复（修复轮排在 M1.6 UI 拟物改版之前）

### P1. Echo/Delay 效果周期性中断（环形缓冲回绕跳读）🔧

- 状态：🔧 待修复（2026-08-10 代码复核确认修复未执行；2026-08-11 排入 M1.6 前修复轮）
- 来源：2026-08-10 GUI 实测——M1.5 的 Beat FX（Echo/Delay）播放约 2 秒后效果"突然中断"
- 现象：Echo/Delay 生效后每约 2.09 秒出现约 0.25 秒的无回声窗口，听感为周期性中断
- 根因：`modules/engine.py` 的 `FeedbackDelay.process()` 中 `start = max(0, delay - self._pos)` 的"延迟未充满"判断基于线性缓冲假设；环形缓冲（长度 ≈ 2.09s）每回绕一次（`_pos` 从 ~92160 跳回 ~1912），该判断误判"未充满"而整块跳过读取，导致回绕后 delay 时长内回声丢失
- 技术要点：环形缓冲下 `read = (pos - delay) % buf_len` 始终指向有效旧数据（delay=11025 < buf_len=92296），零初始化天然提供初始"未充满"行为，start 判断实为多余
- 修复方向：去除 `start` 判断，恒从块头读取（保留已实现的分段回绕读/写）
- 涉及：`modules/engine.py` FeedbackDelay.process
- 影响面：E1.8（Echo/Delay 效果）、E2.4（Beat FX 面板）、GUI 听感

### P2. 弯音（Jog 滚轮）速率不归零，持续变速导致播放紊乱 ✅

- 状态：✅ 已修复（2026-08-12 GUI 实测确认；另修复减速弯音广播异常致静音卡顿 + 每格步进/累积语义调优，参数 `jog_bend_step`/`jog_bend_reset_ms` 进 ui.json 后续可再调）
- 来源：2026-08-10 GUI 实测——滚轮滚一次后音乐持续加速/变速，"使用后音乐播放断断续续"
- 现象：滚轮每格发 `bend_changed(±0.02)` → `deck.jog_bend(±0.02)` 设置 `_jog_bend_rate`；**释放后从未归零**，速率永久生效且多次滚动累积（+0.02、+0.04…），回调每块按 `step = frames × (1+rate)` 推进
- 根因：`ui/main_window.py` 的 `_on_bend_release` 只把值存入 `_bend_timer_pending`（且该字段未在 `__init__` 初始化），**没有定时归零机制**；引擎侧 `jog_bend` 无超时语义
- 验证：`jog_bend(0.02)` 后连续 fill 每次推进 102（原速 100），速率永久保持
- 修复方向：滚轮弯音应为"脉冲"语义——发送后短延迟（如 50-100ms 定时器）自动 `jog_bend(0.0)` 归零；或引擎侧给 bend 加超时衰减
- 涉及：`ui/main_window.py`（弯音归零定时器）、`modules/engine.py`（可选超时）
- 影响面：Jog 交互（E2.3）、播放稳定性

### P3. 搓碟（Jog 拖动）未实现"搓"效果，仅为位置跳变 ✅

- 状态：✅ 已修复（2026-08-12 GUI 实测确认：平滑变速刮擦（块内逐帧插值，向前加速/向后倒放）+ 手停静音 + Slip 落回；增益手感调优留待后续，参数 `jog_scratch_gain`/`jog_scratch_speed_ref` 在 ui.json）
- 来源：2026-08-10 GUI 实测——顶面按住拖动听不到搓碟音效，且拖动后音乐从新位置继续（跳变）
- 现象：拖动映射 `scratch_moved(dx×256)` → `deck.jog_scratch(delta)` 直接改 `_position`；无"按住期间位置跟随手速、释放后从拖动点继续"的搓碟语义
- 根因：
  1. 拖动只是**跳变位置**：`jog_scratch` 改 `_position` 后，下一块 `_fill_playing` 继续正常推进——慢速拖动时位置增量与正常推进互相抵消，听感几乎无变化
  2. 无**搓碟触摸锁定**：真实转盘"触摸+转=搓（播放暂停、位置跟手）、松手=弯音"；当前实现触摸时播放仍正常推进
  3. `SCRATCH_GAIN=256`（每像素 256 样本）对慢速拖动过小，对快速拖动又造成大跳变
- 修复方向（参考 FLX4/B13-3.16 语义）：
  - 触摸按下（Vinyl 开）时**暂停正常推进**（position 只由拖动驱动），拖动增量映射播放位置（可正可负）
  - 松开后从当前位置继续播放（可选：回到拖动前位置 = "slip 搓碟"；FLX4 默认非 slip 语义为就地继续）
  - 按拖动速度调整增益（速度越快偏移越大）
- 涉及：`modules/engine.py`（jog_scratch/touch 与 `_fill_playing` 联动）、`ui/jog_wheel.py`（增益标定）
- 影响面：Jog 交互（E2.3）、搓碟表演

### P4.（预留）

### P5. Pitch 滑块无效果（M1 遗留占位）📌

- 状态：📌 待修复（**V0.21 版本之后**；2026-08-12 GUI 实测发现）
- 来源：2026-08-12 GUI 实测——Pitch 推子（-8..8%）拖动后播放速率不变
- 现象：状态栏提示 "Pitch -3%（预渲染接入待 D3 管线完善）"，实际变速未生效
- 根因：`ui/main_window.py` `_on_pitch` 为占位实现（仅打印日志）；单盘实时变速从未接入——变速预渲染只接入了转场管线（D3 prepare/mix），Pitch 滑块与 Keylock 按钮均未接线
- 修复方向（候选）：把 Pitch 接到引擎实时变速——复用 F2 弯音的 step 插值路线（`_fill_playing` 插值分支），Deck 加 `set_pitch(percent)`；Keylock 语义（变速不变调 vs 变调不变速）需后续评估预渲染 vs 实时插值
- 涉及：`ui/main_window.py`（_on_pitch/_on_keylock）、`modules/engine.py`（Deck 变速状态 + _fill_playing）
- 影响面：Pitch 变速、Keylock 交互

# WebUI Design tokens 生成器（PL006.1）：config/static/ui.json → webui/src/styles/tokens.css
# 用法：python tools/gen_webui_tokens.py（改动 ui.json 配色/尺寸键后重跑）
# 单源纪律：webui 全部颜色/间距/尺寸变量由本脚本从 ui.json 生成（dark=顶层键，
# light=theme_light 覆盖表），禁止手写色值绕过

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI_JSON = ROOT / "config" / "static" / "ui.json"
OUT = ROOT / "webui" / "src" / "styles" / "tokens.css"


def css_vars(d: dict) -> str:
    # ui.json 键 → CSS 变量映射（--c-* 颜色 / --sp-* 间距 / --sz-* 尺寸）
    colors = d.get("colors", {})
    pad = d.get("pad_colors", [])
    lines = [
        f"  --bg: {colors.get('background', '#0d0d0d')};",
        f"  --accent: {colors.get('accent', '#00ff41')};",
        f"  --deck-a: {colors.get('deck_a', '#00cccc')};",
        f"  --deck-b: {colors.get('deck_b', '#cccc00')};",
        f"  --warning: {colors.get('warning', '#ccaa00')};",
        f"  --danger: {colors.get('danger', '#cc2222')};",
        f"  --panel: {d.get('panel_base', '#1c1e22')};",
        f"  --line: {d.get('panel_edge', '#26292f')};",
        f"  --panel-inset: {d.get('panel_inset', '#101215')};",
        f"  --fg-dim: {d.get('silk_text', '#8a9099')};",
        f"  --fg: {d.get('glow_white', '#e8ecf0')};",
        f"  --accent2: {d.get('glow_orange', '#ff7a2f')};",
        f"  --glow-blue: {d.get('glow_blue', '#2f8bff')};",
        f"  --glow-green: {d.get('glow_green', '#2fe37a')};",
    ]
    for i, c in enumerate(pad[:5]):
        lines.append(f"  --pad-{i + 1}: {c};")
    lines += [
        f"  --sp-1: {d.get('spacing_sm', 4)}px;",
        f"  --sp-2: {d.get('spacing_md', 8)}px;",
        f"  --sp-3: {d.get('spacing_lg', 12)}px;",
        f"  --btn-min-w: {d.get('button_min_width', 32)}px;",
        f"  --btn-min-h: {d.get('button_min_height', 32)}px;",
        f"  --knob-mixer: {d.get('knob_size_mixer', 32)}px;",
        f"  --knob-fx: {d.get('knob_size_fx', 28)}px;",
        f"  --jog-size: {d.get('jog_size', 140)}px;",
        f"  --pad-size: {d.get('pad_btn_size', 42)}px;",
    ]
    shares = d.get("splitter_main_shares", [0.375, 0.1, 0.375, 0.15])
    mins = d.get("splitter_main_mins", [395, 200, 395, 280])
    lines.append(
        "  --layout-rows: "
        + " ".join(f"max({int(m * 2)}px, {s * 100:.1f}fr)" for m, s in zip(mins, shares))
        + ";"
    )
    led = d.get("led_segments", 12)
    lines.append(f"  --led-segments: {led};")
    lines.append(f"  --led-green: {d.get('led_green_threshold', 0.6)};")
    lines.append(f"  --led-yellow: {d.get('led_yellow_threshold', 0.85)};")
    return "\n".join(lines)


def main() -> None:
    # 生成 tokens.css：:root（dark 默认）+ :root[data-theme=light] 覆盖
    ui = json.loads(UI_JSON.read_text(encoding="utf-8"))
    light = ui.get("theme_light", {})
    text = (
        "/* 本文件由 tools/gen_webui_tokens.py 从 config/static/ui.json 生成——\n"
        "   勿手改色值；改动 ui.json 配色/尺寸键后重跑生成器（token 同源纪律，PL006.1） */\n\n"
        ":root {\n" + css_vars(ui) + "\n}\n\n"
        ":root[data-theme=\"light\"] {\n" + css_vars(light) + "\n}\n"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"written {OUT.relative_to(ROOT)} ({len(text)} chars)")


if __name__ == "__main__":
    main()
    sys.exit(0)


# ===== tools/gen_webui_tokens.py 模块说明 =====
# 函数：
#   css_vars(d)：ui.json 键 → CSS 变量文本（颜色/间距/尺寸/布局比例/LED 阈值）
#   main()：读 ui.json → 生成 webui/src/styles/tokens.css（dark :root + light 覆盖）
# 设计理由：
#   token 同源——PySide6 版（palette.py 读 ui.json）与 Web 版（tokens.css）共用
#   同一配置文件，双栈主题一致；生成器入库 tools/（可重跑），产物入库 webui/（构建零依赖）
# 异常处理：键缺失用内置默认值兜底（宽容解析）；无异常路径
# 关联配置：config/static/ui.json（colors/panel_*/glow_*/pad_colors/spacing_*/
#   *_size/splitter_main_shares/led_*）；theme_light 覆盖表（palette 语义对应）

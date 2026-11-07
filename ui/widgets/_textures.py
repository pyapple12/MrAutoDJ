# 程序化贴图离线渲染 + PNG 磁盘缓存（J3 批次 3 A 路线）
# 把 PanelFrame 的程序化金属绘制离线渲染为 PNG（cache/ui_textures/，已 gitignore），
# 运行时按 (名称, 主题, 尺寸) 键控加载——零素材复用现有绘制语言，一次渲染终身使用

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPixmap, QPen

from ui import palette
from utils.file_utils import get_project_root

# 渲染期基色加深比例（中段提亮量，对齐原 PanelFrame 渐变语言）
_MID_LIFT = 6

_MEM: dict[str, QPixmap] = {}


def _dir() -> Path:
    # 贴图缓存目录：项目内 cache/ui_textures/（cache/ 已 gitignore，可随时重建）
    return get_project_root() / "cache" / "ui_textures"


def _render_brushed(w: int, h: int) -> QPixmap:
    # 拉丝金属面板纹理：垂直渐变（base→中段提亮→edge）+ 半透明横向拉丝线
    # （复用 PanelFrame 原绘制语言；配色按当前主题 palette 现取）
    pm = QPixmap(w, h)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    base = palette.color("panel_base", "#1c1e22")
    grad = QLinearGradient(0, 0, 0, h)
    grad.setColorAt(0.0, base)
    grad.setColorAt(0.5, QColor(base.red() + _MID_LIFT, base.green() + _MID_LIFT, base.blue() + 8))
    grad.setColorAt(1.0, palette.color("panel_edge", "#26292f"))
    p.fillRect(0, 0, w, h, grad)
    for y in range(4, h - 4, 6):
        alpha = 10 if (y // 6) % 2 == 0 else 5
        p.setPen(QPen(QColor(255, 255, 255, alpha), 1))
        p.drawLine(0, y, w, y)
    p.end()
    return pm


def texture(name: str, w: int, h: int) -> QPixmap:
    # 取贴图：内存 → 磁盘 PNG → 现渲染并写盘（键含主题，dark/light 各一份）；
    # FIX004.14：尺寸量化 32px 步进（splitter 拖动逐像素变化不再逐像素 miss/
    # 写盘——量化键复用，绘制按需拉伸）；缓存超 64 项全清（防无界增长）；
    # FIX005.4：量化取**上整**（≥ 需求尺寸，原尺寸绘制即可覆盖全面板——
    # 原向下取整在非 32 倍数尺寸右/下缘露透明空带）
    qw = max(32, ((w + 31) // 32) * 32)
    qh = max(32, ((h + 31) // 32) * 32)
    # FIX005/P3-14：键附配色指纹（panel_base/edge 调色后旧 PNG 不失效）
    csig = (
        palette.color("panel_base", "#1c1e22").name()
        + palette.color("panel_edge", "#26292f").name()
    )[-12:]
    key = f"{name}_{palette.current()}_{csig}_{qw}x{qh}"
    hit = _MEM.get(key)
    if hit is not None:
        return hit
    if len(_MEM) > 64:
        _MEM.clear()  # 简单防增长：全清后按需重建（贴图渲染廉价）
    path = _dir() / f"{key}.png"
    if path.is_file():
        pm = QPixmap(str(path))
    else:
        if name == "brushed":
            pm = _render_brushed(qw, qh)
        else:
            pm = QPixmap(qw, qh)  # 未知名称：空贴图兜底
        try:
            _dir().mkdir(parents=True, exist_ok=True)
            pm.save(str(path), "PNG")
        except OSError:
            pass  # 写盘失败降级为纯内存（只读目录等）
    _MEM[key] = pm
    return pm


def clear_memory_cache() -> None:
    # 清内存缓存（磁盘 PNG 保留；主题切换由键控天然隔离，本接口供热重载/测试）
    _MEM.clear()


# ===== ui/widgets/_textures.py 模块说明 =====
# 函数：
#   _dir()：PNG 缓存目录（cache/ui_textures/，gitignore，可随时重建）
#   _render_brushed(w, h)：拉丝金属纹理渲染（复用 PanelFrame 渐变/拉丝语言，
#     配色按当前主题 palette 现取）
#   texture(name, w, h)：三级查找 内存→磁盘 PNG→现渲染写盘；键 = 名称_主题_尺寸
#   clear_memory_cache()：仅清内存（测试/热重载用）
# 设计理由：批次 3 A 路线——把运行期程序化绘制离线化为 PNG 贴图（拟物度不变，
#   重复渲染开销归零、可外发精修替换）；磁盘缓存可 gitignore 重建零成本
# 异常处理：写盘失败（只读目录）降级纯内存；未知名称返回空贴图不崩
# 关联配置：config/static/ui.json（panel_base/panel_edge 配色，经 palette）；
#   base.json cache_path 同目录约定（cache/）

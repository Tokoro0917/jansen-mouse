"""機体の全体図（部品の説明つき）: 三面図と、色の凡例つきの立体図。

    python -m jansen.cli drawing -o ../docs/images
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import patches  # noqa: E402
from shapely import affinity  # noqa: E402

from .assembly import _module_poses, _shape, module_parts  # noqa: E402
from .body import BEAM_HALF_ANGLE, default_design, evaluate, leg_obstacles, sensor_ray  # noqa: E402
from .linkage import JansenLeg  # noqa: E402

plt.rcParams["font.family"] = ["IPAGothic", "IPAPGothic", "DejaVu Sans"]

# 番号, 名前, 説明, 色
PARTS = [
    (1, "脚（12 本）", "テオヤンセン機構。片側 3 組 × 前後 2 本。足先にゴム", "#e07a5f"),
    (2, "フレーム板", "1.5 mm 厚、片側 4 枚。脚の固定ピンとクランク軸を支える", "#888888"),
    (3, "タイロッド", "M2 全ねじ 2 本。左右すべてのフレーム板を横に貫き、左右の脚群をつなぐ", "#444444"),
    (4, "モータ", "N20 ウォームギヤ + エンコーダ × 2。出力軸がクランク軸に直結", "#b0b0b0"),
    (5, "タイロッドの柱", "3D プリント 2 本。基板をタイロッドに留める", "#b0c4de"),
    (6, "モータ押さえ", "3D プリント。モータを下から支え、前後の柱で基板に留める（基板と挟む）", "#7f9cc0"),
    (7, "基板（1 枚）", "110 × 25 mm。中央の溝の中、モータの上。全部の回路を載せる", "#2e7d32"),
    (8, "マイコン", "STM32F411 を基板に直付け", "#1a237e"),
    (9, "電池", "2S LiPo 200 mAh。タイロッドを避けて前に置く", "#f2c14e"),
    (10, "IMU", "ジャイロ（旋回中心の真上）", "#7b1fa2"),
    (11, "モータドライバ", "DRV8835", "#8d1c1c"),
    (12, "壁センサ", "黒いホルダに発光・受光。基板の裏に下げる。FL/FR は前、L/R は横", "#111111"),
]
COLOR = {n: c for n, _, _, c in PARTS}
COMPONENT_PART = {"motor_L": 4, "motor_R": 4, "rod_post_rear": 5, "rod_post_front": 5, "motor_clamp": 6,
                  "clamp_post_rear": 6, "clamp_post_front": 6, "board": 7, "mcu": 8, "battery": 9, "imu": 10,
                  "driver": 11}


def _tag(ax, n, x, y, dx=0.0, dy=0.0):
    """番号の丸印（dx, dy だけずらして引き出し線を引く）。"""
    tx, ty = x + dx, y + dy
    if dx or dy:
        ax.plot([x, tx], [y, ty], color="k", lw=0.6, zorder=9)
    ax.add_patch(patches.Circle((tx, ty), 3.6, facecolor="white", edgecolor="k", lw=0.8, zorder=10))
    ax.text(tx, ty, str(n), ha="center", va="center", fontsize=7, zorder=11)


def _rect(ax, x0, x1, y0, y1, color, alpha=0.9, z=3, **kw):
    ax.add_patch(patches.Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=color, edgecolor="k",
                                   lw=0.4, alpha=alpha, zorder=z, **kw))


def three_views(scale, throws, center_width, bp, out: Path, theta_deg: float = 30.0) -> Path:
    d = default_design(scale, throws, center_width, bp)
    rep = evaluate(d)
    obs, h = leg_obstacles(scale, throws, center_width, bp)
    leg = JansenLeg(scale=scale)
    comps = {c.name: c for c in d.components}
    la = leg.length("a")
    tie_z = h + bp.spacer_y
    drawn = [n for n in COMPONENT_PART if n in comps]

    def mid(c, axis):
        lo, hi = getattr(c, axis)
        return (lo + hi) / 2

    fig = plt.figure(figsize=(16, 11))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.62], width_ratios=[1.15, 1.0, 0.95])
    ax_side = fig.add_subplot(gs[0, 0])
    ax_top = fig.add_subplot(gs[0, 1])
    ax_front = fig.add_subplot(gs[0, 2])
    ax_leg = fig.add_subplot(gs[1, :])

    # ---------------- 横から（x-z、左側から見る）----------------
    ax = ax_side
    ax.set_title("横から見た図（左側から。右が前）", fontsize=11)
    sweep = [o for o in obs if o.name.startswith("legs")][0].poly
    ax.add_patch(patches.Polygon(list(sweep.exterior.coords), closed=True, facecolor="#f4d6cc",
                                 edgecolor="#c97b63", lw=0.6, ls="--", zorder=1))
    pose = _module_poses(leg, math.radians(theta_deg))
    for name, js in module_parts().items():
        sh = affinity.translate(_shape(name, js, pose, leg, bp), 0, h)
        ax.add_patch(patches.Polygon(list(sh.exterior.coords), closed=True, facecolor=COLOR[1],
                                     edgecolor="k", lw=0.4, alpha=0.85, zorder=2))
    frame = [o for o in obs if o.name.startswith("frame")][0].poly
    ax.add_patch(patches.Polygon(list(frame.exterior.coords), closed=True, facecolor=COLOR[2],
                                 edgecolor="k", lw=0.5, alpha=0.45, zorder=3))
    for name in drawn:
        if name == "motor_R":
            continue
        c = comps[name]
        _rect(ax, c.x[0], c.x[1], c.z[0], c.z[1], COLOR[COMPONENT_PART[name]], z=4)
    for s in d.sensors:
        hc = comps[s.board]
        _rect(ax, hc.x[0], hc.x[1], hc.z[0], hc.z[1], COLOR[12], z=6)
        if abs(s.direction_deg) < 1:
            (x0, _), (x1, _) = sensor_ray(s)
            ax.plot([x0, x1], [s.origin[2]] * 2, color="red", lw=1.2, zorder=7)
    for sx in (-la, la):
        ax.add_patch(patches.Circle((sx, tie_z), 1.3, color=COLOR[3], zorder=8))
    ax.add_patch(patches.Circle((0, h), 1.6, color="k", zorder=8))
    ax.text(-62, 74, f"● = クランク軸（高さ {h:.1f}）", fontsize=8, va="center", zorder=9)
    ax.axhline(0, color="k", lw=1.2)
    ax.add_patch(patches.Rectangle((84, 0), 12, 50, facecolor="#e8dcc0", edgecolor="#9c8a60", zorder=0))
    ax.text(90, 52, "前の壁\n（高さ 50）", ha="center", fontsize=7)
    ax.text(68, d.sensors[0].origin[2] + 1.5, "光", color="red", fontsize=7)
    board, motor, clamp, battery = comps["board"], comps["motor_L"], comps["motor_clamp"], comps["battery"]
    _tag(ax, 1, 4, 6, 0, 0)
    _tag(ax, 2, la, h - 6, 10, -8)
    _tag(ax, 3, la, tie_z, 10, 8)
    _tag(ax, 4, -22, h, 0, 0)
    _tag(ax, 5, -la, mid(comps["rod_post_rear"], "z"), -10, 8)
    _tag(ax, 6, clamp.x[0] + 4, clamp.z[0] + 1, -8, -10)
    _tag(ax, 7, board.x[0] + 4, board.z[1], -6, 10)
    _tag(ax, 8, mid(comps["mcu"], "x"), comps["mcu"].z[1], 0, 9)
    _tag(ax, 9, mid(battery, "x"), battery.z[1], 0, 6)
    _tag(ax, 12, 48, comps["holder_FL"].z[0], 6, -10)
    x_rear = min(min(o.poly.bounds[0] for o in obs), min(c.x[0] for c in d.components))
    x_front = max(max(c.x[1] for c in d.components), max(o.poly.bounds[2] for o in obs))
    top = max(max(c.z[1] for c in d.components), max(o.poly.bounds[3] for o in obs))
    ax.annotate("", (x_rear, -8), (x_front, -8), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text((x_rear + x_front) / 2, -13, f"全長 {x_front - x_rear:.1f}", ha="center", fontsize=8)
    ax.annotate("", (x_rear - 6, 0), (x_rear - 6, top), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text(x_rear - 8, top / 2, f"高さ {top:.1f}", rotation=90, ha="right", va="center", fontsize=8)
    ax.set_xlim(-65, 100)
    ax.set_ylim(-18, 80)

    # ---------------- 上から（x-y）----------------
    ax = ax_top
    ax.set_title("上から見た図（上が前）", fontsize=11)
    for o in obs:
        x0, _, x1, _ = o.poly.bounds
        if o.name.startswith("legs"):
            _rect(ax, o.y0, o.y1, x0, x1, "#f4d6cc", alpha=1.0, z=1, ls="--")
        else:
            _rect(ax, o.y0, o.y1, x0, x1, COLOR[2], alpha=0.8, z=2)
    for name in drawn:
        c = comps[name]
        alpha = 0.5 if name in ("board", "motor_clamp") else 0.95
        zz = 3 if name in ("motor_L", "motor_R", "motor_clamp") else (4 if name == "board" else 5)
        _rect(ax, -c.y[1], -c.y[0], c.x[0], c.x[1], COLOR[COMPONENT_PART[name]], alpha=alpha, z=zz)
    y_out = max(abs(o.y1) for o in obs)
    for sx in (-la, la):
        ax.plot([-y_out - 2, y_out + 2], [sx, sx], color=COLOR[3], lw=1.6, zorder=6)
    for s in d.sensors:
        hc = comps[s.board]
        _rect(ax, -hc.y[1], -hc.y[0], hc.x[0], hc.x[1], COLOR[12], z=7)
        (x0, y0), (x1, y1) = sensor_ray(s)
        ax.plot([-y0, -y1], [x0, x1], color="red", lw=1.2, zorder=7)
        t = math.tan(math.radians(BEAM_HALF_ANGLE))
        length = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / length, (y1 - y0) / length
        nx, ny = -uy, ux
        ax.add_patch(patches.Polygon([(-y0, x0), (-(y1 + ny * length * t), x1 + nx * length * t),
                                      (-(y1 - ny * length * t), x1 - nx * length * t)],
                                     closed=True, facecolor="red", alpha=0.08, zorder=0))
        ax.text(-y1, x1 + (4 if abs(s.direction_deg) < 1 else 3), s.name, color="red", fontsize=7, ha="center")
    ax.add_patch(patches.Circle((0, 0), rep.turning_radius, fill=False, ls=":", color="b", lw=0.9, zorder=8))
    ax.text(rep.turning_radius * 0.72, -rep.turning_radius * 0.72 - 6,
            f"旋回で通る円\n半径 {rep.turning_radius:.1f}", color="b", fontsize=7)
    for wy in (-84, 84):
        ax.add_patch(patches.Rectangle((wy if wy > 0 else wy - 12, -96), 12, 192, facecolor="#e8dcc0",
                                       edgecolor="#9c8a60", zorder=0))
    ax.add_patch(patches.Rectangle((-96, 84), 192, 12, facecolor="#e8dcc0", edgecolor="#9c8a60", zorder=0))
    ax.text(0, 97.5, "前の壁", ha="center", fontsize=7)
    ax.text(-90, 0, "左の壁", rotation=90, va="center", fontsize=7)
    ax.annotate("", (-y_out, -60), (y_out, -60), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text(0, -66, f"全幅 {2 * y_out:.1f}", ha="center", fontsize=8)
    ax.text(0, -78, "区画の中心に止まったとき。壁の面は中心から 84 mm", ha="center", fontsize=7)
    _tag(ax, 1, -35, -25, 0, 0)
    _tag(ax, 1, 35, -25, 0, 0)
    _tag(ax, 2, -y_out + 0.7, 10, -10, 8)
    _tag(ax, 3, 40, la, 0, 9)
    _tag(ax, 5, 0, -la, 0, 0)
    _tag(ax, 7, 0, board.x[0] + 4, 0, 0)
    _tag(ax, 8, 0, mid(comps["mcu"], "x"), 0, 0)
    _tag(ax, 9, 0, mid(battery, "x"), 0, 0)
    _tag(ax, 12, 13, 58, 12, -12)
    ax.set_xlim(-100, 100)
    ax.set_ylim(-100, 104)

    # ---------------- 前から（y-z）----------------
    ax = ax_front
    ax.set_title("前から見た図", fontsize=11)
    for o in obs:
        _, z0, _, z1 = o.poly.bounds
        if o.name.startswith("legs"):
            _rect(ax, -o.y1, -o.y0, z0, z1, "#f4d6cc", alpha=1.0, z=1, ls="--")
        else:
            _rect(ax, -o.y1, -o.y0, z0, z1, COLOR[2], alpha=0.8, z=2)
    for name in drawn:
        c = comps[name]
        _rect(ax, -c.y[1], -c.y[0], c.z[0], c.z[1], COLOR[COMPONENT_PART[name]],
              alpha=0.9, z=3 if name in ("motor_L", "motor_R") else 4)
    ax.plot([-y_out - 2, y_out + 2], [tie_z, tie_z], color=COLOR[3], lw=1.6, zorder=6)
    for s in d.sensors:
        hc = comps[s.board]
        _rect(ax, -hc.y[1], -hc.y[0], hc.z[0], hc.z[1], COLOR[12], z=7)
        if abs(s.direction_deg) > 1:
            (_, y0), (_, y1) = sensor_ray(s)
            ax.plot([-y0, -y1], [s.origin[2]] * 2, color="red", lw=1.2, zorder=7)
    ax.axhline(0, color="k", lw=1.2)
    for wy in (-84, 84):
        ax.add_patch(patches.Rectangle((wy if wy > 0 else wy - 12, 0), 12, 50, facecolor="#e8dcc0",
                                       edgecolor="#9c8a60", zorder=0))
    ax.text(-90, 52, "右の壁", ha="center", fontsize=7)
    ax.text(90, 52, "左の壁", ha="center", fontsize=7)
    _tag(ax, 1, -35, 12, 0, 0)
    _tag(ax, 2, -y_out + 0.7, 45, -8, 10)
    _tag(ax, 3, 45, tie_z, 0, 8)
    _tag(ax, 4, -6, h, 0, 0)
    _tag(ax, 7, 10, board.z[0], 14, -12)
    _tag(ax, 9, 0, battery.z[1], 0, 6)
    _tag(ax, 12, 13, mid(comps["holder_L"], "z"), 10, -14)
    ax.set_xlim(-100, 100)
    ax.set_ylim(-10, 80)

    for a in (ax_side, ax_top, ax_front):
        a.set_aspect("equal")
        a.grid(alpha=0.2)
        a.tick_params(labelsize=7)
    ax_side.set_xlabel("前後 x [mm]（機体中心から）", fontsize=8)
    ax_side.set_ylabel("高さ z [mm]（床から）", fontsize=8)
    ax_top.set_xlabel("左右 [mm]", fontsize=8)
    ax_top.set_ylabel("前後 x [mm]", fontsize=8)
    ax_front.set_xlabel("左右 [mm]", fontsize=8)

    # ---------------- 凡例 ----------------
    ax = ax_leg
    ax.axis("off")
    cols = 2
    per = math.ceil(len(PARTS) / cols)
    for i, (n, name, desc, color) in enumerate(PARTS):
        col, row = divmod(i, per)
        x = 0.01 + col * 0.5
        y = 0.92 - row * 0.14
        ax.text(x + 0.008, y, f"{n:>2}", transform=ax.transAxes, ha="center", va="center", fontsize=9,
                bbox=dict(boxstyle="circle,pad=0.25", facecolor="white", edgecolor="k", lw=0.8))
        ax.add_patch(patches.Rectangle((x + 0.022, y - 0.03), 0.015, 0.06, transform=ax.transAxes,
                                       facecolor=color, edgecolor="k", lw=0.4))
        ax.text(x + 0.045, y, f"{name}: {desc}", transform=ax.transAxes, va="center", fontsize=10)
    ax.text(0.01, 0.0, "赤線 = 壁センサの光（薄い赤は ±10° の広がり）。点線の淡い色 = 脚がクランク 1 回転で動く範囲。"
            f"寸法は mm。全長 {x_front - x_rear:.1f} × 全幅 {2 * y_out:.1f} × 高さ {top:.1f}、重量 約 {rep.total_mass:.0f} g",
            transform=ax.transAxes, fontsize=9)

    fig.suptitle("Jansen Mouse 機体の全体図（基板 1 枚）", fontsize=14)
    fig.tight_layout()
    out.mkdir(parents=True, exist_ok=True)
    path = out / "overview_views.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


# 立体図（OpenSCAD の組立図の色）の凡例
SCAD_COLORS = [
    ("#cd5c5c", "脚の足三角形（足先が床につく）"),
    ("#ffa500", "脚の上三角形"),
    ("#4682b4", "脚のリンク j・k（クランクにつながる）"),
    ("#2e8b57", "脚のリンク c・f"),
    ("#808080", "フレーム板（片側 4 枚）"),
    ("#696969", "クランクウェブ（クランク軸の腕）"),
    ("#b0c4de", "タイロッドの柱・モータ押さえ"),
    ("#006400", "基板（1 枚）"),
    ("#000080", "マイコン（STM32 直付け）"),
    ("#ffd700", "電池（2S LiPo）"),
    ("#800080", "IMU（ジャイロ）"),
    ("#800000", "モータドライバ"),
    ("#111111", "壁センサ（ホルダ入り）"),
    ("#ff0000", "壁センサの光"),
]


def overview_3d(renders: list[tuple[str, str]], out: Path) -> Path:
    """OpenSCAD で描いた組立図（[(画像, 見出し)]）に色の凡例を付けて 1 枚にする。

    画像は cad/ で次のように作る:
        xvfb-run -a openscad --camera=10,0,5,62,0,35,330 --imgsize=900,700 --colorscheme=Tomorrow -o a1.png assembly_generated.scad
        xvfb-run -a openscad --camera=0,0,5,58,0,215,330 --imgsize=900,700 --colorscheme=Tomorrow -o a2.png assembly_generated.scad
    """
    import matplotlib.image as mpimg

    fig = plt.figure(figsize=(16, 8.6))
    gs = fig.add_gridspec(1, len(renders) + 1, width_ratios=[1] * len(renders) + [0.62])
    for i, (path, title) in enumerate(renders):
        ax = fig.add_subplot(gs[0, i])
        ax.imshow(mpimg.imread(path))
        ax.set_title(title, fontsize=12)
        ax.axis("off")
    ax = fig.add_subplot(gs[0, len(renders)])
    ax.axis("off")
    ax.text(0, 0.98, "色の見方", fontsize=13, va="top", transform=ax.transAxes)
    for k, (c, name) in enumerate(SCAD_COLORS):
        y = 0.92 - k * 0.058
        ax.add_patch(patches.Rectangle((0, y - 0.018), 0.08, 0.036, transform=ax.transAxes, facecolor=c,
                                       edgecolor="k", lw=0.5))
        ax.text(0.11, y, name, transform=ax.transAxes, va="center", fontsize=11)
    ax.text(0, 0.02, "モータ（2 個）は基板の下、\n中央の溝の中に隠れている。\n白い板は区画の中心にいるときの前の壁。",
            transform=ax.transAxes, fontsize=10, va="bottom")
    fig.suptitle("Jansen Mouse 立体図", fontsize=15)
    fig.tight_layout()
    out.mkdir(parents=True, exist_ok=True)
    path = out / "overview_3d.png"
    fig.savefig(path, dpi=100)
    plt.close(fig)
    return path

"""機構パラメータの解析・出力ツール。

    python -m jansen.cli report                 # 歩容指標とリンク長表を表示
    python -m jansen.cli plot  -o out/          # 足先軌跡・接地数のグラフ
    python -m jansen.cli anim  -o out/          # 動作アニメーション (GIF)
    python -m jansen.cli header -o ../firmware/include/mechanism_params.h
    python -m jansen.cli scad  -o ../cad/links_generated.scad
    python -m jansen.cli footprint              # 縮尺・スロー数ごとの機体外形の比較
    python -m jansen.cli assembly -o ../cad/assembly_generated.scad --theta 30
    python -m jansen.cli body                   # 機体の部品配置の検証（干渉・センサの見通し・重量）
"""
from __future__ import annotations

import argparse
import math

import numpy as np
from pathlib import Path

from .assembly import BuildParams, PART_JOINTS, footprint
from .body import (HOLDER_D, HOLDER_W, SENSOR_LAYOUT, holder_dims,
                   default_design, evaluate, leg_obstacles, sensor_ray)
from .drive import crank_torque, drive_profile, spin_turn_torque
from .gait import standard_side, support_analysis
from .linkage import HOLY_NUMBERS, MOVING_LINKS, JansenLeg, gait_metrics

DEFAULT_SCALE = 0.40   # [mm/unit] 超信地旋回できる外形から決定（docs/design.md 参照）
DEFAULT_THROWS = 3     # 片側のクランクスロー数（脚は 2 倍）。片側 6 脚、全体で 12 脚
CENTER_WIDTH = 26.0    # 中央部（直交出力の N20 ウォームギヤモータ 2 個を並べた幅）[mm]
CORRIDOR_MM = 168.0    # 区画 180 mm - 壁厚 12 mm
CELL_MM = 180.0
BUILD = BuildParams()
# 駆動解析の前提（docs/design.md「駆動とモータ」参照）
MASS_KG = 0.20
FOOT_MU = 0.6
LINK_EFFICIENCY = 0.6
SEARCH_SPEED = 60.0     # [mm/s]
FAST_SPEED = 90.0       # [mm/s]
TURN_RATE_DPS = 180.0   # [deg/s]
TORQUE_MARGIN = 3.0     # モデルの不確かさを見込んだ安全率
SPEED_TABLE_N = 64      # ファーム / シミュレーション用の胴体速度表の分割数

# 関節図の線分（描画用）
SEGMENTS = [("O", "A"), ("A", "C"), ("B", "C"), ("A", "D"), ("B", "D"), ("B", "E"),
            ("C", "E"), ("E", "F"), ("D", "F"), ("F", "P"), ("D", "P")]


def build_report(scale: float, throws: int) -> str:
    leg = JansenLeg(scale=scale)
    g = gait_metrics(leg)
    sup = support_analysis(leg, standard_side(throws))
    fp = footprint(scale, throws, CENTER_WIDTH, BUILD)
    lay = fp.layout
    pr = drive_profile(leg, standard_side(throws))
    tread = fp.width - throws * lay.thickness - BUILD.plate
    t_walk = crank_torque(pr, MASS_KG, mu=FOOT_MU, link_efficiency=LINK_EFFICIENCY)
    t_turn = spin_turn_torque(pr, MASS_KG, tread, mu=FOOT_MU, link_efficiency=LINK_EFFICIENCY)
    rpm_fast = FAST_SPEED / pr.travel_per_rev * 60
    rpm_turn = math.radians(TURN_RATE_DPS) * tread / (2 * pr.body_speed.mean()) / (2 * math.pi) * 60
    lines = [
        f"# Jansen leg report (scale = {scale} mm/unit, throws/side = {throws})",
        "",
        "## 歩容",
        f"- **1 回転あたりの前進量: {pr.travel_per_rev:.2f} mm**",
        f"- 1 区画 ({CELL_MM:.0f} mm) あたりクランク回転数: {CELL_MM / pr.travel_per_rev:.3f} rev",
        f"- 1 本の足の接地区間の長さ: {g.stance_length:.2f} mm（1 回転の前進量とは別物）",
        f"- 胴体速度 / クランク角速度: {pr.body_speed.min():.2f} 〜 {pr.body_speed.max():.2f} mm/rad",
        f"- 回転角に対する前進量の非線形性: 最大 "
        f"{abs(pr.travel - pr.thetas / (2 * math.pi) * pr.travel_per_rev).max():.2f} mm",
        f"- 接地足の前後方向の滑り: 前進量の {pr.slip.mean() / pr.body_speed.mean() * 100:.0f} %",
        f"- 足上げ高さ: {g.step_height:.2f} mm",
        f"- クランク中心の対地高さ: {-g.ground_y:.2f} mm",
        f"- 接地区間の平坦度: {g.flatness:.3f} mm",
        f"- 足先の x 範囲: {g.x_min:.1f} 〜 {g.x_max:.1f} mm",
        f"- 片側の最小接地脚数: {sup.min_contacts}",
        f"- 胴体の上下動: {sup.body_bob:.3f} mm",
        "",
        f"## 駆動（機体 {MASS_KG * 1000:.0f} g, 足の摩擦係数 {FOOT_MU}, 関節効率 {LINK_EFFICIENCY}）",
        f"- 直進時の片側クランクトルク: 最大 {t_walk.peak:.1f} N·mm（実効 {t_walk.rms:.1f}）",
        f"- 超信地旋回時の片側クランクトルク: 最大 {t_turn.peak:.1f} N·mm（実効 {t_turn.rms:.1f}）",
        f"- 必要なクランク回転数: 最短走行 {FAST_SPEED:.0f} mm/s で {rpm_fast:.0f} rpm、"
        f"旋回 {TURN_RATE_DPS:.0f} deg/s で {rpm_turn:.0f} rpm",
        f"- **モータ（減速後）の要求: {max(rpm_fast, rpm_turn) * 1.2:.0f} rpm 以上で "
        f"{max(t_walk.peak, t_turn.peak) * TORQUE_MARGIN:.0f} N·mm"
        f"（{max(t_walk.peak, t_turn.peak) * TORQUE_MARGIN / 98.07:.2f} kgf·cm）以上**"
        f"（回転数 +20 %、トルク安全率 {TORQUE_MARGIN:.0f}）",
        "",
        "## 機体外形（干渉チェック済みの積層から算出）",
        f"- 全長（脚の掃引範囲）: {fp.length:.1f} mm",
        f"- 全幅: {fp.width:.1f} mm（中央部 {CENTER_WIDTH:.0f} mm を含む）",
        f"- 外接長方形の対角長（参考。旋回半径は下の「機体の部品配置」）: {fp.diagonal:.1f} mm",
        f"- 脚モジュール厚: {lay.thickness:.1f} mm"
        f"（脚 {lay.n_layers} 層 + クランクウェブ 2 枚 + フレーム板 1 枚,"
        f" 板厚 {BUILD.plate} mm, ワッシャ {BUILD.washer} mm）",
        "",
        "## 積層順（1 モジュール = 前脚 + 後脚 ' ）",
        "",
        "層 0 と層 N+1 はクランクウェブ（組立クランク軸）。固定ピン B / B' はフレーム板から片持ち。",
        "",
        "| 層 | 部品 |",
        "|---|---|",
    ]
    for z in range(1, lay.n_layers + 1):
        names = sorted(n for n, v in lay.layers.items() if v == z)
        lines.append(f"| {z} | {', '.join(names)} |")
    lines += [
        "",
        "固定ピンを立てる側: " + ", ".join(
            f"{j} = {'層 N+1 側' if s == 'high' else '層 0 側'}のフレーム板"
            for j, s in lay.fixed_pin_side.items()),
        "",
        *build_body_section(scale, throws),
        "## リンク長 [mm]（穴中心間距離）",
        "",
        "| link | holy number | length |",
        "|---|---|---|",
    ]
    for name in sorted(HOLY_NUMBERS):
        kind = "" if name in MOVING_LINKS else "（フレーム）"
        lines.append(f"| {name}{kind} | {HOLY_NUMBERS[name]} | {leg.length(name):.2f} |")
    return "\n".join(lines) + "\n"


def build_body_section(scale: float, throws: int) -> list[str]:
    d = default_design(scale, throws, CENTER_WIDTH, BUILD)
    rep = evaluate(d)
    ok = lambda xs: "なし" if not xs else "、".join(xs)  # noqa: E731
    lines = [
        "## 機体の部品配置",
        "",
        f"- 部品と脚・フレームの干渉: {ok(rep.interference)}",
        f"- 超信地旋回の半径: {rep.turning_radius:.1f} mm（{rep.turning_limiter}）"
        f" / 壁まで {84.0:.0f} mm（余裕 {84.0 - rep.turning_radius:.1f} mm）",
        f"- 部品の最低地上高: {rep.min_ground_clearance:.1f} mm",
        f"- 重量: {rep.total_mass:.0f} g、重心 (x, y, z) = "
        f"({rep.cog[0]:.1f}, {rep.cog[1]:.1f}, {rep.cog[2]:.1f}) mm",
        f"- 横方向の最小支持幅（片側）: {rep.support_half_width:.1f} mm → 転倒角 {rep.tip_angle_deg:.0f}°",
        "",
        "| 部品 | x [mm] | y [mm] | z [mm] | 重量 [g] | 備考 |",
        "|---|---|---|---|---|---|",
    ]
    for c in d.components:
        lines.append(f"| {c.name} | {c.x[0]:.0f}〜{c.x[1]:.0f} | {c.y[0]:.1f}〜{c.y[1]:.1f} | "
                     f"{c.z[0]:.1f}〜{c.z[1]:.1f} | {c.mass_g:.1f} | {c.note} |")
    lines += ["", "| 壁センサ | 位置 (x, y, z) [mm] | 向き | 光路を遮るもの |", "|---|---|---|---|"]
    for sn in d.sensors:
        x, y, z = sn.origin
        lines.append(f"| {sn.name} | ({x:.1f}, {y:.1f}, {z:.1f}) | {sn.direction_deg:+.0f}° | "
                     f"{ok(rep.blockers[sn.name])} |")
    for name, b in rep.legacy_blockers.items():
        lines.append(f"| {name} | （以前の配置） | | {ok(b)} |")
    lines += ["", "| 重量の内訳 | g |", "|---|---|"]
    for k, v in rep.mass_items.items():
        lines.append(f"| {k} | {v:.1f} |")
    lines += [f"| **合計** | **{rep.total_mass:.0f}** |", ""]
    return lines


def cmd_plot(scale: float, throws: int, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    leg = JansenLeg(scale=scale)
    path = leg.foot_path(360)
    sup = support_analysis(leg, standard_side(throws))
    out.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(path[:, 0], path[:, 1], label="foot path")
    pts = leg.solve(math.radians(60))
    for a, b in SEGMENTS:
        ax.plot([pts[a][0], pts[b][0]], [pts[a][1], pts[b][1]], "k-o", ms=3, lw=1.5)
    ax.set_aspect("equal")
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_title(f"Jansen leg (scale {scale} mm/unit)")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.savefig(out / "foot_path.png", dpi=120, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 3))
    ax.step(sup.thetas * 180 / math.pi, sup.contacts, where="post")
    ax.set_xlabel("crank angle [deg]")
    ax.set_ylabel("feet on ground (one side)")
    ax.set_ylim(0, max(sup.contacts) + 1)
    ax.grid(alpha=0.3)
    fig.savefig(out / "contacts.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def cmd_anim(scale: float, out: Path, frames: int = 48) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter

    leg = JansenLeg(scale=scale)
    path = leg.foot_path(360)
    out.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(path[:, 0], path[:, 1], color="tab:blue", alpha=0.5)
    lines = [ax.plot([], [], "k-o", ms=3)[0] for _ in SEGMENTS]
    ax.set_aspect("equal")
    ax.set_xlim(-50, 15)
    ax.set_ylim(-55, 25)
    ax.grid(alpha=0.3)

    def update(k):
        pts = leg.solve(2 * math.pi * k / frames)
        for ln, (a, b) in zip(lines, SEGMENTS):
            ln.set_data([pts[a][0], pts[b][0]], [pts[a][1], pts[b][1]])
        return lines

    anim = FuncAnimation(fig, update, frames=frames, blit=True)
    anim.save(out / "leg.gif", writer=PillowWriter(fps=24))
    plt.close(fig)


def build_header(scale: float, throws: int) -> str:
    leg = JansenLeg(scale=scale)
    g = gait_metrics(leg)
    fp = footprint(scale, throws, CENTER_WIDTH, BUILD)
    pr = drive_profile(leg, standard_side(throws))
    sensors = {sn.name: sn for sn in default_design(scale, throws, CENTER_WIDTH, BUILD).sensors}
    idx = np.linspace(0, len(pr.thetas), SPEED_TABLE_N, endpoint=False).astype(int)
    vals = [f"{v:.3f}f" for v in pr.body_speed[idx]]
    table = "\n".join("    " + ", ".join(vals[i:i + 8]) + "," for i in range(0, len(vals), 8))
    return f"""// このファイルは mechanism/ の `python -m jansen.cli header` で自動生成される。手で編集しないこと。
#pragma once

namespace mech {{
constexpr float kLinkScaleMmPerUnit = {scale:.4f}f;
constexpr int kCrankThrowsPerSide = {throws};
constexpr float kTravelMmPerRev = {pr.travel_per_rev:.4f}f;  // クランク 1 回転あたりの胴体の前進量
constexpr float kStanceLengthMm = {g.stance_length:.4f}f;   // 1 本の足の接地区間の長さ（参考値）
constexpr float kCrankHeightMm = {-g.ground_y:.4f}f;   // クランク中心の対地高さ
constexpr float kStepHeightMm = {g.step_height:.4f}f;
constexpr float kBodyLengthMm = {fp.length:.1f}f;
constexpr float kBodyWidthMm = {fp.width:.1f}f;
constexpr float kLegGroupPitchMm = {fp.width - throws * fp.layout.thickness - BUILD.plate:.1f}f;  // 左右脚群の中心間距離

// 壁センサの位置（機体中心 = クランク軸の真下から。x 前, y 左）。脚の掃引域を避けた配置（jansen/body.py）
constexpr float kFrontSensorForwardMm = {sensors["FL"].origin[0]:.1f}f;  // FL / FR: 中央の溝の中、真正面向き
constexpr float kFrontSensorLateralMm = {sensors["FL"].origin[1]:.1f}f;
constexpr float kSideSensorForwardMm = {sensors["L"].origin[0]:.1f}f;   // L / R: 脚より前、真横向き
constexpr float kSideSensorLateralMm = {sensors["L"].origin[1]:.1f}f;

// 片側の胴体速度 / クランク角速度 [mm/rad] をクランク 1 回転で {SPEED_TABLE_N} 等分した表
// （シミュレーション用。クランク角 0 は組立時の基準位相）
constexpr int kBodySpeedTableSize = {SPEED_TABLE_N};
constexpr float kBodySpeedTable[kBodySpeedTableSize] = {{
{table}
}};
}}  // namespace mech
"""


def build_scad(scale: float, throws: int) -> str:
    leg = JansenLeg(scale=scale)
    lay = footprint(scale, throws, CENTER_WIDTH, BUILD).layout
    body = "\n".join(f"L_{n} = {leg.length(n):.3f};" for n in sorted(HOLY_NUMBERS))
    layers = "\n".join(f"LAYER_{n.replace(chr(39), '_R')} = {z};"
                        for n, z in sorted(lay.layers.items()))
    d = default_design(scale, throws, CENTER_WIDTH, BUILD)
    comp = {c.name: c for c in d.components}

    def rng(name, axis):
        lo, hi = getattr(comp[name], axis)
        return f"[{lo:.2f}, {hi:.2f}]"

    body = body + "\n// 機体の部品配置（機体座標: x 前, y 左, z 上。jansen/body.py）\n" + "\n".join([
        f"CRANK_H = {-gait_metrics(leg).ground_y:.2f};",
        f"BRIDGE_X = {rng('bridge', 'x')}; BRIDGE_Y = {rng('bridge', 'y')}; BRIDGE_Z = {rng('bridge', 'z')};",
        f"DECK_Z = {rng('deck', 'z')}; DECK_FRONT_X = {rng('deck_front', 'x')}; DECK_FRONT_Y = {rng('deck_front', 'y')};",

        "SENSORS = [" + ", ".join(f"[{x:.2f}, {y:.2f}, {a:.1f}]" for _, (x, y), a in SENSOR_LAYOUT)
        + "];  // FL, FR, L, R: ホルダの前の面の真ん中 (x, y) と光の向き",
        "HOLDER = [{:.2f}, {:.2f}, {:.2f}, {:.2f}, {:.2f}];".format(HOLDER_W, HOLDER_D, *holder_dims(comp["deck"].z[0])) +
        "  // 幅, 奥行き, 高さ, 発光の穴, 受光の穴（基板の下面から）",
        f"MOTOR_X = {rng('motor_L', 'x')}; MOTOR_Z = {rng('motor_L', 'z')};",
        f"DECK_X = {rng('deck', 'x')}; DECK_Y = {rng('deck', 'y')};",

    ])
    return ("// 自動生成: python -m jansen.cli scad （手で編集しないこと）\n"
            f"SCALE = {scale};\nTHROWS = {throws};\n"
            f"PLATE = {BUILD.plate};\nWASHER = {BUILD.washer};\nLINK_W = {BUILD.link_width};\n"
            f"N_LAYERS = {lay.n_layers};\nCENTER_WIDTH = {CENTER_WIDTH};\nSPACER_Y = {BUILD.spacer_y};\n"
            f"{body}\n{layers}\n")


def build_assembly(scale: float, throws: int, theta_deg: float) -> str:
    """指定クランク角での全体組立図（OpenSCAD）。parts.scad の部品を配置する。"""
    import numpy as np

    from .assembly import _module_poses, module_parts

    leg = JansenLeg(scale=scale)
    lay = footprint(scale, throws, CENTER_WIDTH, BUILD).layout
    pitch = BUILD.plate + BUILD.washer
    module_t = lay.thickness
    ground = gait_metrics(leg).ground_y
    out = ["// 自動生成: python -m jansen.cli assembly （手で編集しないこと）",
           "// 脚の平面 = XY（Y 上向き）、クランク軸 = Z。最後に全体を起こして Z 上向きにする。",
           "include <parts.scad>", "PART = \"none\";", "rotate([90, 0, 0]) {"]

    def place(p0, p1, p2, z, color, call):
        ang = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
        mirror = ""
        if p2 is not None:
            cross = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])
            mirror = "mirror([0,1,0]) " if cross < 0 else ""
        out.append(f"color(\"{color}\") translate([{p0[0]:.3f},{p0[1]:.3f},{z:.3f}]) "
                   f"rotate([0,0,{ang:.3f}]) {mirror}{call};")

    colors = {"j": "SteelBlue", "k": "SteelBlue", "c": "SeaGreen", "f": "SeaGreen",
              "U": "Orange", "T": "Tomato"}
    calls = {"j": "bar(L_j)", "k": "bar(L_k)", "c": "bar(L_c)", "f": "bar(L_f)",
             "U": "tri_upper()", "T": "tri_foot()"}
    parts = module_parts()
    for side in (-1, 1):  # 右 / 左
        for mod in range(throws):
            th = math.radians(theta_deg) + 2 * math.pi * mod / throws
            pose = {k: np.asarray(v) for k, v in _module_poses(leg, th).items()}
            base = CENTER_WIDTH / 2 + mod * module_t + BUILD.plate  # フレーム板の外側から
            def z_of(layer):
                return side * (base + layer * pitch) - (BUILD.plate if side < 0 else 0)
            out.append(f"color(\"Gray\") translate([0,0,{side * (base - BUILD.plate) - (BUILD.plate if side < 0 else 0):.3f}]) frame();")
            for wl in (0, lay.n_layers + 1):
                place(pose["O"], pose["A"], None, z_of(wl), "DimGray", "web()")
            for name, joints in parts.items():
                base_name = name.rstrip("'")
                pts = [pose[j] for j in joints]
                p2 = pts[2] if len(pts) == 3 else None
                place(pts[0], pts[1], p2, z_of(lay.layers[name]), colors[base_name], calls[base_name])
        out.append(f"color(\"Gray\") translate([0,0,{side * (CENTER_WIDTH / 2 + throws * module_t) - (BUILD.plate if side < 0 else 0):.3f}]) frame();")
    out.append(f"color(\"Black\", 0.6) translate([-30,-10,{-CENTER_WIDTH / 2 + 1:.1f}]) "
               f"cube([60, 30, {CENTER_WIDTH - 2:.1f}]);  // 電装部")
    out.append(f"color(\"White\", 0.3) translate([-90, {ground - 1:.2f}, -90]) "
               f"cube([180, 1, 180]);  // 床（1 区画分）")
    out.append("}")
    # 機体の部品（機体座標 x 前, y 左, z 上 → 起こした後の座標: X = x, Y = -y, Z = z - クランク高さ）
    d = default_design(scale, throws, CENTER_WIDTH, BUILD)
    h = -ground
    out.append("// 機体の部品（jansen/body.py の default_design）")
    out.append(f"color(\"LightSteelBlue\") mirror([0, 1, 0]) translate([0, 0, {-h:.2f}]) {{ bridge(); motor_clamp(); }}")
    out.append(f"color(\"Black\") mirror([0, 1, 0]) translate([0, 0, {-h:.2f}]) placed_holders();")
    for c in d.components:
        if c.name == "bridge" or c.name.startswith("holder_"):
            continue  # 実際の形状（bridge()・sensor_holder()）で描く
        out.append(f"color(\"{c.color}\") translate([{c.x[0]:.2f}, {-c.y[1]:.2f}, {c.z[0] - h:.2f}]) "
                   f"cube([{c.x[1] - c.x[0]:.2f}, {c.y[1] - c.y[0]:.2f}, {c.z[1] - c.z[0]:.2f}]);  // {c.name}")
    for sn in d.sensors:
        (x0, y0), (x1, y1) = sensor_ray(sn)
        z = sn.origin[2] - h
        out.append(f"color(\"Red\", 0.6) hull() {{ translate([{x0:.2f}, {-y0:.2f}, {z:.2f}]) sphere(0.8, $fn=8); "
                   f"translate([{x1:.2f}, {-y1:.2f}, {z:.2f}]) sphere(0.8, $fn=8); }}  // 壁センサ {sn.name} の光路")
    out.append(f"color(\"White\", 0.25) translate([84, -90, {-h:.2f}]) cube([12, 180, 50]);  // 前壁（区画中心にいるとき）")
    return "\n".join(out) + "\n"


def build_footprint_table(center_width: float) -> str:
    """脚の数・縮尺・板厚ごとの外形。通路に収まるかは、実際の脚の形から求めた超信地旋回の半径で判断する。"""
    from dataclasses import replace

    from .body import BodyDesign, leg_obstacles, turning_radius

    rows = ["| 脚の数 | 縮尺 | 板厚 | 全長 | 全幅 | 旋回半径 | 壁までの余裕 | 胴体の上下動 | 1 回転の前進量 |",
            "|---|---|---|---|---|---|---|---|---|"]
    for throws in (2, 3, 4):
        for scale in (0.35, 0.40, 0.45):
            for plate in (2.0, 1.5):
                bp = replace(BUILD, plate=plate, samples=36)
                obs, _ = leg_obstacles(scale, throws, center_width, bp)
                radius, _ = turning_radius(BodyDesign(scale, throws, center_width, bp), obs)
                length = max(max(abs(o.poly.bounds[0]), abs(o.poly.bounds[2])) for o in obs) * 2
                width = 2 * max(abs(o.y1) for o in obs)
                leg = JansenLeg(scale=scale)
                bob = support_analysis(leg, standard_side(throws)).body_bob
                travel = drive_profile(leg, standard_side(throws), n=360).travel_per_rev
                rows.append(f"| {4 * throws} | {scale:.2f} | {plate:.1f} | {length:.1f} | {width:.1f} | {radius:.1f} | "
                            f"{84.0 - radius:+.1f} | {bob:.2f} | {travel:.1f} |")
    return "\n".join(rows) + "\n"


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="jansen")
    p.add_argument("command",
                   choices=["report", "plot", "anim", "header", "scad", "footprint", "assembly", "body", "drawing"])
    p.add_argument("--scale", type=float, default=DEFAULT_SCALE)
    p.add_argument("--throws", type=int, default=DEFAULT_THROWS)
    p.add_argument("--theta", type=float, default=30.0, help="assembly のクランク角 [deg]")
    p.add_argument("-o", "--out", type=Path, default=None)
    args = p.parse_args(argv)

    if args.command == "report":
        text = build_report(args.scale, args.throws)
        if args.out:
            args.out.write_text(text, encoding="utf-8")
        print(text, end="")
    elif args.command == "plot":
        cmd_plot(args.scale, args.throws, args.out or Path("out"))
    elif args.command == "anim":
        cmd_anim(args.scale, args.out or Path("out"))
    elif args.command == "header":
        text = build_header(args.scale, args.throws)
        (args.out.write_text(text, encoding="utf-8") if args.out else print(text, end=""))
    elif args.command == "drawing":
        from .drawing import three_views
        print(three_views(args.scale, args.throws, CENTER_WIDTH, BUILD, args.out or Path("out")))
    elif args.command == "body":
        print("\n".join(build_body_section(args.scale, args.throws)))
    elif args.command in ("scad", "footprint", "assembly"):
        text = {"scad": lambda: build_scad(args.scale, args.throws),
                "footprint": lambda: build_footprint_table(CENTER_WIDTH),
                "assembly": lambda: build_assembly(args.scale, args.throws, args.theta)}[args.command]()
        (args.out.write_text(text, encoding="utf-8") if args.out else print(text, end=""))


if __name__ == "__main__":
    main()

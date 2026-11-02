"""組み立て手順の図（docs/images/assembly_steps.png、docs/images/assembly_side.png）。

1 モジュール（前の脚 + 後ろの脚）を、フレーム板の側から 1 層ずつ重ねていく様子を、層の間を広げた立体図で描く。
片側 3 モジュールのつなぎ方（六角シャフト・フレーム板・タイロッド）も描く。
OpenSCAD（xvfb-run）で各手順を描いてから、matplotlib で説明つきの 1 枚にまとめる。

    python -m jansen.cli guide -o ../docs/images
"""
from __future__ import annotations

import math
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from .assembly import BuildParams, _module_poses, layer_offset, module_parts, solve_layers
from .linkage import JansenLeg
from .parts_list import LINK_NAME, pin_specs

CAD = Path(__file__).resolve().parents[2] / "cad"
# joints.png と同じ層の色
LAYER_COLOR = {1: "#e07a5f", 2: "#3d85c6", 3: "#6aa84f", 4: "#f1c232", 5: "#8e7cc3"}
CALL = {"j": "bar(L_j)", "k": "bar(L_k)", "c": "bar(L_c)", "f": "bar(L_f)", "U": "tri_upper()", "T": "tri_foot()"}


def _place(p0, p1, p2, z, color, call) -> str:
    ang = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
    mirror = ""
    if p2 is not None:
        cross = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])
        mirror = "mirror([0,1,0]) " if cross < 0 else ""
    return (f"color(\"{color}\") translate([{p0[0]:.3f},{p0[1]:.3f},{z:.3f}]) "
            f"rotate([0,0,{ang:.3f}]) {mirror}{call};")


def _cyl(p, z0, z1, d, color) -> str:
    return (f"color({color}) translate([{p[0]:.3f},{p[1]:.3f},{z0:.3f}]) "
            f"cylinder(d={d}, h={z1 - z0:.3f}, $fn=24);")


def module_steps(leg: JansenLeg, bp: BuildParams) -> list[tuple[str, list[int]]]:
    """手順（説明, その手順で置く層）。フレーム板（層 N+2）から下へ重ねる。"""
    lay = solve_layers(leg, bp)
    n = lay.n_layers
    names = {l: [k for k, v in lay.layers.items() if v == l] for l in range(1, n + 1)}

    def label(ps):
        return "・".join(LINK_NAME[p.rstrip("'")].replace("リンク ", "") + ("'" if p.endswith("'") else "")
                        for p in sorted(ps))
    steps = [("フレーム板に、固定ピン B・B' を立てる", [n + 2]),
             ("クランクウェブを置き、クランクピン A を圧入する", [n + 1])]
    for l in range(n, 0, -1):
        steps.append((f"層 {l}: {label(names[l])} を通す（必要なピン・スリーブを足す）", [l]))
    steps.append(("反対側のクランクウェブを A に圧入し、E リングで止める", [0]))
    return steps


def module_scad(leg: JansenLeg, bp: BuildParams, theta_deg: float, explode: float, upto: int) -> str:
    """1 モジュールを、手順 upto まで重ねた立体（層の間隔を explode 倍に広げる）。"""
    lay = solve_layers(leg, bp)
    n = lay.n_layers
    pitch = bp.plate + bp.washer
    pose = {k: np.asarray(v) for k, v in _module_poses(leg, math.radians(theta_deg)).items()}
    steps = module_steps(leg, bp)
    placed = set(l for _, ls in steps[:upto] for l in ls)

    def z(layer):  # フレーム板（層 N+2）を机に置き、上へ重ねていく。層の番号が小さいほど上
        return (n + 2 - layer) * pitch * explode

    out = [f"include <{CAD / 'parts.scad'}>", "PART = \"none\";"]
    if n + 2 in placed:
        out.append(f"color(\"Gray\") translate([0,0,{z(n + 2):.3f}]) frame();")
    for wl in (0, n + 1):
        if wl in placed:
            out.append(_place(pose["O"], pose["A"], None, z(wl), "DimGray", "web()"))
    for name, js in module_parts().items():
        l = lay.layers[name]
        if l in placed:
            pts = [pose[j] for j in js]
            out.append(_place(pts[0], pts[1], pts[2] if len(pts) == 3 else None, z(l),
                              LAYER_COLOR[l], CALL[name.rstrip("'")]))
    for p in pin_specs(leg, bp):
        ls = [m[0] for m in p.members]
        bottom = max(ls)  # いちばん下（フレーム板の側）の部品
        if bottom not in placed:
            continue  # ピンは、いちばん下の部品を置くときに通す
        top_placed = min(l for l in ls if l in placed)
        top = min(ls)
        out.append(_cyl(pose[p.joint], z(bottom) - 0.8, z(top_placed) + bp.plate + 0.8, 3.0, "\"Silver\""))
        if top < top_placed:  # これから通す部品の分（薄く）
            out.append(_cyl(pose[p.joint], z(top_placed) + bp.plate + 0.8, z(top) + bp.plate + 0.8, 3.0,
                            "\"Silver\", 0.3"))
        # スリーブ（空いた層）: 層 a の部品（上）と層 b の部品（下）の間
        for a_, b_ in zip(ls, ls[1:]):
            if b_ - a_ > 1 and a_ in placed and b_ in placed:
                out.append(_cyl(pose[p.joint], z(b_) + bp.plate + 0.3, z(a_) - 0.3, 4.0, "\"LightSkyBlue\", 0.85"))
    return "\n".join(out) + "\n"


def side_scad(leg: JansenLeg, bp: BuildParams, throws: int, center_width: float, theta_deg: float,
              gap: float) -> str:
    """片側 throws モジュール + フレーム板 + 六角シャフト + タイロッド。モジュールの間を gap [mm] 広げる。"""
    lay = solve_layers(leg, bp)
    n = lay.n_layers
    pitch = bp.plate + bp.washer
    module_t = lay.thickness  # フレーム板とウェブの間にもワッシャ（両側）
    la = leg.length("a")
    out = [f"include <{CAD / 'parts.scad'}>", "PART = \"none\";"]
    z_frames = []
    for mod in range(throws):
        th = math.radians(theta_deg) + 2 * math.pi * mod / throws
        pose = {k: np.asarray(v) for k, v in _module_poses(leg, th).items()}
        base = center_width / 2 + mod * (module_t + gap)
        z_frames.append(base)
        out.append(f"color(\"Gray\") translate([0,0,{base:.3f}]) frame();")
        for wl in (0, n + 1):
            call = "web(motor = true)" if (mod == 0 and wl == 0) else "web()"
            out.append(_place(pose["O"], pose["A"], None, base + layer_offset(wl, bp), "DimGray", call))
        for name, js in module_parts().items():
            l = lay.layers[name]
            pts = [pose[j] for j in js]
            out.append(_place(pts[0], pts[1], pts[2] if len(pts) == 3 else None,
                              base + layer_offset(l, bp), LAYER_COLOR[l], CALL[name.rstrip("'")]))
        if mod > 0:  # 前のモジュールのウェブ → フレーム板 → このモジュールのウェブ を六角シャフトでつなぐ
            z0 = base - gap - pitch  # 前のモジュールの外側のウェブの下面
            hex_len = gap + 3 * bp.plate + 2 * bp.washer  # ウェブ | ワッシャ | フレーム板 | ワッシャ | ウェブ
            out.append(f"color(\"Gold\") translate([0,0,{z0:.3f}]) linear_extrude({hex_len:.3f}) "
                       f"circle(d = 3.46, $fn = 6);")
    z_last = center_width / 2 + throws * (module_t + gap) - gap
    out.append(f"color(\"Gray\") translate([0,0,{z_last:.3f}]) frame();")
    # タイロッド（M2 全ねじ）
    for sx in (-1, 1):
        out.append(f"color(\"Black\") translate([{sx * la:.3f},{bp.spacer_y:.3f},{center_width / 2 - 6:.3f}]) "
                   f"cylinder(d = 2, h = {z_last - center_width / 2 + 12:.3f}, $fn = 16);")
    # モータ（中央の溝の側、出力軸がいちばん内側のウェブに入る）
    out.append(f"color(\"Silver\") translate([-34, -7, {center_width / 2 - 12.5:.3f}]) cube([41, 14, 12]);")
    # 重ねる向き（z）を横にして、脚が下に垂れる向きで見る
    return "\n".join(out[:2] + ["rotate([0,90,0]) rotate([0,0,90]) {"] + out[2:] + ["}"]) + "\n"


def _render(scad: str, png: Path, camera: str, size=(800, 620)) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".scad", delete=False) as f:
        f.write(scad)
        path = f.name
    view = ["--viewall", "--autocenter"] if float(camera.split(",")[-1]) == 0 else []  # 距離 0 = 全体が入るように
    subprocess.run(["xvfb-run", "-a", "openscad", "--hardwarnings", f"--camera={camera}", *view,
                    f"--imgsize={size[0]},{size[1]}", "--colorscheme=Tomorrow", "-o", str(png), path],
                   check=True, capture_output=True)


def build_guide(scale: float, throws: int, center_width: float, bp: BuildParams, out: Path,
                theta_deg: float = 30.0) -> list[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.image as mpimg
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["IPAGothic", "DejaVu Sans"]

    leg = JansenLeg(scale=scale)
    steps = module_steps(leg, bp)
    out.mkdir(parents=True, exist_ok=True)
    lay = solve_layers(leg, bp)
    zc = (lay.n_layers + 2) * (bp.plate + bp.washer) * 3.0 / 2
    cam = f"0,-6,{zc:.1f},58,0,25,190"  # 全手順で同じ位置・大きさ（距離 190 mm）
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        pngs = []
        for k in range(1, len(steps) + 1):
            p = tmp / f"s{k}.png"
            _render(module_scad(leg, bp, theta_deg, 3.0, k), p, cam)
            pngs.append(p)
        done = tmp / "done.png"
        _render(module_scad(leg, bp, theta_deg, 1.0, len(steps)), done, cam.replace(f",{zc:.1f},", f",{zc / 3:.1f},"))
        side = tmp / "side.png"
        _render(side_scad(leg, bp, throws, center_width, theta_deg, 25.0), side, "0,0,0,75,0,-35,0", (1100, 700))
        side_done = tmp / "side_done.png"
        _render(side_scad(leg, bp, throws, center_width, theta_deg, 0.0), side_done, "0,0,0,75,0,-35,0", (1100, 700))

        # 1 モジュールの手順
        cols = 3
        rows = math.ceil((len(steps) + 1) / cols)
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 5.2, rows * 4.3))
        for i, ax in enumerate(axes.flat):
            ax.axis("off")
            if i < len(steps):
                ax.imshow(mpimg.imread(pngs[i]))
                ax.set_title(f"{i + 1}. {steps[i][0]}", fontsize=10, loc="left", wrap=True)
            elif i == len(steps):
                ax.imshow(mpimg.imread(done))
                ax.set_title(f"{i + 1}. できあがり（実際の間隔。部品の間に 0.3 mm のワッシャ）", fontsize=10, loc="left")
        fig.suptitle("1 モジュール（前の脚 + 後ろの脚）の組み立て。層の間を 3 倍に広げて描いている\n"
                     "銀 = φ3 ピン（薄い所は後で通す部品の分）、水色 = 空いた層を埋めるスリーブ、色 = 層（joints.png と同じ）",
                     fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        p1 = out / "assembly_steps.png"
        fig.savefig(p1, dpi=90)
        plt.close(fig)

        fig, (a, b) = plt.subplots(1, 2, figsize=(16, 6.2))
        for ax, img, title in ((a, side, "モジュールの間を広げた図"), (b, side_done, "組み上がり")):
            ax.imshow(mpimg.imread(img))
            ax.set_title(title, fontsize=11)
            ax.axis("off")
        fig.suptitle(f"片側 {throws} モジュールのつなぎ方: フレーム板 → モジュール → フレーム板 → … の順に重ね、"
                     "金 = 3 mm 六角シャフトでクランクウェブどうしを 120° ずらしてつなぎ、\n"
                     "黒 = M2 全ねじ（タイロッド）で全部のフレーム板を貫いて締める。銀の箱 = モータ（出力軸がいちばん内側のウェブに入る）",
                     fontsize=11)
        fig.tight_layout(rect=(0, 0, 1, 0.9))
        p2 = out / "assembly_side.png"
        fig.savefig(p2, dpi=90)
        plt.close(fig)
    return [p1, p2]
